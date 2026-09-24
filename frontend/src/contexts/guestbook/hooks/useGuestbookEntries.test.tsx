import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/problem'

import {
  guestbookEntryKeys,
  useCreateGuestbookEntry,
  useDeleteGuestbookEntry,
  useGuestbookEntries,
  useUpdateGuestbookEntry,
} from './useGuestbookEntries'
import type { GuestbookEntryPaging, GuestbookEntryQuery } from './useGuestbookEntries'

/**
 * The seam between the screen and the wire, tested where neither of its
 * neighbours can see it.
 *
 * The page test proves the screen reacts; the client test proves a request goes
 * out. What lives only here is the **cache contract**: one key shape, every
 * mutation invalidating it, and a `DELETE` that answers `204` resolving rather
 * than failing on its missing body. Each of those is the kind of thing that
 * breaks into a stale list -- a screen showing what was true one action ago,
 * with no error anywhere.
 *
 * Stubbing follows `api/client.test.ts`: `openapi-fetch` captures
 * `globalThis.fetch` when `client.ts` is imported, and undici's `Request`
 * refuses an origin-less path, so both are replaced before the module graph
 * loads.
 */
const stubs = vi.hoisted(() => {
  const RealRequest = globalThis.Request

  function RequestWithBase(input: RequestInfo | URL, init?: RequestInit): Request {
    const absolute =
      typeof input === 'string' && input.startsWith('/') ? `http://localhost${input}` : input
    return new RealRequest(absolute, init)
  }
  RequestWithBase.prototype = RealRequest.prototype
  vi.stubGlobal('Request', RequestWithBase)

  const fetchStub = vi.fn(
    (_input: Request): Promise<Response> =>
      Promise.reject(new Error('fetch called before the test configured a response')),
  )
  vi.stubGlobal('fetch', fetchStub)
  return { fetchStub }
})

const ENTRY = {
  id: '11111111-1111-4111-8111-111111111111',
  author: 'Anna',
  message: 'Hello there',
  created_at: '2026-08-30T20:00:00Z',
  updated_at: '2026-08-30T20:00:00Z',
}

/** One page holding that entry, in the envelope the contract answers with. */
const PAGE = { items: [ENTRY], total: 1, total_all: 1 }

/** What the screen asks for on its first read.
 *
 * Annotated rather than `as const`: the literal type would narrow `search` to
 * `''` and make every other phrase below a type error, which is a test that
 * cannot express the thing it is testing. */
const FIRST_READ: GuestbookEntryQuery = { search: '', sort: 'newest' }

/** How much of the answer the address asks for: one piece of four. */
const FIRST_PIECE: GuestbookEntryPaging = { shown: 4, step: 4 }

function json(body: unknown, status = 200): Response {
  return status === 204
    ? new Response(null, { status })
    : new Response(JSON.stringify(body), {
        status,
        headers: { 'content-type': 'application/json' },
      })
}

/** A client with retries off, so a failing test fails now rather than in a second. */
function harness() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const invalidated: unknown[][] = []
  const realInvalidate = queryClient.invalidateQueries.bind(queryClient)
  queryClient.invalidateQueries = ((filters?: { queryKey?: unknown[] }) => {
    if (filters?.queryKey) invalidated.push(filters.queryKey)
    return realInvalidate(filters as never)
  }) as typeof queryClient.invalidateQueries

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return { wrapper, queryClient, invalidated }
}

/** The last request the hook actually put on the wire. */
function sent(): Request {
  const call = stubs.fetchStub.mock.calls.at(-1)
  if (call === undefined) throw new Error('no request was sent')
  return call[0]
}

beforeEach(() => {
  stubs.fetchStub.mockReset()
  stubs.fetchStub.mockImplementation((request: Request) =>
    Promise.resolve(request.method === 'DELETE' ? json(null, 204) : json(PAGE)),
  )
})

