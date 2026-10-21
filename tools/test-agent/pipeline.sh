#!/usr/bin/env bash
# One test agent run, identical in CI and locally:
#   baseline tests -> agent -> guard -> format -> independent verification -> patch
#
#   tools/test-agent/pipeline.sh <out-dir>
#
# <out-dir> must contain plan.json and prompt.md from plan.py. Everything the
# report needs is written there. Exit code is 0 when the run produced a usable
# result (verification passed, guard passed), 1 otherwise.
set -uo pipefail

out=$(realpath "$1")
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
cd "$repo"

areas=$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["areas"]))' "$out/plan.json")
targets=$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["targets"]))' "$out/plan.json")
focus() { python3 -c 'import json,sys; print(" ".join(t["path"] for t in json.load(open(sys.argv[1]))["targets"] if t["area"]==sys.argv[2]))' "$out/plan.json" "$1"; }

if [[ -z "$areas" ]]; then
  echo "Nothing to test."; echo ok > "$out/guard.txt"; : > "$out/tests.patch"; exit 0
fi

echo "::group::Baseline tests ($areas)"
for area in $areas; do
  python3 "$here/run_tests.py" "$area" --coverage --json-out "$out/before-$area.json" > /dev/null || true
done
echo "::endgroup::"


# The guard compares against HEAD, so the tree must be clean before the agent runs.
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "Working tree is not clean; commit or stash changes first." >&2; exit 1
fi

if [[ "$targets" -gt 0 ]]; then
  echo "::group::Test agent"
  "$here/run_agent.sh" "$out/prompt.md" "$out/agent-result.json"
  echo "::endgroup::"
fi

echo "::group::Guard"
if python3 "$here/guard.py" check > "$out/guard-check.json" 2> "$out/guard-err.txt"; then
  echo ok > "$out/guard.txt"
else
  cat "$out/guard-err.txt" > "$out/guard.txt"
  cat "$out/guard.txt"
  echo "::endgroup::"
  exit 1
fi
changed=$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["changed_tests"]))' "$out/guard-check.json")
echo "Changed test files: ${changed:-none}"
echo "::endgroup::"

# Format generated frontend tests with the project's Prettier config.
fe_changed=$(for f in $changed; do [[ $f == frontend/* ]] && echo "${f#frontend/}"; done)
if [[ -n "$fe_changed" ]]; then
  (cd frontend && node_modules/.bin/prettier --write $fe_changed > /dev/null)
fi

echo "::group::Verification (full suites)"
status=0
for area in $areas; do
  extra=(); [[ $area == frontend ]] && extra=(--typecheck)
  python3 "$here/run_tests.py" "$area" --coverage "${extra[@]}" --focus $(focus "$area") \
    --json-out "$out/after-$area.json" || status=1
  # Re-run the files the agent touched to catch order- or time-dependent tests.
  touched=$(for f in $changed; do [[ $f == $area/* && ( $f == *test_*.py || $f == *.test.ts* ) ]] && echo "$f"; done)
  if [[ -n "$touched" ]]; then
    python3 "$here/run_tests.py" "$area" $touched --json-out "$out/repeat-$area.json" > /dev/null || status=1
  fi
done
echo "::endgroup::"

python3 "$here/guard.py" patch "$out/tests.patch"
exit $status
