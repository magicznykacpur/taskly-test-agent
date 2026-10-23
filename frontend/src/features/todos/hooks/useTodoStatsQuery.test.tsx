import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import { useTodoStatsQuery } from './useTodoStatsQuery'

vi.mock('../api/todos', () => ({
  todosApi: { stats: vi.fn() },
}))

beforeEach(() => vi.clearAllMocks())

function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { client, wrapper }
}

const stats = { total: 3, completed: 1, active: 2, overdue: 1 }

it('loads statistics through the API with an abort signal', async () => {
  const { client, wrapper } = setup()
  vi.mocked(todosApi.stats).mockResolvedValue(stats)
  const { result } = renderHook(() => useTodoStatsQuery(), { wrapper })

  await waitFor(() => expect(result.current.data).toEqual(stats))
  expect(todosApi.stats).toHaveBeenCalledWith(expect.any(AbortSignal))
  expect(client.getQueryData(todoKeys.stats)).toEqual(stats)
})

it('exposes the error when loading statistics fails', async () => {
  const { wrapper } = setup()
  vi.mocked(todosApi.stats).mockRejectedValue(new Error('down'))
  const { result } = renderHook(() => useTodoStatsQuery(), { wrapper })

  await waitFor(() => expect(result.current.isError).toBe(true))
})
