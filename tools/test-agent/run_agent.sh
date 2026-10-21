#!/usr/bin/env bash
# Run the test-engineer agent headlessly on a prompt produced by plan.py.
#
#   tools/test-agent/run_agent.sh <prompt.md> <agent-result.json>
#
# Credentials come from ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN.
# Optional: TEST_AGENT_MODEL (overrides the agent's model), TEST_AGENT_MAX_TURNS,
# TEST_AGENT_MAX_BUDGET_USD (API key billing only).
set -euo pipefail

prompt_file=$1
result_file=$2
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
cd "$repo"

args=(
  -p "$(cat "$prompt_file")"
  --agent test-engineer
  --output-format json
  --json-schema "$(cat "$here/report.schema.json")"
  # Deny anything not listed. Writes are further limited to test paths by the
  # agent's PreToolUse hook, and Bash to the test runner only.
  --permission-mode dontAsk
  --allowedTools "Read,Glob,Grep,Write,Edit,Skill,StructuredOutput,Bash(python3 tools/test-agent/run_tests.py:*)"
  --disallowedTools "WebFetch,WebSearch,Agent,Task,NotebookEdit"
  --strict-mcp-config
  --setting-sources project
  --settings "$here/agent-settings.json"
  --max-turns "${TEST_AGENT_MAX_TURNS:-80}"
)
if [[ -n "${TEST_AGENT_MODEL:-}" ]]; then
  args+=(--model "$TEST_AGENT_MODEL")
fi
if [[ -n "${TEST_AGENT_MAX_BUDGET_USD:-}" ]]; then
  args+=(--max-budget-usd "$TEST_AGENT_MAX_BUDGET_USD")
fi

# The agent's exit code is not trusted for the verdict: the workflow re-runs
# the tests itself. Keep the JSON result even when the agent stops early.
set +e
claude "${args[@]}" < /dev/null > "$result_file"
status=$?
set -e
echo "claude exited with $status" >&2
exit 0
