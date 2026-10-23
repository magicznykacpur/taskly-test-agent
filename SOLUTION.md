# Solution: unit test agent and PR workflow

This repository adds a custom **test-engineer agent** with five reusable **skills**, and a GitHub Actions workflow that runs the agent on every pull request. The agent decides whether the changed code needs new or updated unit tests, writes them, and runs them. The workflow then verifies the tests independently, commits them to the PR, and posts a report on the PR.

The same agent, in *backfill* mode, wrote the missing tests for the existing app:

| Area | Tests before → after | Line coverage before → after |
|---|---|---|
| Backend (pytest) | 21 → 75 | 42% → 100% |
| Frontend (Vitest) | 18 → 83 | 47.7% → 99.3% (two passes: 72.8%, then 99.3%) |

## Where things are

| Path | What it is |
|---|---|
| `.claude/agents/test-engineer.md` | The custom agent: role, workflow, hard rules, tool allowlist, preloaded skills |
| `.claude/skills/test-impact-analysis/` | Skill: decide `created` / `updated` / `no_change` per changed file |
| `.claude/skills/pytest-unit-tests/` | Skill: backend test conventions and patterns per layer (router, repository, core, dependencies) |
| `.claude/skills/vitest-react-tests/` | Skill: frontend conventions (RTL queries, design-system mocks, TanStack Query hooks, timers, fetch) |
| `.claude/skills/run-unit-tests/` | Skill: how to run tests, read coverage, and fix failures in a bounded loop |
| `.claude/skills/test-agent-report/` | Skill: the structured final report the workflow publishes |
| `tools/test-agent/plan.py` | Deterministic planner: diff → targets, skipped files, prompt |
| `tools/test-agent/run_tests.py` | The only command the agent may run: pytest/Vitest with coverage, JSON summary, secrets stripped |
| `tools/test-agent/guard.py` | Write guard: PreToolUse hook, post-run tree check, patch validation |
| `tools/test-agent/run_agent.sh` | Headless Claude Code invocation with locked-down permissions and a JSON schema |
| `tools/test-agent/pipeline.sh` | One run end to end, identical in CI and locally |
| `tools/test-agent/report.py` | Renders the PR comment and job summary |
| `tools/test-agent/tests/` | Unit tests for the tooling itself |
| `.github/workflows/test-agent.yml` | The PR workflow |
| `.github/workflows/ci.yml` | Plain CI: both suites with coverage, typecheck, format check, tooling tests |

## How a PR run works

```
pull_request ─▶ generate job (read-only token, model credential)              publish job (write token, no credential)
               1. checkout PR head, no git credentials                        1. checkout BASE commit only (trusted tools)
               2. overlay .claude/ + tools/test-agent/ from base              2. download artifact
               3. plan.py: changed files → targets / skipped                  3. guard.py verify-patch (again)
               4. install deps (no install scripts)                           4. if verified and PR head unchanged:
               5. pipeline.sh:                                                     git apply, commit as github-actions[bot], push
                  baseline tests + coverage                                   5. upsert one sticky PR comment
                  claude --agent test-engineer (skills, structured output)    6. fail the check if tests fail
                  guard check → prettier → full suites again → re-run new tests
                  → tests.patch
               6. job summary + artifact (plan, prompt, agent result, results, patch)
```

1. **Plan (no model).** `plan.py` classifies each changed file using the same path rules as the coverage config: application source, test, or other. Docs, config, styles, stories, types and barrels are skipped with a reason, and tokens are spent only on files where a unit test can matter. If nothing testable changed, the agent is not started.
2. **Agent.** `claude -p --agent test-engineer` gets the plan as its prompt: paths, diffs, and the conventional test file for each target. It follows its skills: analyse the impact, write tests in the repo's style, run them with `run_tests.py`, use `--focus` coverage to find uncovered lines, fix failures (at most 3 attempts per file), and finish with a JSON report validated by `report.schema.json`.
3. **Verify (no model).** The pipeline does not trust the agent's claims. It checks that only test files changed, formats them with Prettier, re-runs **both full suites** with coverage (plus `tsc` for the frontend), and runs the touched test files a second time to catch flaky tests.
4. **Publish.** If verification passes, the tests are committed to the PR branch with a `Generated-by: test-agent` trailer. The PR gets a single comment that is updated on each push. It shows per-file decisions with reasons, pass/fail counts, coverage before → after (overall and per changed file), the flaky check, failing tests, possible bugs found, skills used, turns, time and cost, and a link to the run artifacts.

