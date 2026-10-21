import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { TodoList } from './TodoList'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))
vi.mock('./TodoEmptyState', () => ({
  TodoEmptyState: () => <p>Empty task list</p>,
}))
vi.mock('./TodoItem', () => ({
  TodoItem: ({
    todo,
    busy,
    onToggle,
    onEdit,
    onDelete,
  }: {
    todo: { id: number; title: string }
    busy: boolean
    onToggle: () => void
    onEdit: () => void
    onDelete: () => void
  }) => (
    <li>
      {todo.title}
      <span>{busy ? 'busy' : 'idle'}</span>
      <button onClick={onToggle}>toggle {todo.id}</button>
      <button onClick={onEdit}>edit {todo.id}</button>
      <button onClick={onDelete}>delete {todo.id}</button>
    </li>
  ),
}))

const props = {
  todos: [],
  hasTodos: false,
  loading: false,
  failed: false,
  busy: false,
  onCreate: vi.fn(),
  onToggle: vi.fn(),
  onEdit: vi.fn(),
  onDelete: vi.fn(),
}

it('renders tasks and forwards each action with its task', async () => {
  const user = userEvent.setup()
  const a = { ...todoFixture, id: 1, title: 'First' }
  const b = { ...todoFixture, id: 2, title: 'Second' }
  const handlers = { onToggle: vi.fn(), onEdit: vi.fn(), onDelete: vi.fn() }
  render(<TodoList {...props} {...handlers} todos={[a, b]} hasTodos busy />)
  expect(screen.getAllByRole('listitem')).toHaveLength(2)
  expect(screen.getAllByText('busy')).toHaveLength(2)
  await user.click(screen.getByRole('button', { name: 'toggle 2' }))
  await user.click(screen.getByRole('button', { name: 'edit 1' }))
  await user.click(screen.getByRole('button', { name: 'delete 2' }))
  expect(handlers.onToggle).toHaveBeenCalledWith(b)
  expect(handlers.onEdit).toHaveBeenCalledWith(a)
  expect(handlers.onDelete).toHaveBeenCalledWith(b)
})

it('shows an unavailable message only when loading failed with no tasks', () => {
  const { rerender } = render(<TodoList {...props} failed />)
  expect(
    screen.getByText('The task list is temporarily unavailable'),
  ).toBeVisible()
  rerender(<TodoList {...props} failed hasTodos todos={[{ ...todoFixture }]} />)
  expect(
    screen.queryByText('The task list is temporarily unavailable'),
  ).not.toBeInTheDocument()
  expect(screen.getByText(todoFixture.title)).toBeVisible()
})

it('shows loading feedback before showing an empty list', () => {
  const props = {
    todos: [],
    hasTodos: false,
    failed: false,
    busy: false,
    onCreate: vi.fn(),
    onToggle: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
  }
  const { rerender } = render(<TodoList {...props} loading />)
  expect(screen.getByRole('status')).toHaveTextContent('Loading your tasks…')
  expect(screen.queryByText('Empty task list')).not.toBeInTheDocument()
  rerender(<TodoList {...props} loading={false} />)
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(screen.getByText('Empty task list')).toBeVisible()
})
