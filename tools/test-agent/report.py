#!/usr/bin/env python3
"""Render the test agent's PR comment and job summary from the run's artifacts.

Expected files in --dir (all optional, a missing file is reported as such):
  plan.json                     planner output
  agent-result.json             `claude -p --output-format json` result
  before-{backend,frontend}.json  run_tests.py results before the agent ran
  after-{backend,frontend}.json   independent verification after the agent ran
  guard.txt                     "ok" or the guard's error output
  repeat-{backend,frontend}.json  second run of the new/changed tests (flakiness check)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MARKER = "<!-- test-agent-report -->"
MAX_TEXT = 600


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def clean(text: object, limit: int = MAX_TEXT) -> str:
    """Make model-written text safe to embed: one line, no HTML, no pings."""
    s = re.sub(r"<[^>]*>", "", str(text or ""))
    s = s.replace("@", "@​").replace("|", "\\|")
    s = " ".join(s.split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def pct(value) -> str:
    return "n/a" if value is None else f"{float(value):.1f}%"


def changed_file_coverage(plan, before, after, area):
    rows = []
    for t in (plan or {}).get("targets", []):
        if t["area"] != area:
            continue
        b = ((before or {}).get("coverage") or {}).get("files", {}).get(t["path"], {}).get("lines_pct")
        a = ((after or {}).get("coverage") or {}).get("files", {}).get(t["path"], {}).get("lines_pct")
        rows.append((t["path"], b, a))
    return rows


def agent_report(result):
    if not result:
        return None
    report = result.get("structured_output")
    if isinstance(report, str):
        try:
            report = json.loads(report)
        except ValueError:
            report = None
    return report if isinstance(report, dict) else None


def overall_status(guard_ok, afters, plan, agent):
    if not plan or not plan.get("targets") and not plan.get("changed_tests"):
        return "skipped", "⏭️ No application code changed that needs unit tests."
    if not guard_ok:
        return "failure", "❌ The agent tried to change files outside test paths. Nothing was committed."
    if any(a is None for a in afters.values()):
        return "failure", "❌ Verification did not produce results."
    if any(not a.get("ok") for a in afters.values()):
        return "failure", "❌ Some tests fail. See the failures below."
    if agent is None:
        return "warning", "⚠️ Tests pass, but the agent did not return a report."
    return "success", "✅ All tests pass."


def render(d: Path, commit: str | None, run_url: str | None, publish_note: str | None) -> tuple[str, str]:
    plan = load(d / "plan.json")
    result = load(d / "agent-result.json")
    agent = agent_report(result)
    guard_text = (d / "guard.txt").read_text().strip() if (d / "guard.txt").exists() else "missing"
    guard_ok = guard_text == "ok"
    areas = (plan or {}).get("areas", []) or []
    befores = {a: load(d / f"before-{a}.json") for a in areas}
    afters = {a: load(d / f"after-{a}.json") for a in areas}
    repeats = {a: load(d / f"repeat-{a}.json") for a in areas}
    status, headline = overall_status(guard_ok, afters, plan, agent)

    out = [MARKER, "## 🧪 Unit test agent", "", f"**{headline}**", ""]
    if agent and agent.get("summary"):
        out += [clean(agent["summary"], 1200), ""]

    if commit:
        out.append(f"Generated tests were committed to this PR in {commit}. Review them like any other change.")
    elif publish_note:
        out.append(publish_note)
    out.append("")

    decisions = (agent or {}).get("decisions", [])
    if decisions:
        icons = {"created": "🆕 created", "updated": "✏️ updated", "no_change": "➖ no change"}
        out += ["### Decisions", "", "| Source file | Decision | Test file | Reason |", "|---|---|---|---|"]
        for dec in decisions:
            test_file = f"`{clean(dec.get('test_file'), 120)}`" if dec.get("test_file") else ""
            out.append(f"| `{clean(dec.get('source_file'), 120)}` | {icons.get(dec.get('action'), clean(dec.get('action'), 20))} | {test_file} | {clean(dec.get('reason'))} |")
        out.append("")

    if areas:
        out += ["### Verification", "", "Tests were re-run by the workflow, independently of the agent.", "",
                "| Area | Passed | Failed | Coverage before → after | Flaky check |", "|---|---|---|---|---|"]
        for a in areas:
            b, r, rep = befores.get(a), afters.get(a), repeats.get(a)
            if r is None:
                out.append(f"| {a} | – | – | – | – |")
                continue
            before_pct = ((b or {}).get("coverage") or {}).get("total_pct")
            after_pct = (r.get("coverage") or {}).get("total_pct")
            flaky = "–" if rep is None else ("stable" if rep.get("ok") else "⚠️ failed on re-run")
            out.append(f"| {a} | {r.get('passed', 0)} | {r.get('failed', 0)} | {pct(before_pct)} → {pct(after_pct)} | {flaky} |")
        out.append("")

        rows = [row for a in areas for row in changed_file_coverage(plan, befores.get(a), afters.get(a), a)]
        if rows:
            out += ["<details><summary>Coverage of changed files</summary>", "", "| File | Before | After |", "|---|---|---|"]
            out += [f"| `{p}` | {pct(b)} | {pct(a)} |" for p, b, a in rows]
            out += ["", "</details>", ""]

        failures = [(a, f) for a in areas for f in (afters.get(a) or {}).get("failures", [])]
        if failures:
            out += ["<details open><summary>Failing tests</summary>", ""]
            for a, f in failures[:10]:
                out += [f"**{a}** `{clean(f['test'], 200)}`", "```", f["message"][:1500].replace("```", "ˋˋˋ"), "```"]
            out += ["</details>", ""]

    if not guard_ok and guard_text != "missing":
        out += ["### Guard", "```", guard_text[:1500], "```", ""]

    findings = (agent or {}).get("findings", [])
    if findings:
        out += ["### Possible bugs found while testing", ""]
        out += [f"- `{clean(f.get('file'), 120)}`: {clean(f.get('description'))}" for f in findings]
        out.append("")

    skipped = (plan or {}).get("skipped", [])
    if skipped:
        out += ["<details><summary>Skipped by the planner</summary>", ""]
        out += [f"- `{s['path']}`: {s['reason']}" for s in skipped[:50]]
        out += ["", "</details>", ""]

    meta = []
    if agent and agent.get("skills_used"):
        meta.append("Skills used: " + ", ".join(f"`{clean(s, 40)}`" for s in agent["skills_used"]))
    if result:
        bits = []
        if result.get("num_turns") is not None:
            bits.append(f"{result['num_turns']} turns")
        if result.get("duration_ms") is not None:
            bits.append(f"{result['duration_ms'] / 1000:.0f}s")
        if result.get("total_cost_usd") is not None:
            bits.append(f"${result['total_cost_usd']:.2f}")
        if bits:
            meta.append("Agent run: " + ", ".join(bits))
    if run_url:
        meta.append(f"[Workflow run and artifacts]({run_url})")
    if meta:
        out += ["---", "<sub>" + " · ".join(meta) + "</sub>"]
    return "\n".join(out) + "\n", status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--run-url")
    parser.add_argument("--publish-note")
    args = parser.parse_args(argv)
    body, status = render(args.dir, args.commit, args.run_url, args.publish_note)
    args.out.write_text(body)
    print(status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
