---
name: test-impact-analysis
description: Decide whether a changed source file needs a new unit test, an updated test, or no test change, and pick the test file. Use before writing any test for a pull request or coverage task.
---

# Test impact analysis

Make one decision per target file: `created`, `updated` or `no_change`, each with a one-sentence reason a reviewer can check.

## Steps

1. Read the whole source file, not only the diff. A diff hides the surrounding contract.
2. Find the existing tests for it:
   - the conventional test file named in the task (backend `backend/tests/<same path>/test_<module>.py`, frontend `<Name>.test.tsx` next to the component),
   - other tests that import it: `Grep` for the module name in `backend/tests` or `frontend/src/**/*.test.*`.
3. Classify the change using the table below.
4. If tests are needed, list the concrete behaviours to cover before writing code (inputs → expected outputs, branches, error paths). This list becomes the test names.

## Decision table

| Change | Decision |
|---|---|
| New module, function, endpoint, component or hook with logic | `created`: add a test file, or a new section in the existing one |
| New branch, condition, validation rule, error path or prop that changes output | `updated`: add cases for the new behaviour |
| Changed behaviour (different result, message, status code, ordering) | `updated`: change the assertions that encode the old behaviour and add cases for the new one. Explain the change in the reason |
| Rename or move with no behaviour change | `updated` only if existing tests break (imports, names); otherwise `no_change` |
| Pure refactor already covered (coverage of changed lines stays high and tests pass) | `no_change`: say which tests cover it |
| Formatting, comments, logging text, type-only changes | `no_change` |
| Glue with no logic (re-exports, plain wiring) | `no_change`, unless it is completely untested and cheap to test |

In backfill mode, every target is "existing code" that is below the coverage threshold. The fact that a test file exists is never a reason for `no_change` on its own: read it, compare it with the uncovered lines, and add the missing cases. Prioritise by risk: uncovered branches in business logic (validators, repository, utils, hooks, request handling) come before trivial presentational code.

## What makes a test worth adding

- It would fail if the behaviour broke. A test that only checks that a function "is defined" or that a component "renders" without asserting output adds no value.
- It checks behaviour through the public interface (HTTP response, return value, rendered text, roles, called callbacks), not private details.
- It covers edges: empty input, boundaries (exactly 120 characters vs 121), `None`/`null`, not-found, error responses, disabled/busy states.
- It does not duplicate a case that already exists.

## Changed tests written by the PR author

If the author already changed or added tests for a target, read them first. Add only the cases that are still missing, and never rewrite their assertions.
