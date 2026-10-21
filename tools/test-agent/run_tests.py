#!/usr/bin/env python3
"""Run backend (pytest) or frontend (Vitest) unit tests and summarise the result.

This is the only command the test agent may execute. It:
  * runs the whole suite or selected test files,
  * optionally collects coverage and reports uncovered lines for `--focus` files,
  * strips secrets from the environment before running project code,
  * prints a compact JSON summary that fits in the agent's context.

Usage:
  run_tests.py backend [TEST_FILE ...] [--coverage] [--focus SRC ...] [--json-out FILE]
  run_tests.py frontend [TEST_FILE ...] [--coverage] [--focus SRC ...] [--typecheck] [--json-out FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TIMEOUT_SECONDS = 600
MAX_FAILURE_CHARS = 1500
MAX_FAILURES = 10

# Only these variables reach the test process. Everything else, including
# ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN and GITHUB_TOKEN, is dropped so
# code under test cannot read credentials.
_ENV_ALLOWLIST = {
    "PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "TEMP", "TMP",
    "CI", "TERM", "VIRTUAL_ENV", "NODE_OPTIONS", "SYSTEMROOT", "PYTHONPATH",
}


def safe_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k in _ENV_ALLOWLIST}
    env.setdefault("CI", "1")
    env["TZ"] = env.get("TZ", "UTC")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["FORCE_COLOR"] = "0"
    env["NO_COLOR"] = "1"
    return env


def _relative_to(prefix: str, paths: list[str]) -> list[str]:
    out = []
    for raw in paths:
        p = raw.replace("\\", "/")
        if p.startswith(prefix + "/"):
            p = p[len(prefix) + 1:]
        resolved = (REPO / prefix / p).resolve()
        if not resolved.is_relative_to(REPO / prefix):
            raise SystemExit(f"Path outside {prefix}/: {raw}")
        out.append(p)
    return out


def _python() -> str:
    override = os.environ.get("TEST_AGENT_PYTHON")
    if override:
        return override
    for candidate in ("backend/.venv/bin/python", "backend/.venv/Scripts/python.exe"):
        if (REPO / candidate).exists():
            return str(REPO / candidate)
    return sys.executable


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd, cwd=cwd, env=safe_env(), capture_output=True, text=True,
            timeout=TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", f"Timed out after {TIMEOUT_SECONDS}s")


def _clip(text: str, limit: int = MAX_FAILURE_CHARS) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit // 2] + "\n…\n" + text[-limit // 2:]


def run_backend(tests: list[str], coverage: bool, work: Path) -> dict:
    junit = work / "junit.xml"
    cov_json = work / "coverage.json"
    cmd = [_python(), "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
    if coverage:
        cmd += ["--cov=app", "--cov-branch", f"--cov-report=json:{cov_json}", "--cov-report="]
    cmd += _relative_to("backend", tests)
    proc = _run(cmd, REPO / "backend")

    result: dict = {"area": "backend", "exit_code": proc.returncode, "passed": 0, "failed": 0, "skipped": 0, "failures": []}
    if junit.exists():
        root = ET.parse(junit).getroot()
        for case in root.iter("testcase"):
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is not None:
                result["failed"] += 1
                if len(result["failures"]) < MAX_FAILURES:
                    result["failures"].append({"test": name, "message": _clip(problem.get("message", "") + "\n" + (problem.text or ""))})
            elif case.find("skipped") is not None:
                result["skipped"] += 1
            else:
                result["passed"] += 1
    if proc.returncode not in (0, 1) or (proc.returncode == 1 and not result["failures"]):
        # Collection errors, import errors or crashes: show the raw output.
        result["output"] = _clip(proc.stdout + "\n" + proc.stderr, 4000)

    if coverage and cov_json.exists():
        data = json.loads(cov_json.read_text())
        files = {}
        for path, info in data.get("files", {}).items():
            summary = info["summary"]
            files[f"backend/{path}"] = {
                "lines_pct": round(summary["percent_covered"], 1),
                "uncovered_lines": info.get("missing_lines", []),
            }
        totals = data.get("totals", {})
        result["coverage"] = {
            "total_pct": round(totals.get("percent_covered", 0.0), 1),
            "statements": totals.get("num_statements", 0),
            "covered": totals.get("covered_lines", 0),
            "files": files,
        }
    return result


def _vitest() -> list[str]:
    local = REPO / "frontend/node_modules/.bin/vitest"
    if local.exists():
        return [str(local)]
    return [shutil.which("npx") or "npx", "--no-install", "vitest"]


def run_frontend(tests: list[str], coverage: bool, work: Path) -> dict:
    report = work / "vitest.json"
    cov_dir = work / "coverage"
    cmd = _vitest() + ["run", "--reporter=dot", "--reporter=json", f"--outputFile.json={report}"]
    if coverage:
        cmd += [
            "--coverage.enabled=true",
            "--coverage.reporter=json",
            "--coverage.reporter=json-summary",
            f"--coverage.reportsDirectory={cov_dir}",
        ]
    cmd += _relative_to("frontend", tests)
    proc = _run(cmd, REPO / "frontend")

    result: dict = {"area": "frontend", "exit_code": proc.returncode, "passed": 0, "failed": 0, "skipped": 0, "failures": []}
    if report.exists():
        data = json.loads(report.read_text())
        for file in data.get("testResults", []):
            rel = os.path.relpath(file.get("name", ""), REPO)
            if file.get("status") == "failed" and not file.get("assertionResults"):
                result["failed"] += 1
                result["failures"].append({"test": rel, "message": _clip(file.get("message", ""))})
            for case in file.get("assertionResults", []):
                status = case.get("status")
                if status == "passed":
                    result["passed"] += 1
                elif status == "failed":
                    result["failed"] += 1
                    if len(result["failures"]) < MAX_FAILURES:
                        result["failures"].append({
                            "test": f"{rel} > {case.get('fullName', '')}",
                            "message": _clip("\n".join(case.get("failureMessages", []))),
                        })
                else:
                    result["skipped"] += 1
    if proc.returncode != 0 and not result["failures"]:
        result["output"] = _clip(proc.stdout + "\n" + proc.stderr, 4000)

    if coverage and (cov_dir / "coverage-summary.json").exists():
        summary = json.loads((cov_dir / "coverage-summary.json").read_text())
        detail = {}
        if (cov_dir / "coverage-final.json").exists():
            detail = json.loads((cov_dir / "coverage-final.json").read_text())
        files = {}
        for path, info in summary.items():
            if path == "total":
                continue
            rel = os.path.relpath(path, REPO)
            uncovered = sorted({
                loc["start"]["line"]
                for key, loc in detail.get(path, {}).get("statementMap", {}).items()
                if detail[path]["s"].get(key, 0) == 0
            })
            files[rel] = {"lines_pct": info["lines"]["pct"], "uncovered_lines": uncovered}
        total = summary.get("total", {}).get("lines", {})
        result["coverage"] = {
            "total_pct": total.get("pct", 0),
            "statements": total.get("total", 0),
            "covered": total.get("covered", 0),
            "files": files,
        }
    return result


def compact_ranges(lines: list[int]) -> str:
    """[1, 2, 3, 7, 9, 10] -> "1-3, 7, 9-10" to keep agent output short."""
    spans: list[list[int]] = []
    for n in sorted(set(lines)):
        if spans and spans[-1][1] == n - 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in spans)


def typecheck() -> list[str]:
    """Type-check the frontend (tests included) with the project's tsconfig."""
    tsc = REPO / "frontend/node_modules/.bin/tsc"
    proc = _run([str(tsc) if tsc.exists() else "tsc", "--noEmit", "--pretty", "false"], REPO / "frontend")
    if proc.returncode == 0:
        return []
    lines = [line for line in (proc.stdout + proc.stderr).splitlines() if "error TS" in line]
    return [f"frontend/{line}" for line in lines[:30]] or [_clip(proc.stdout + proc.stderr)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("area", choices=["backend", "frontend"])
    parser.add_argument("tests", nargs="*", help="Test files to run (default: whole suite)")
    parser.add_argument("--coverage", action="store_true", help="Collect coverage")
    parser.add_argument("--focus", nargs="*", default=[], help="Source files whose coverage to report in detail")
    parser.add_argument("--typecheck", action="store_true", help="Also run tsc --noEmit (frontend only)")
    parser.add_argument("--json-out", help="Write the full result (all files' coverage) to this file")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="test-agent-") as tmp:
        runner = run_backend if args.area == "backend" else run_frontend
        result = runner(args.tests, args.coverage or bool(args.focus), Path(tmp))

    if args.typecheck and args.area == "frontend":
        result["typecheck_errors"] = typecheck()
    result["ok"] = result["exit_code"] == 0 and result["failed"] == 0 and not result.get("typecheck_errors")
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))

    # Keep stdout small: only the focus files' coverage is printed.
    printable = dict(result)
    if "coverage" in printable:
        cov = dict(printable["coverage"])
        focus = {f.replace("\\", "/") for f in args.focus}
        cov["files"] = {
            k: {**v, "uncovered_lines": compact_ranges(v["uncovered_lines"])}
            for k, v in cov["files"].items() if k in focus
        }
        printable["coverage"] = cov
    print(json.dumps(printable, indent=1))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
