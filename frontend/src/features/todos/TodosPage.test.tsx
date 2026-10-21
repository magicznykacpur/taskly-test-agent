import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { useNotice } from '../../hooks/useNotice'
import { todoFixture } from '../../test/todoFixture'
import type { Todo } from './types'
import { useTodoFilters } from './hooks/useTodoFilters'
import { useTodosBusy } from './hooks/useTodosBusy'
import { useTodosQuery } from './hooks/useTodosQuery'
import { useUpdateTodoMutation } from './hooks/useUpdateTodoMutation'
import { TodosPage } from './TodosPage'

vi.mock('../../design-system', () => import('../../design-system/mocks'))
vi.mock('../../hooks/useNotice', () => ({ useNotice: vi.fn() }))
vi.mock('./hooks/useTodoFilters', () => ({ useTodoFilters: vi.fn() }))
vi.mock('./hooks/useTodosBusy', () => ({ useTodosBusy: vi.fn() }))
vi.mock('./hooks/useTodosQuery', () => ({ useTodosQuery: vi.fn() }))
vi.mock('./hooks/useUpdateTodoMutation', () => ({
  useUpdateTodoMutation: vi.fn(),
}))
vi.mock('./components/TodosHeader', () => ({
  TodosHeader: ({
    disabled,
    onCreate,
  }: {
    disabled: boolean
    onCreate: () => void
  }) => (
    <h1>
      Tasks
      <button disabled={disabled} onClick={onCreate}>
        New task
      </button>
    </h1>
  ),
}))
vi.mock('./components/TodoFilters', () => ({ TodoFilters: () => null }))
vi.mock('./components/TodoList', () => ({
  TodoList: (props: {
    todos: Todo[]
    onCreate: () => void
    onToggle: (todo: Todo) => void
    onEdit: (todo: Todo) => void
    onDelete: (todo: Todo) => void
  }) => (
    <div>
      <p>Task list</p>
      <button onClick={props.onCreate}>list create</button>
      <button onClick={() => props.onToggle(props.todos[0])}>toggle</button>
      <button onClick={() => props.onEdit(props.todos[0])}>edit</button>
      <button onClick={() => props.onDelete(props.todos[0])}>delete</button>
    </div>
  ),
}))
vi.mock('./components/TodoEditor', () => ({
  TodoEditor: (props: {
    todo: Todo | 'new'
    onClose: () => void
    onSaved: (notice: string) => void
  }) => (
    <div>
      <p>Editor: {props.todo === 'new' ? 'new' : props.todo.title}</p>
      <button onClick={props.onClose}>close editor</button>
      <button onClick={() => props.onSaved('Task saved.')}>save editor</button>
    </div>
  ),
}))
vi.mock('./components/DeleteTodoDialog', () => ({
  DeleteTodoDialog: (props: {
    todo: Todo
    onClose: () => void
    onDeleted: () => void
  }) => (
    <div>
      <p>Deleting: {props.todo.title}</p>
      <button onClick={props.onClose}>close delete</button>
      <button onClick={props.onDeleted}>confirm delete</button>
    </div>
  ),
}))
vi.mock('../../components/SuccessNotice', () => ({ SuccessNotice: () => null }))

const todo = { ...todoFixture, title: 'Write tests' }

