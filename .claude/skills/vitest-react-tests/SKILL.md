---
name: vitest-react-tests
description: Conventions and patterns for writing Vitest + React Testing Library unit tests for the React/TypeScript frontend in frontend/src. Use when creating or updating any *.test.ts or *.test.tsx file.
---

# Frontend unit tests (Vitest + React Testing Library)

The frontend is React 19 + TypeScript with TanStack Query and styled-components. Tests are colocated: `Foo.tsx` is tested in `Foo.test.tsx` and `foo.ts` in `foo.test.ts`. The environment is jsdom, and `src/test/setup.ts` loads jest-dom matchers and runs `cleanup` after each test.

## Style (match the existing tests exactly)

- Import test functions explicitly: `import { beforeEach, expect, it, vi } from 'vitest'`.
- Top-level `it(...)` blocks, no `describe` nesting. Each name is a sentence describing behaviour: `it('shows a deletion error and allows cancelling without deleting', ...)`.
- Prettier style: no semicolons, single quotes, trailing commas, 80 columns. The workflow runs Prettier on your files afterwards, but write them close to that style.
- TypeScript strict mode applies to tests too. Cast partial mocks as the existing tests do: `as unknown as ReturnType<typeof useDeleteTodoMutation>`.
- Use the shared fixture `todoFixture` from `src/test/todoFixture.ts`, spread to vary it: `{ ...todoFixture, id: 8, completed: true }`.

## Queries and interactions

- Query like a user: `getByRole` with `name`, `getByLabelText`, `getByText`. Use `getByTestId('alert')` only for mocked design-system components that expose a test id.
- Interact with `userEvent.setup()` and `await user.click(...)`, `user.type(...)`, `user.selectOptions(...)`. Not `fireEvent`.
- Assert absence with `queryBy*` plus `.not.toBeInTheDocument()`. Use `await screen.findBy*` or `waitFor` for async UI.

## Mocking

- **Design system**: components under test that import from `design-system` must mock it with the lightweight test doubles. The relative path depends on the file's depth:
  ```ts
  vi.mock('../../../design-system', () => import('../../../design-system/mocks'))
  ```
- **Child components**: when testing a container (such as `TodosPage` or `TodoList`), replace children with simple stubs, as `TodosPage.test.tsx` does, so the test covers only the container's logic.
- **Hooks used by a component**: `vi.mock('../hooks/useX', () => ({ useX: vi.fn() }))`, then `vi.mocked(useX).mockReturnValue({...})` in each test.
- **API layer**: mock `../../../lib/http` (`request: vi.fn()`) to test `todosApi`, or mock `../api/todos` (`todosApi: { create: vi.fn(), ... }`) to test hooks.
- **fetch** (for `src/lib/http.ts`): `vi.stubGlobal('fetch', vi.fn())` and return `new Response(JSON.stringify(body), { status })`. Call `vi.unstubAllGlobals()` in `afterEach`.
- **Timers** (for example `useNotice`'s 4 second timeout): `vi.useFakeTimers()`, wrap `vi.advanceTimersByTime(...)` in `act(...)`, and `vi.useRealTimers()` in `afterEach`. Do not combine fake timers with `userEvent` unless you pass `advanceTimers: vi.advanceTimersByTime`.
- Reset between tests with `beforeEach(() => vi.clearAllMocks())` when mocks are shared at module level.

## Testing TanStack Query hooks

Render the hook with a fresh client per test so cache state never leaks between tests:

```tsx
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { client, wrapper }
}

it('adds a created task to the top of the cached list', async () => {
  const { client, wrapper } = setup()
  client.setQueryData(todoKeys.list, [todoFixture])
  vi.mocked(todosApi.create).mockResolvedValue({ ...todoFixture, id: 8 })
  const { result } = renderHook(() => useCreateTodoMutation(), { wrapper })
  await act(() => result.current.mutateAsync(todoFixture))
  expect(client.getQueryData(todoKeys.list)).toEqual([
    { ...todoFixture, id: 8 },
    todoFixture,
  ])
})
```

A hook test file that contains JSX must use the `.test.tsx` extension.

## What to cover

- Every branch in render logic: loading, error, empty, populated, disabled/busy.
- Every callback prop: it is called with the right arguments, and not called when the control is disabled or the action is cancelled.
- Error paths: rejected promises keep the UI open and show the message.
- Utility functions: table-driven with `it.each` for boundaries (for example 120 vs 121 characters, invalid dates such as `2026-02-30`).

## Running

```bash
python3 tools/test-agent/run_tests.py frontend frontend/src/lib/http.test.ts --focus frontend/src/lib/http.ts --typecheck
```

See the `run-unit-tests` skill for how to read the output.