## Technical decisions

- **Claude Code CLI, headless, instead of a custom agent framework.** Agents (`.claude/agents`) and skills (`.claude/skills`) are first-class there. The same files work interactively (`claude --agent test-engineer`), locally (`pipeline.sh`) and in CI. `--json-schema` gives a validated structured report, and `--permission-mode dontAsk` with an allowlist gives deny-by-default tools.
- **Calling the CLI directly rather than `anthropics/claude-code-action`.** The action is built around a GitHub token and its MCP tools. Here the model never needs GitHub: all GitHub writes happen in a separate job that never runs the model. That split is the main security property, and it is simpler to show with the plain CLI.
- **Deterministic wrapper around a non-deterministic core.** Planning, guarding, verification and reporting are plain scripts with their own unit tests. The model does what needs judgement: whether a change needs tests, which cases matter, and how to write them in the repo's style.
- **Skills are specific to this repo.** They encode the existing test conventions (autospec repository mock, `dependency_overrides`, design-system mocks, top-level `it`, Prettier style), so generated tests look like the hand-written ones. This matters more for usefulness than generic "write good tests" prompts.
- **Commit to the PR branch** (not a separate PR or a suggestion comment). That way the tests are reviewed together with the change they cover. Setting the repository variable `TEST_AGENT_COMMIT=false` switches to report-only mode, where the patch stays an artifact.
- **Expected failures instead of source changes.** If a test shows a real bug, the agent keeps the assertion of the intended behaviour as `xfail(strict=True)` / `it.fails` and reports it under "Possible bugs". It never edits source code to make tests green.

## Security and reliability

| Risk | Mitigation |
|---|---|
| Fork PRs and secret exfiltration | `pull_request` trigger (not `pull_request_target`). Fork PRs and drafts are skipped. Top-level `permissions: {}`, with each job declaring the minimum. |
| Agent writes outside tests (bug or prompt injection) | Three layers: a PreToolUse hook denies `Write`/`Edit` outside test globs, `guard.py check` fails the run if the tree has other changes, and the publish job validates the patch again (paths, no mode changes, symlinks or renames) before applying it. |
| Agent runs arbitrary commands or reaches the network | Tool allowlist: Read, Glob, Grep, Write, Edit, Skill and `Bash(python3 tools/test-agent/run_tests.py:*)` only. Web tools, subagents and MCP servers are disabled (`--strict-mcp-config`). |
| Credential theft by code under test | Only the pipeline step has the model credential. `run_tests.py` passes an allowlisted environment to pytest/Vitest, so `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN` and `GITHUB_TOKEN` are not inherited. The generate job has no git credentials (`persist-credentials: false`) and a read-only token. Dependencies install without lifecycle scripts (`npm ci --ignore-scripts`, `pip --only-binary :all:`). |
| PR weakens its own guardrails | The `.claude/` directory and `tools/test-agent/` are replaced with the base commit's versions before the agent runs, and the publish job runs only base-commit code. |
| Prompt injection via PR text | PR title, body and comments are never given to the model. Diffs are marked as untrusted data. Model text in the PR comment is sanitised (HTML stripped, @-mentions neutralised, tables escaped). |
| Wrong or useless tests | Independent re-run of full suites, typecheck, flaky re-run, and coverage per changed file. Skills require behavioural assertions and forbid weakening existing tests. A human reviews the bot commit in the PR. |
| Loops and races | Runs on the bot's own commit stop at the `Generated-by: test-agent` trailer check, and GitHub additionally holds workflows triggered by the bot for approval. `concurrency` cancels outdated runs. Publishing is skipped if the PR head moved during the run. |
| Cost and runaway | Plan-level target cap (25 files), `--max-turns`, optional `--max-budget-usd`, 30-minute job timeout. Agent turns and cost are shown in every report. |
| Supply chain | Every action is pinned to a commit SHA, the Claude Code CLI is pinned to a version, and dependencies come from lockfiles. |

