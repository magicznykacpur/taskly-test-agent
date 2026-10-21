#!/usr/bin/env python3
"""Enforce that the agent changed only test files.

Subcommands:
  hook          PreToolUse hook for Claude Code: deny Write/Edit outside test paths.
  check         Fail if the working tree has changes outside test paths.
  patch FILE    Write the agent's changes (test files only) as a git patch.
  verify-patch FILE
                Fail if a patch touches anything outside test paths. Run again
                in the publishing job, which must not trust the artifact.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout


def changed_paths() -> list[str]:
    out = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [e for e in out.split("\0") if e]
    return sorted({e[3:] for e in entries})


def hook() -> int:
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or REPO).resolve()
    try:
        rel = Path(raw).resolve().relative_to(project).as_posix() if os.path.isabs(raw) else raw
    except ValueError:
        rel = None
    if rel and rules.is_writable(rel):
        return 0
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{raw!r} is not a test file. The test agent may only write backend/tests/**, "
                "frontend/src/**/*.test.ts(x) and frontend/src/test/*. Never modify application "
                "source; report suspected bugs in `findings` instead."
            ),
        }
    }
    print(json.dumps(decision))
    return 0


def check() -> int:
    bad = [p for p in changed_paths() if not rules.is_writable(p)]
    if bad:
        print("Changes outside allowed test paths:\n" + "\n".join(f"  {p}" for p in bad), file=sys.stderr)
        return 1
    print(json.dumps({"changed_tests": changed_paths()}))
    return 0


def patch(out: str) -> int:
    if check() != 0:
        return 1
    files = changed_paths()
    if files:
        git("add", "--intent-to-add", "--", *files)
    Path(out).write_text(git("diff", "--binary", "--", *files) if files else "")
    return 0


_HEADER = re.compile(r"^diff --git a/(\S+) b/(\S+)$")


def verify_patch(path: str) -> int:
    touched = set()
    for line in Path(path).read_text().splitlines():
        if line.startswith("diff --git "):
            m = _HEADER.match(line)
            if not m:
                print(f"Unparseable patch header: {line}", file=sys.stderr)
                return 1
            touched.update(m.groups())
        elif line.startswith(("rename ", "copy ", "old mode", "new mode")) or (
            line.startswith(("new file mode", "deleted file mode")) and not line.endswith(" 100644")
        ):
            # Only plain, non-executable files: no symlinks, exec bits or renames.
            print(f"Unsupported patch operation: {line}", file=sys.stderr)
            return 1
    touched.discard("/dev/null")
    bad = sorted(p for p in touched if not rules.is_writable(p))
    if bad:
        print("Patch touches non-test paths:\n" + "\n".join(f"  {p}" for p in bad), file=sys.stderr)
        return 1
    print(json.dumps({"files": sorted(touched)}))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    command, *rest = argv
    if command == "hook":
        return hook()
    if command == "check":
        return check()
    if command == "patch" and len(rest) == 1:
        return patch(rest[0])
    if command == "verify-patch" and len(rest) == 1:
        return verify_patch(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
