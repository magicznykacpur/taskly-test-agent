import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import { useCreateTodoMutation } from './useCreateTodoMutation'

vi.mock('../api/todos', () => ({
  todosApi: { create: vi.fn() },
}))

beforeEach(() => vi.clearAllMocks())

function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { client, wrapper }
}

const input = {
  title: 'Prepare a demo',
  description: '',
  priority: 'medium' as const,
  due_date: null,
  completed: false,
}

it('adds a created task to the top of the cached list', async () => {
  const { client, wrapper } = setup()
  client.setQueryData(todoKeys.list, [todoFixture])
  vi.mocked(todosApi.create).mockResolvedValue({ ...todoFixture, id: 8 })
  const { result } = renderHook(() => useCreateTodoMutation(), { wrapper })

  await act(() => result.current.mutateAsync(input))

  expect(todosApi.create).toHaveBeenCalledWith(input)
  expect(client.getQueryData(todoKeys.list)).toEqual([
    { ...todoFixture, id: 8 },
    todoFixture,
  ])
})

it('creates the cached list when none exists and avoids duplicates', async () => {
  const { client, wrapper } = setup()
  vi.mocked(todosApi.create).mockResolvedValue(todoFixture)
  const { result } = renderHook(() => useCreateTodoMutation(), { wrapper })

  await act(() => result.current.mutateAsync(input))
  expect(client.getQueryData(todoKeys.list)).toEqual([todoFixture])

  await act(() => result.current.mutateAsync(input))
  expect(client.getQueryData(todoKeys.list)).toEqual([todoFixture])
})

it('leaves the cache untouched when creation fails', async () => {
  const { client, wrapper } = setup()
  client.setQueryData(todoKeys.list, [todoFixture])
  vi.mocked(todosApi.create).mockRejectedValue(new Error('boom'))
  const { result } = renderHook(() => useCreateTodoMutation(), { wrapper })

  await act(async () => {
    await expect(result.current.mutateAsync(input)).rejects.toThrow('boom')
  })

  expect(client.getQueryData(todoKeys.list)).toEqual([todoFixture])
})
