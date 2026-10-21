---
name: run-unit-tests
description: Run backend or frontend unit tests with tools/test-agent/run_tests.py, read the JSON summary and coverage, and fix failing tests in a bounded loop. Use after writing or changing any test, and to find uncovered lines.
---

# Running and verifying unit tests

`tools/test-agent/run_tests.py` is the only command available to you. It runs the project's own test runner with a clean environment (no secrets) and prints a short JSON summary.

```bash
# one or more test files, with coverage details for the source files you are testing
python3 tools/test-agent/run_tests.py backend backend/tests/core/test_config.py --focus backend/app/core/config.py
python3 tools/test-agent/run_tests.py frontend frontend/src/lib/http.test.ts --focus frontend/src/lib/http.ts --typecheck

# the whole suite of an area (do this once at the end)
python3 tools/test-agent/run_tests.py backend --coverage
python3 tools/test-agent/run_tests.py frontend --coverage --typecheck
```

Output fields: `ok`, `passed`, `failed`, `skipped`, `failures[]` (test name and message), `output` (raw output when tests could not even start, for example an import or syntax error), `typecheck_errors[]` (frontend, with `--typecheck`) and `coverage.files[<focus file>]` with `lines_pct` and `uncovered_lines`.

Note that when you run a single test file, coverage shows only what *that* file covers. Lines covered by other test files will appear as uncovered.

## The loop

1. Before writing anything, run the existing test file (or the area's suite) with `--focus` on the target. This gives you a baseline and the uncovered lines.
2. Write the tests, then run that test file with `--focus`.
3. If something fails, read the message and decide which side is wrong:
   - **The test is wrong** (wrong selector, wrong mock shape, async not awaited, wrong import path): fix the test.
   - **The source is wrong** (it contradicts its own validation rules, docstring, types or the API contract): do not change the source. Keep the assertion of the intended behaviour, mark the test as an expected failure (`@pytest.mark.xfail(strict=True, reason="...")` or `it.fails(...)`) and record a finding.
   - Never "fix" a failure by asserting whatever the code currently returns without understanding why.
4. Repeat at most **3 times per test file**. If it still fails, delete only the tests *you* added that you cannot make pass, and explain why in the report.
5. Look at `uncovered_lines`. Add tests for uncovered branches that carry real behaviour. Do not chase 100%; skip trivial lines.
6. Finish with one full-suite run per area you touched. The suite must be green (expected failures are fine). Frontend runs must also have no `typecheck_errors` in files you wrote.

## Flakiness

The workflow re-runs your tests a second time. Tests must not depend on order, the current date, time zones, random values or real timers. Fix the clock (`vi.setSystemTime`, or patching `datetime` in the module under test) whenever logic depends on "today" (for example `isOverdue`).
