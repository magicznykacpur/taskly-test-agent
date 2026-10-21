import { afterEach, expect, it, vi } from 'vitest'
import { request } from './http'

function stubFetch() {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

it('prefixes the path with /api and sends JSON headers merged with custom ones', async () => {
  const fetchMock = stubFetch()
  fetchMock.mockResolvedValue(json({ ok: true }))

  await expect(
    request('/todos', { method: 'POST', headers: { 'X-Test': '1' } }),
  ).resolves.toEqual({ ok: true })

  expect(fetchMock).toHaveBeenCalledWith('/api/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Test': '1' },
  })
})

it('returns undefined for a 204 response', async () => {
  stubFetch().mockResolvedValue(new Response(null, { status: 204 }))
  await expect(request('/todos/1')).resolves.toBeUndefined()
})

it('throws a connection message when fetch fails', async () => {
  stubFetch().mockRejectedValue(new TypeError('Failed to fetch'))
  await expect(request('/todos')).rejects.toThrow(
    'Cannot connect to the server. Please try again.',
  )
})

it('rethrows the original error when the request was aborted', async () => {
  const controller = new AbortController()
  controller.abort()
  const abortError = new DOMException('Aborted', 'AbortError')
  stubFetch().mockRejectedValue(abortError)

  await expect(request('/todos', { signal: controller.signal })).rejects.toBe(
    abortError,
  )
})

it('shows validation guidance for a 422 response', async () => {
  stubFetch().mockResolvedValue(json({ detail: 'ignored' }, 422))
  await expect(request('/todos')).rejects.toThrow(/Check the task details/)
})

it('uses the string detail from an error response', async () => {
  stubFetch().mockResolvedValue(json({ detail: 'Todo not found' }, 404))
  await expect(request('/todos/9')).rejects.toThrow('Todo not found')
})

it.each([
  ['a non-string detail', json({ detail: [{ msg: 'x' }] }, 500)],
  ['a body that is not JSON', new Response('oops', { status: 500 })],
])('falls back to a generic message for %s', async (_name, response) => {
  stubFetch().mockResolvedValue(response)
  await expect(request('/todos')).rejects.toThrow(
    'The operation failed. Please try again.',
  )
})
