## 🧪 Unit test agent

**✅ All tests pass.**

Added 8 new frontend test files (http, three mutation hooks, useTodosQuery, useTodosBusy, useTodoFilters, TodoEmptyState). The full frontend suite passes with 43 tests, no type errors, and coverage rose from 47.7% to 72.8%. The other targets already had tests and I did not read or change them, so their decisions are no_change. AppProviders is also no_change because it is wiring only.


### Decisions

| Source file | Decision | Test file | Reason |
|---|---|---|---|
| `frontend/src/lib/http.ts` | 🆕 created | `frontend/src/lib/http.test.ts` | Request handling had no tests; covers headers, 204, network failure, abort rethrow, 422, string detail and generic fallbacks. |
| `frontend/src/features/todos/hooks/useCreateTodoMutation.ts` | 🆕 created | `frontend/src/features/todos/hooks/useCreateTodoMutation.test.tsx` | Cache update logic (prepend, dedupe, empty cache, failure) was untested. |
| `frontend/src/features/todos/hooks/useUpdateTodoMutation.ts` | 🆕 created | `frontend/src/features/todos/hooks/useUpdateTodoMutation.test.tsx` | Cache replacement, missing cache and failure paths were untested. |
| `frontend/src/features/todos/hooks/useDeleteTodoMutation.ts` | 🆕 created | `frontend/src/features/todos/hooks/useDeleteTodoMutation.test.tsx` | Cache removal and failure paths were untested. |
| `frontend/src/features/todos/hooks/useTodosQuery.ts` | 🆕 created | `frontend/src/features/todos/hooks/useTodosQuery.test.tsx` | Covers loading via the API with an abort signal and the error path. |
| `frontend/src/features/todos/hooks/useTodosBusy.ts` | 🆕 created | `frontend/src/features/todos/hooks/useTodosBusy.test.tsx` | Busy flag is true only while a todo-keyed mutation is pending. |
| `frontend/src/features/todos/hooks/useTodoFilters.ts` | 🆕 created | `frontend/src/features/todos/hooks/useTodoFilters.test.ts` | Covers the default state and how filter, search and sort change the visible list. |
| `frontend/src/features/todos/components/TodoEmptyState.tsx` | 🆕 created | `frontend/src/features/todos/components/TodoEmptyState.test.tsx` | It had 0% coverage; covers the first-task state, the disabled button and the no-matches state. |
| `frontend/src/app/AppProviders.tsx` | ➖ no change | `frontend/src/app/AppProviders.test.tsx` | Pure provider wiring with no logic. |
| `frontend/src/App.tsx` | ➖ no change | `frontend/src/App.test.tsx` | A test file exists and passes. I did not read it or the source, so this is not a finding that coverage is sufficient. |
| `frontend/src/components/ApplicationHeader.tsx` | ➖ no change | `frontend/src/components/ApplicationHeader.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/components/SuccessNotice.tsx` | ➖ no change | `frontend/src/components/SuccessNotice.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/TodosPage.tsx` | ➖ no change | `frontend/src/features/todos/TodosPage.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/api/todos.ts` | ➖ no change | `frontend/src/features/todos/api/todos.test.ts` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/DeleteTodoDialog.tsx` | ➖ no change | `frontend/src/features/todos/components/DeleteTodoDialog.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodoEditor.tsx` | ➖ no change | `frontend/src/features/todos/components/TodoEditor.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodoFilters.tsx` | ➖ no change | `frontend/src/features/todos/components/TodoFilters.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodoForm.tsx` | ➖ no change | `frontend/src/features/todos/components/TodoForm.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodoItem.tsx` | ➖ no change | `frontend/src/features/todos/components/TodoItem.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodoList.tsx` | ➖ no change | `frontend/src/features/todos/components/TodoList.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/components/TodosHeader.tsx` | ➖ no change | `frontend/src/features/todos/components/TodosHeader.test.tsx` | A test file exists and passes. I did not inspect it. |
| `frontend/src/features/todos/utils/todos.ts` | ➖ no change | `frontend/src/features/todos/utils/todos.test.ts` | A test file exists and passes. I did not inspect it. |
| `frontend/src/hooks/useNotice.ts` | ➖ no change | `frontend/src/hooks/useNotice.test.ts` | A test file exists and passes. I did not inspect it. |

### Verification

Tests were re-run by the workflow, independently of the agent.

| Area | Passed | Failed | Coverage before → after | Flaky check |
|---|---|---|---|---|
| frontend | 43 | 0 | 47.7% → 72.8% | stable |

<details><summary>Coverage of changed files</summary>

| File | Before | After |
|---|---|---|
| `frontend/src/App.tsx` | 100.0% | 100.0% |
| `frontend/src/app/AppProviders.tsx` | 0.0% | 0.0% |
| `frontend/src/components/ApplicationHeader.tsx` | 100.0% | 100.0% |
| `frontend/src/components/SuccessNotice.tsx` | 100.0% | 100.0% |
| `frontend/src/features/todos/TodosPage.tsx` | 50.0% | 50.0% |
| `frontend/src/features/todos/api/todos.ts` | 57.1% | 57.1% |
| `frontend/src/features/todos/components/DeleteTodoDialog.tsx` | 37.5% | 37.5% |
| `frontend/src/features/todos/components/TodoEditor.tsx` | 90.0% | 90.0% |
| `frontend/src/features/todos/components/TodoEmptyState.tsx` | 0.0% | 100.0% |
| `frontend/src/features/todos/components/TodoFilters.tsx` | 100.0% | 100.0% |
| `frontend/src/features/todos/components/TodoForm.tsx` | 87.5% | 87.5% |
| `frontend/src/features/todos/components/TodoItem.tsx` | 100.0% | 100.0% |
| `frontend/src/features/todos/components/TodoList.tsx` | 20.0% | 20.0% |
| `frontend/src/features/todos/components/TodosHeader.tsx` | 100.0% | 100.0% |
| `frontend/src/features/todos/hooks/useCreateTodoMutation.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/hooks/useDeleteTodoMutation.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/hooks/useTodoFilters.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/hooks/useTodosBusy.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/hooks/useTodosQuery.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/hooks/useUpdateTodoMutation.ts` | 0.0% | 100.0% |
| `frontend/src/features/todos/utils/todos.ts` | 52.0% | 60.0% |
| `frontend/src/hooks/useNotice.ts` | 71.4% | 71.4% |
| `frontend/src/lib/http.ts` | 0.0% | 100.0% |

</details>

---
<sub>Skills used: `run-unit-tests`, `vitest-react-tests`, `test-impact-analysis` · Agent run: 32 turns, 112s, $0.24</sub>
