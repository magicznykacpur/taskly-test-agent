import { render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { useTodoStatsQuery } from '../hooks/useTodoStatsQuery'
import { TodoStatsSummary } from './TodoStatsSummary'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))
vi.mock('../hooks/useTodoStatsQuery', () => ({ useTodoStatsQuery: vi.fn() }))

beforeEach(() => vi.clearAllMocks())

function mockQuery(value: { data?: object; isError?: boolean }) {
  vi.mocked(useTodoStatsQuery).mockReturnValue({
    data: undefined,
    isError: false,
    ...value,
  } as unknown as ReturnType<typeof useTodoStatsQuery>)
}

it('shows a loading status until statistics arrive', () => {
  mockQuery({})
  render(<TodoStatsSummary />)
  expect(screen.getByRole('status')).toHaveTextContent('Loading statistics…')
})

it('renders nothing when loading statistics failed', () => {
  mockQuery({ isError: true })
  const { container } = render(<TodoStatsSummary />)
  expect(container).toBeEmptyDOMElement()
})

it('renders nothing when there are no tasks', () => {
  mockQuery({ data: { total: 0, completed: 0, active: 0, overdue: 0 } })
  const { container } = render(<TodoStatsSummary />)
  expect(container).toBeEmptyDOMElement()
})

it('shows counts, overdue badge and rounded completion percentage', () => {
  mockQuery({ data: { total: 3, completed: 1, active: 2, overdue: 1 } })
  render(<TodoStatsSummary />)
  expect(screen.getByRole('region', { name: 'Task statistics' })).toBeVisible()
  expect(screen.getByText('2 active')).toBeVisible()
  expect(screen.getByText('1 completed')).toBeVisible()
  expect(screen.getByText('1 overdue')).toBeVisible()
  expect(screen.getByText('33% done')).toBeVisible()
})

it('hides the overdue badge when nothing is overdue', () => {
  mockQuery({ data: { total: 2, completed: 2, active: 0, overdue: 0 } })
  render(<TodoStatsSummary />)
  expect(screen.queryByText(/overdue/)).not.toBeInTheDocument()
  expect(screen.getByText('100% done')).toBeVisible()
})
