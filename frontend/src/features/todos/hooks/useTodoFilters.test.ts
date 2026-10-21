import { act, renderHook } from '@testing-library/react'
import { expect, it } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { useTodoFilters } from './useTodoFilters'

const todos = [
  { ...todoFixture, id: 1, title: 'Write report', created_at: '2026-10-01' },
  {
    ...todoFixture,
    id: 2,
    title: 'Buy milk',
    completed: true,
    created_at: '2026-10-02',
  },
]

it('starts with all todos, newest first', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  expect(result.current.filter).toBe('all')
  expect(result.current.search).toBe('')
  expect(result.current.sort).toBe('newest')
  expect(result.current.visible.map((todo) => todo.id)).toEqual([2, 1])
})

it('applies status filter, search and sort to the visible todos', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setFilter('completed'))
  expect(result.current.visible.map((todo) => todo.id)).toEqual([2])

  act(() => result.current.setFilter('all'))
  act(() => result.current.setSearch('report'))
  expect(result.current.visible.map((todo) => todo.id)).toEqual([1])

  act(() => result.current.setSearch(''))
  act(() => result.current.setSort('priority'))
  expect(result.current.sort).toBe('priority')
  expect(result.current.visible.map((todo) => todo.id)).toEqual([2, 1])
})
