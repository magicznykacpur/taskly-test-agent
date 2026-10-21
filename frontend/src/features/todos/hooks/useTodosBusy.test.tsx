import type { ReactNode } from 'react'
import {
  QueryClient,
  QueryClientProvider,
  useMutation,
} from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { expect, it } from 'vitest'
import { todoKeys } from '../api/queryKeys'
import { useTodosBusy } from './useTodosBusy'

function setup() {
  const client = new QueryClient()
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  return { wrapper }
}

it('is busy only while a todo mutation is pending', async () => {
  const { wrapper } = setup()
  let release!: () => void
  const { result } = renderHook(
    () => ({
      busy: useTodosBusy(),
      mutation: useMutation({
        mutationKey: todoKeys.create,
        mutationFn: () => new Promise<void>((resolve) => (release = resolve)),
      }),
    }),
    { wrapper },
  )
  expect(result.current.busy).toBe(false)

  act(() => result.current.mutation.mutate())
  await waitFor(() => expect(result.current.busy).toBe(true))

  await act(async () => release())
  await waitFor(() => expect(result.current.busy).toBe(false))
})

it('ignores mutations that are not todo mutations', async () => {
  const { wrapper } = setup()
  const { result } = renderHook(
    () => ({
      busy: useTodosBusy(),
      mutation: useMutation({
        mutationKey: ['other'],
        mutationFn: () => new Promise<void>(() => {}),
      }),
    }),
    { wrapper },
  )

  act(() => result.current.mutation.mutate())
  await waitFor(() => expect(result.current.mutation.isPending).toBe(true))

  expect(result.current.busy).toBe(false)
})
