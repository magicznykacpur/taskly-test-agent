import { afterEach, describe, expect, it, vi } from 'vitest'
import { formatDate, isOverdue, selectTodos, validateTodo } from './todos'
import type { Todo } from '../types'

const base: Todo = {
  id: 1,
  title: 'Sprint plan',
  description: '',
  priority: 'medium',
  completed: false,
  due_date: null,
  created_at: '2026-10-01T12:00:00Z',
  updated_at: '2026-10-01T12:00:00Z',
}

describe('selectTodos', () => {
  it('combines status with a case-insensitive search in the description', () => {
    const matching = { ...base, description: 'Discuss the API' }
    const todos = [
      matching,
      { ...matching, id: 2, completed: true },
      { ...base, id: 3 },
    ]
    expect(selectTodos(todos, 'active', ' api ', 'newest')).toEqual([matching])
  })

  it('sorts by priority without changing the source array', () => {
    const high: Todo = { ...base, id: 2, priority: 'high' }
    const todos = [base, high]
    expect(selectTodos(todos, 'all', '', 'priority')).toEqual([high, base])
    expect(todos).toEqual([base, high])
  })
})

describe('validateTodo', () => {
  const valid = {
    title: 'Task',
    description: '',
    priority: 'medium' as const,
    due_date: null,
    completed: false,
  }

  it('accepts a valid task', () => {
    expect(validateTodo({ ...valid, due_date: '2026-02-28' })).toEqual({})
  })

  it.each([
    ['   ', 'Enter a task title.'],
    ['a'.repeat(120), undefined],
    ['a'.repeat(121), 'The title must be at most 120 characters.'],
  ])('validates title %#', (title, message) => {
    expect(validateTodo({ ...valid, title }).title).toBe(message)
  })

  it.each([
    ['a'.repeat(2000), undefined],
    ['a'.repeat(2001), 'The description must be at most 2000 characters.'],
  ])('validates description length %#', (description, message) => {
    expect(validateTodo({ ...valid, description }).description).toBe(message)
  })

  it.each([
    ['2026-02-30', 'Enter a valid date.'],
    ['2026-13-01', 'Enter a valid date.'],
    ['26-1-1', 'Enter a valid date.'],
    ['2026-02-28', undefined],
    ['2028-02-29', undefined],
  ])('validates due date %s', (due_date, message) => {
    expect(validateTodo({ ...valid, due_date }).due_date).toBe(message)
  })
})

describe('selectTodos ordering', () => {
  it('sorts by due date with undated tasks last, then newest id first', () => {
    const late = { ...base, id: 1, due_date: '2026-11-01' }
    const soon = { ...base, id: 2, due_date: '2026-10-05' }
    const none = { ...base, id: 3 }
    const tie = { ...base, id: 4, due_date: '2026-10-05' }
    expect(selectTodos([late, none, soon, tie], 'all', '', 'due')).toEqual([
      tie,
      soon,
      late,
      none,
    ])
  })

  it('sorts newest by creation time, breaking ties by id', () => {
    const older = { ...base, id: 1, created_at: '2026-09-01T00:00:00Z' }
    const newer = { ...base, id: 2 }
    const tie = { ...base, id: 3 }
    expect(selectTodos([older, newer, tie], 'all', '', 'newest')).toEqual([
      tie,
      newer,
      older,
    ])
  })

  it('filters completed tasks and breaks priority ties by id', () => {
    const done = { ...base, id: 1, completed: true }
    const a = { ...base, id: 2 }
    const b = { ...base, id: 3 }
    expect(selectTodos([done, a, b], 'completed', '', 'priority')).toEqual([
      done,
    ])
    expect(selectTodos([a, b], 'active', '', 'priority')).toEqual([b, a])
  })
})

describe('isOverdue', () => {
  afterEach(() => vi.useRealTimers())

  it.each([
    ['2026-10-14', false, true],
    ['2026-10-15', false, false],
    ['2026-10-16', false, false],
    ['2026-10-14', true, false],
    [null, false, false],
  ])('due %s completed %s gives %s', (due_date, completed, expected) => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 15, 12))
    expect(isOverdue({ ...base, due_date, completed })).toBe(expected)
  })
})

describe('formatDate', () => {
  it('formats an ISO date in en-GB style', () => {
    expect(formatDate('2026-10-05')).toBe('5 Oct 2026')
  })
})