describe('the query keys', () => {
  it('nest the list under the resource, so one invalidation reaches every read', () => {
    // `all` is a prefix of `list()`. If it stopped being one, a mutation would
    // invalidate a key nothing reads and the screen would keep showing the
    // previous answer -- with no error to notice.
    expect(guestbookEntryKeys.list(FIRST_READ).slice(0, guestbookEntryKeys.all.length)).toEqual([
      ...guestbookEntryKeys.all,
    ])
  })

  it('separate two different reads, so a search cannot answer with another search', () => {
    // Two phrases are two questions with two answers. One shared key would make
    // the second phrase show the first one's results until its refetch landed --
    // and going back to a phrase already typed would show them again.
    expect(guestbookEntryKeys.list({ ...FIRST_READ, search: 'anna' })).not.toEqual(
      guestbookEntryKeys.list({ ...FIRST_READ, search: 'brian' }),
    )
    expect(guestbookEntryKeys.list({ ...FIRST_READ, sort: 'oldest' })).not.toEqual(
      guestbookEntryKeys.list(FIRST_READ),
    )
  })

  it('carry the question and nothing about how much of it is on screen [req:CR-2609-9b1e/R-7]', () => {
    // `limit` used to be a third member, and that is what broke paging: asking
    // for a bigger piece looked to the cache like somebody had asked something
    // else, and once the size reached the contract's ceiling it stopped moving
    // at all -- so pressing "Load more" changed the key by nothing and refetched
    // nothing. The key is now the question; how much of the answer is on screen
    // is an argument beside it.
    expect(guestbookEntryKeys.list(FIRST_READ)).toEqual([
      'guestbook-entries',
      'list',
      { search: '', sort: 'newest' },
    ])
  })
})

describe('reading the list', () => {
  it('asks the path the schema names and returns the page whole', async () => {
    const { wrapper } = harness()

    const { result } = renderHook(() => useGuestbookEntries(FIRST_READ, FIRST_PIECE), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(new URL(sent().url).pathname).toBe('/api/guestbook-entries')
    // Both counts survive the flattening: a hook that returned only `items`
    // would leave the screen deriving "3 matches" from the page length, which is
    // the number the envelope exists to stop it guessing.
    expect(result.current.data).toEqual({
      entries: PAGE.items,
      total: PAGE.total,
      totalAll: PAGE.total_all,
      answering: FIRST_READ,
    })
  })

  it('hands back the question its answer came for [req:CR-2609-9b1e/R-6]', async () => {
    const { wrapper } = harness()

    const { result, rerender } = renderHook(
      (query: Parameters<typeof useGuestbookEntries>[0]) =>
        useGuestbookEntries(query, FIRST_PIECE),
      { wrapper, initialProps: FIRST_READ },
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Hold the second answer, so the moment between the question and its answer
    // can be read rather than skipped over. A stub that answers at once never
    // shows this state, which is why it was shipped.
    let release: (() => void) | undefined
    stubs.fetchStub.mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          release = () => resolve(json({ items: [], total: 0, total_all: 1 }))
        }),
    )

    rerender({ search: 'zzz', sort: 'newest' })
    await waitFor(() => expect(result.current.isPlaceholderData).toBe(true))

    // The entries on screen are the previous phrase's, and so is the question
    // travelling with them. A screen reading the phrase from the address and the
    // counts from here would say "0 matches for “zzz”" over Anna's entry.
    expect(result.current.data?.entries).toEqual(PAGE.items)
    expect(result.current.data?.answering).toEqual(FIRST_READ)

    release?.()
    await waitFor(() => expect(result.current.isPlaceholderData).toBe(false))
    expect(result.current.data?.answering).toEqual({ search: 'zzz', sort: 'newest' })
    expect(result.current.data?.entries).toEqual([])
  })

  it('puts the sort and the piece size on the query string, and the phrase only when there is one', async () => {
    const { wrapper } = harness()

    const { result, rerender } = renderHook(
      (query: Parameters<typeof useGuestbookEntries>[0]) =>
        useGuestbookEntries(query, FIRST_PIECE),
      { wrapper, initialProps: FIRST_READ },
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const empty = new URL(sent().url).searchParams
    expect(empty.get('sort')).toBe('newest')
    expect(empty.get('limit')).toBe('4')
    // Absent, not empty: `q=` and no `q` mean the same thing to the server, and
    // sending the empty one puts a parameter in every request that says nothing.
    expect(empty.has('q')).toBe(false)

    // Absent at its default too: the first piece starts at the beginning, and
    // `offset=0` in every request says nothing the endpoint does not assume.
    expect(empty.has('offset')).toBe(false)

    rerender({ search: 'anna', sort: 'oldest' })
    await waitFor(() => expect(new URL(sent().url).searchParams.get('q')).toBe('anna'))

    expect(new URL(sent().url).searchParams.get('sort')).toBe('oldest')
  })

  it('asks for the next piece by offset, never by a bigger ceiling [req:CR-2609-9b1e/R-7]', async () => {
    const book = Array.from({ length: 9 }, (_, index) => ({ ...ENTRY, id: `id-${index}` }))
    stubs.fetchStub.mockImplementation((request: Request) => {
      const asked = new URL(request.url).searchParams
      const offset = Number(asked.get('offset') ?? '0')
      const limit = Number(asked.get('limit') ?? '20')
      return Promise.resolve(
        json({ items: book.slice(offset, offset + limit), total: book.length, total_all: book.length }),
      )
    })
    const { wrapper } = harness()

    // The address says eight are on screen, so the hook restores eight -- the
    // first piece as far as one request may carry it, then the rest.
    const { result } = renderHook(
      () => useGuestbookEntries(FIRST_READ, { shown: 8, step: 4 }),
      { wrapper },
    )
    await waitFor(() => expect(result.current.data?.entries).toHaveLength(8))

    // Each entry exactly once, which is what an offset over a total order buys
    // and what the old growing window could not deliver past the ceiling.
    expect(result.current.data?.entries.map((entry) => entry.id)).toEqual(
      book.slice(0, 8).map((entry) => entry.id),
    )
    expect(result.current.hasNextPage).toBe(true)

    await waitFor(() => expect(result.current.data?.entries).toHaveLength(8))
    await result.current.fetchNextPage()
    await waitFor(() => expect(result.current.hasNextPage).toBe(false))
    expect(result.current.data?.entries).toHaveLength(9)
  })

  it('surfaces a refusal as an error rather than as an empty page', async () => {
    stubs.fetchStub.mockImplementation(() =>
      Promise.resolve(json({ detail: { code: 'boom', message: 'no' } }, 500)),
    )
    const { wrapper } = harness()

    const { result } = renderHook(() => useGuestbookEntries(FIRST_READ, FIRST_PIECE), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))

    // An empty page and a failed read look identical on screen, and only one of
    // them should say "No entries yet. Be the first."
    expect(result.current.error).toBeInstanceOf(ApiError)
    expect(result.current.data).toBeUndefined()
  })
})

