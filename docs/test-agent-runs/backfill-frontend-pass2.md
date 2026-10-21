## 🧪 Unit test agent

**✅ All tests pass.**

Backfilled tests for all 8 frontend targets. The full frontend suite passes (83 tests, up from 43), typecheck is clean, and line coverage went from 72.8% to 99.3%. No source files were changed.


### Decisions

| Source file | Decision | Test file | Reason |
|---|---|---|---|
| `frontend/src/app/AppProviders.tsx` | 🆕 created | `frontend/src/app/AppProviders.test.tsx` | The file had no test. New tests check that children get the default query client, the theme and GlobalStyles, and that a client passed as a prop is used. |
| `frontend/src/features/todos/components/TodoList.tsx` | ✏️ updated | `frontend/src/features/todos/components/TodoList.test.tsx` | The populated list branch was untested. New tests check that the toggle, edit and delete callbacks receive the right task and that busy is passed down. They also check the unavailable message appears only when loading failed and no tasks are cached. The TodoItem stub was extended with buttons. |
| `frontend/src/features/todos/components/DeleteTodoDialog.tsx` | ✏️ updated | `frontend/src/features/todos/components/DeleteTodoDialog.test.tsx` | The remove() paths were untested. New tests cover successful delete calling onDeleted, a failed delete staying open without onDeleted, and actions being disabled when pending or busy. |
| `frontend/src/features/todos/TodosPage.tsx` | ✏️ updated | `frontend/src/features/todos/TodosPage.test.tsx` | Toggle, editor and delete flows were untested. New tests cover completion and reactivation notices, the busy guard, a failed toggle staying silent, opening, closing and saving the editor, and delete close and confirm. The child stubs were extended to expose callbacks. |
| `frontend/src/features/todos/api/todos.ts` | ✏️ updated | `frontend/src/features/todos/api/todos.test.ts` | update and remove were untested. New tests check the PATCH body contains only writable fields and that remove sends DELETE to the right URL. |
| `frontend/src/features/todos/utils/todos.ts` | ✏️ updated | `frontend/src/features/todos/utils/todos.test.ts` | validateTodo, isOverdue, formatDate and the due and newest sorts were untested. New table-driven cases cover title and description length boundaries and invalid dates such as 2026-02-30. isOverdue runs with a fixed system time, and the sort tests cover id tiebreaks. |
| `frontend/src/hooks/useNotice.ts` | ✏️ updated | `frontend/src/hooks/useNotice.test.ts` | The timeout logic was untested. New tests use fake timers to check a notice clears after 4s, a new notice restarts the timer, and notify stays stable across renders. |
| `frontend/src/features/todos/components/TodoForm.tsx` | ✏️ updated | `frontend/src/features/todos/components/TodoForm.test.tsx` | The description onChange and due-date clearing were untested. One new test covers description validation and trimming, and clearing the due date submitting null. |

### Verification

Tests were re-run by the workflow, independently of the agent.

| Area | Passed | Failed | Coverage before → after | Flaky check |
|---|---|---|---|---|
| frontend | 83 | 0 | 72.8% → 99.3% | stable |

<details><summary>Coverage of changed files</summary>

| File | Before | After |
|---|---|---|
| `frontend/src/app/AppProviders.tsx` | 0.0% | 100.0% |
| `frontend/src/features/todos/components/TodoList.tsx` | 20.0% | 100.0% |
| `frontend/src/features/todos/components/DeleteTodoDialog.tsx` | 37.5% | 100.0% |
| `frontend/src/features/todos/TodosPage.tsx` | 50.0% | 100.0% |
| `frontend/src/features/todos/api/todos.ts` | 57.1% | 100.0% |
| `frontend/src/features/todos/utils/todos.ts` | 60.0% | 100.0% |
| `frontend/src/hooks/useNotice.ts` | 71.4% | 100.0% |
| `frontend/src/features/todos/components/TodoForm.tsx` | 87.5% | 100.0% |

</details>

<details><summary>Skipped by the planner</summary>

- `frontend/src/App.tsx`: already 100% covered
- `frontend/src/components/ApplicationHeader.tsx`: already 100% covered
- `frontend/src/components/SuccessNotice.tsx`: already 100% covered
- `frontend/src/features/todos/components/TodoEditor.tsx`: already 90% covered
- `frontend/src/features/todos/components/TodoEmptyState.tsx`: already 100% covered
- `frontend/src/features/todos/components/TodoFilters.tsx`: already 100% covered
- `frontend/src/features/todos/components/TodoItem.tsx`: already 100% covered
- `frontend/src/features/todos/components/TodosHeader.tsx`: already 100% covered
- `frontend/src/features/todos/hooks/useCreateTodoMutation.ts`: already 100% covered
- `frontend/src/features/todos/hooks/useDeleteTodoMutation.ts`: already 100% covered
- `frontend/src/features/todos/hooks/useTodoFilters.ts`: already 100% covered
- `frontend/src/features/todos/hooks/useTodosBusy.ts`: already 100% covered
- `frontend/src/features/todos/hooks/useTodosQuery.ts`: already 100% covered
- `frontend/src/features/todos/hooks/useUpdateTodoMutation.ts`: already 100% covered
- `frontend/src/lib/http.ts`: already 100% covered

</details>

---
<sub>Skills used: `run-unit-tests`, `vitest-react-tests`, `test-impact-analysis` · Agent run: 39 turns, 109s, $0.34</sub>