## Running it

### Prerequisites

1. GitHub Actions enabled, and **Settings → Actions → General → Workflow permissions** allowing the token to write (the jobs request `contents: write` / `pull-requests: write` explicitly).
2. One repository secret:
   - `ANTHROPIC_API_KEY` (from console.anthropic.com), **or**
   - `CLAUDE_CODE_OAUTH_TOKEN` (run `claude setup-token` with a Claude Pro/Max subscription).
3. Optional repository variables: `TEST_AGENT_MODEL` (default: the agent's `sonnet`), `TEST_AGENT_MAX_TURNS` (default 80), `TEST_AGENT_MAX_BUDGET_USD`, `TEST_AGENT_COMMIT=false` for report-only mode.
4. Recommended: protect `main` and require review for `.github/`, `.claude/` and `tools/test-agent/` (CODEOWNERS), because `pull_request` workflows run the workflow file from the PR branch.

### On pull requests

Open a non-draft PR from a branch of this repository. "Test agent" runs on open, push, reopen and ready-for-review. Add the label `skip-test-agent` to opt out.

### Locally

```bash
# deps as in README (backend/.venv, frontend/node_modules) and Claude Code logged in
mkdir -p .test-agent/run
python3 tools/test-agent/plan.py --base origin/main --out .test-agent/run/plan.json --prompt-out .test-agent/run/prompt.md
tools/test-agent/pipeline.sh .test-agent/run
python3 tools/test-agent/report.py --dir .test-agent/run --out .test-agent/run/report.md

# backfill of existing code, prioritised by current coverage
python3 tools/test-agent/run_tests.py frontend --coverage --json-out .test-agent/fe.json
python3 tools/test-agent/plan.py --backfill --area frontend --coverage-json .test-agent/fe.json \
  --out .test-agent/run/plan.json --prompt-out .test-agent/run/prompt.md
```

Interactive use also works: `claude --agent test-engineer`.

## Example run

### Backfill (existing code)

The agent ran three times locally through `pipeline.sh`, using exactly the code path CI uses. The full reports are in [`docs/test-agent-runs/`](docs/test-agent-runs/):

- [Backend](docs/test-agent-runs/backfill-backend.md): 11 targets, 6 new test files and 4 extended, 2 `no_change` (already 100%). 75 tests, coverage 42% → 100%. 40 turns, about 100 s, $0.33.
- [Frontend pass 1](docs/test-agent-runs/backfill-frontend-pass1.md): new tests for `http.ts`, all query/mutation hooks and `TodoEmptyState`. 43 tests, coverage 47.7% → 72.8%. Here the agent marked files that already had a test file as `no_change` without reading them. I treated that as a skill bug, not a run to retry: the planner became coverage-aware (`--coverage-json`, `--min-coverage`, with the uncovered lines in the prompt), and the impact-analysis skill now says an existing test file is never a reason for `no_change` by itself.
- [Frontend pass 2](docs/test-agent-runs/backfill-frontend-pass2.md): 8 targets below 90%. Extended tests for TodosPage, TodoList, DeleteTodoDialog, the API client, utils, useNotice and TodoForm. 83 tests, coverage 72.8% → 99.3%. 39 turns, about 110 s, $0.34.

Every run passed the guard (only test files changed), the independent full-suite re-run, `tsc` and the flaky re-run.

### Pull request: [#1 feat: task statistics](https://github.com/magicznykacpur/taskly-test-agent/pull/1)

The PR adds `GET /api/todos/stats` (schema, repository aggregate, route) and a frontend statistics summary (API call, query hook, component, and cache invalidation in the three mutation hooks). It deliberately contains **no tests**, and it breaks all 7 existing `TodosPage` tests, because the page now renders a component that needs a QueryClient. CI on the PR was red.

What the workflow did ([run](https://github.com/magicznykacpur/taskly-test-agent/actions/runs/39918023749), 3 min):

1. **Plan**: 10 targets (backend repository, router and schemas; frontend page, API, component, 4 hooks). `types.ts` and `queryKeys.ts` were skipped as declarative.
2. **Agent decisions** (skills used: `test-impact-analysis`, `pytest-unit-tests`, `vitest-react-tests`, `run-unit-tests`, `test-agent-report`):
   - *Created* `TodoStatsSummary.test.tsx` (loading, error, zero-total, rounded percentage, overdue badge only when > 0) and `useTodoStatsQuery.test.tsx`.
   - *Updated* `TodosPage.test.tsx`: stubbed the new child, as the file already does for its other children, which fixed the 7 failing tests. It also added an assertion that the summary is rendered.
   - *Updated* the three mutation hook tests to assert that the stats query is invalidated, plus the API, repository (compiled SQL uses the `FILTER` clauses with today's date), router (`/stats` is not routed to `/{todo_id}`, with a patched `today`) and schema tests.
3. **Verification** (independent of the agent): backend 80 passed / 0 failed, coverage 97.1% → 100%. Frontend 95 passed / 0 failed, 99.4% coverage, typecheck clean. The flaky re-run was stable in both areas.
4. **Publish**: patch re-validated, then committed as [`0b4630f`](https://github.com/magicznykacpur/taskly-test-agent/commit/0b4630f56725d0f48e9a10b15157e7f4fcc0ef2a) by `github-actions[bot]`. The [PR comment](https://github.com/magicznykacpur/taskly-test-agent/pull/1#issuecomment-6359869244) lists every decision with its reason, plus the numbers above. CI on the bot commit went from red to green.

## Assumptions

- PRs come from branches of this repository, so their authors already have write access. Fork PRs are skipped instead of being handled through `pull_request_target`.
- "Unit tests" means tests without external services. No database or network is needed (the existing suites already work this way), so the workflow needs no Postgres service.
- The coverage scope of each project (`pyproject.toml` omit list, `vite.config.ts` exclude list) reflects what the maintainers consider unit-testable. The planner mirrors it, so the design system and declarative files are not targets.
- Committing generated tests to the PR branch is acceptable, because they are reviewed with the PR.

## Limitations

- Code under test runs in the same job as the agent process. The environment is stripped, but a malicious test could still read the agent's process memory or `/proc/<pid>/environ` as the same user. This is acceptable when only trusted writers can open PRs that run the workflow. It is not acceptable for untrusted contributors.
- Changes to the agent, skills or tooling in a PR take effect only after merge, because PR runs use the base versions by design.
- GitHub holds workflow runs triggered by the bot's commit as "action required" until a maintainer approves them (Actions → the run → Approve and run). The agent workflow has already verified exactly that tree, but required status checks need that approval, or a GitHub App token to push with.
- Model output is non-deterministic. Two runs can produce different (both valid) tests. The verification gates catch wrong tests, not merely mediocre ones.
- Large PRs are capped at 25 target files per run, and diffs are truncated at 400 lines per file (the agent reads the full file).
- Mutation testing is not done, so "tests pass and coverage went up" does not prove the assertions are strong.

## What I would change for production

- Run tests in a sandbox separate from the agent (a container or a different OS user with no access to the agent process), or use workload identity federation (`anthropic_federation_rule_id`) for short-lived credentials instead of a static secret.
- A GitHub App token for the bot commit, so required checks re-run on it, and signed commits.
- Mutation testing (mutmut / Stryker) on changed files as an additional gate, and an LLM-as-judge or human sample review of generated test quality over time.
- Slash-command triggers on the PR (`/test-agent rerun`, `/test-agent skip <file>`), and a scheduled backfill job that opens PRs for the least-covered files.
- Cost dashboards and per-PR budgets, and caching the agent's context (prompt caching) for large repos.
- Evaluate the skills: a small benchmark of historical PRs with known-good tests to measure whether skill changes help.