function setup({
  busy = false,
  saved = { ...todo, completed: true },
}: { busy?: boolean; saved?: Todo } = {}) {
  const notify = vi.fn()
  const mutateAsync = vi.fn().mockResolvedValue(saved)
  vi.mocked(useTodosQuery).mockReturnValue({
    data: [todo],
    isPending: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useTodosQuery>)
  vi.mocked(useUpdateTodoMutation).mockReturnValue({
    error: null,
    reset: vi.fn(),
    mutateAsync,
  } as unknown as ReturnType<typeof useUpdateTodoMutation>)
  vi.mocked(useTodosBusy).mockReturnValue(busy)
  vi.mocked(useNotice).mockReturnValue({ message: '', notify })
  vi.mocked(useTodoFilters).mockReturnValue({
    filter: 'all',
    search: '',
    sort: 'newest',
    visible: [todo],
    setFilter: vi.fn(),
    setSearch: vi.fn(),
    setSort: vi.fn(),
  })
  render(<TodosPage />)
  return { notify, mutateAsync }
}

it('toggles a task and announces completion or reactivation', async () => {
  const user = userEvent.setup()
  const { notify, mutateAsync } = setup()
  await user.click(screen.getByRole('button', { name: 'toggle' }))
  expect(mutateAsync).toHaveBeenCalledWith({
    id: todo.id,
    input: { completed: true },
  })
  expect(notify).toHaveBeenCalledWith('Another task complete. Well done!')
})

it('announces when a task is marked active again', async () => {
  const user = userEvent.setup()
  const { notify } = setup({ saved: { ...todo, completed: false } })
  await user.click(screen.getByRole('button', { name: 'toggle' }))
  await waitFor(() =>
    expect(notify).toHaveBeenCalledWith('Task marked as active.'),
  )
})

it('does not toggle while busy', async () => {
  const user = userEvent.setup()
  const { notify, mutateAsync } = setup({ busy: true })
  await user.click(screen.getByRole('button', { name: 'toggle' }))
  expect(mutateAsync).not.toHaveBeenCalled()
  expect(notify).not.toHaveBeenCalled()
  expect(screen.getByRole('button', { name: 'New task' })).toBeDisabled()
})

it('does not announce anything when toggling fails', async () => {
  const user = userEvent.setup()
  const { notify, mutateAsync } = setup()
  mutateAsync.mockRejectedValue(new Error('nope'))
  await user.click(screen.getByRole('button', { name: 'toggle' }))
  await waitFor(() => expect(mutateAsync).toHaveBeenCalled())
  expect(notify).not.toHaveBeenCalled()
})

it('opens the editor for a new or existing task and closes or saves it', async () => {
  const user = userEvent.setup()
  const { notify } = setup()
  expect(screen.queryByText(/Editor:/)).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'New task' }))
  expect(screen.getByText('Editor: new')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'close editor' }))
  expect(screen.queryByText(/Editor:/)).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'list create' }))
  expect(screen.getByText('Editor: new')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'close editor' }))
  await user.click(screen.getByRole('button', { name: 'edit' }))
  expect(screen.getByText('Editor: Write tests')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'save editor' }))
  expect(screen.queryByText(/Editor:/)).not.toBeInTheDocument()
  expect(notify).toHaveBeenCalledWith('Task saved.')
})

it('confirms deletion, then closes the dialog and announces it', async () => {
  const user = userEvent.setup()
  const { notify } = setup()
  await user.click(screen.getByRole('button', { name: 'delete' }))
  expect(screen.getByText('Deleting: Write tests')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'close delete' }))
  expect(screen.queryByText(/Deleting:/)).not.toBeInTheDocument()
  expect(notify).not.toHaveBeenCalled()
  await user.click(screen.getByRole('button', { name: 'delete' }))
  await user.click(screen.getByRole('button', { name: 'confirm delete' }))
  expect(screen.queryByText(/Deleting:/)).not.toBeInTheDocument()
  expect(notify).toHaveBeenCalledWith('Task deleted.')
})

it('displays a query failure and resets mutation errors before retrying', async () => {
  const user = userEvent.setup()
  const refetch = vi.fn().mockResolvedValue(undefined)
  const reset = vi.fn()
  vi.mocked(useTodosQuery).mockReturnValue({
    data: [],
    isPending: false,
    isFetching: false,
    isError: true,
    error: new Error('The server is unavailable.'),
    refetch,
  } as unknown as ReturnType<typeof useTodosQuery>)
  vi.mocked(useUpdateTodoMutation).mockReturnValue({
    error: null,
    reset,
    mutateAsync: vi.fn(),
  } as unknown as ReturnType<typeof useUpdateTodoMutation>)
  vi.mocked(useTodosBusy).mockReturnValue(false)
  vi.mocked(useNotice).mockReturnValue({ message: '', notify: vi.fn() })
  vi.mocked(useTodoFilters).mockReturnValue({
    filter: 'all',
    search: '',
    sort: 'newest',
    visible: [],
    setFilter: vi.fn(),
    setSearch: vi.fn(),
    setSort: vi.fn(),
  })
  render(<TodosPage />)
  expect(screen.getByTestId('alert')).toHaveTextContent(
    'The server is unavailable.',
  )
  await user.click(screen.getByRole('button', { name: 'Try again' }))
  await waitFor(() => expect(refetch).toHaveBeenCalledTimes(1))
  expect(reset).toHaveBeenCalledTimes(1)
  expect(reset.mock.invocationCallOrder[0]).toBeLessThan(
    refetch.mock.invocationCallOrder[0],
  )
})