describe('every mutation refreshes what the screen shows', () => {
  it('invalidates the resource after a create', async () => {
    stubs.fetchStub.mockImplementation((request: Request) =>
      Promise.resolve(request.method === 'POST' ? json(ENTRY, 201) : json(PAGE)),
    )
    const { wrapper, invalidated } = harness()

    const { result } = renderHook(() => useCreateGuestbookEntry(), { wrapper })
    result.current.mutate({ author: 'Anna', message: 'Hello there' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidated).toContainEqual([...guestbookEntryKeys.all])
  })

  it('invalidates the resource after an edit, and sends PATCH to the entry', async () => {
    stubs.fetchStub.mockImplementation(() => Promise.resolve(json(ENTRY)))
    const { wrapper, invalidated } = harness()

    const { result } = renderHook(() => useUpdateGuestbookEntry(), { wrapper })
    result.current.mutate({ id: ENTRY.id, body: { message: 'corrected' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(sent().method).toBe('PATCH')
    expect(new URL(sent().url).pathname).toBe(`/api/guestbook-entries/${ENTRY.id}`)
    expect(invalidated).toContainEqual([...guestbookEntryKeys.all])
  })

  it('invalidates the resource after a delete', async () => {
    const { wrapper, invalidated } = harness()

    const { result } = renderHook(() => useDeleteGuestbookEntry(), { wrapper })
    result.current.mutate(ENTRY.id)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidated).toContainEqual([...guestbookEntryKeys.all])
  })

  it('does not invalidate anything when a write fails', async () => {
    stubs.fetchStub.mockImplementation(() =>
      Promise.resolve(json({ detail: { code: 'x', message: 'no' } }, 422)),
    )
    const { wrapper, invalidated } = harness()

    const { result } = renderHook(() => useCreateGuestbookEntry(), { wrapper })
    result.current.mutate({ author: '   ', message: 'x' })
    await waitFor(() => expect(result.current.isError).toBe(true))

    // Refetching after a refusal costs a round trip to learn nothing changed.
    expect(invalidated).toEqual([])
  })
})

describe('the delete that answers with no body', () => {
  it('resolves rather than failing on the missing body', async () => {
    const { wrapper } = harness()

    const { result } = renderHook(() => useDeleteGuestbookEntry(), { wrapper })
    result.current.mutate(ENTRY.id)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // `204` carries nothing at all. An implementation insisting on a body would
    // make every successful delete look like an error.
    expect(sent().method).toBe('DELETE')
    expect(result.current.data).toBeUndefined()
  })
})
