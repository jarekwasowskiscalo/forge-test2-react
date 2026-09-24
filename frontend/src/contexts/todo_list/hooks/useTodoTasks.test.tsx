import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'

import type { components } from '@/api/schema'

import type { TodoTask } from '../lib/todoTask'

type TodoTaskCreate = components['schemas']['TodoTaskCreate']
type TodoTaskUpdate = components['schemas']['TodoTaskUpdate']

/**
 * The one place the screen's copy of the list is written, tested where neither
 * the page nor the wire can see it.
 *
 * Two promises live here and nowhere else (`spec/design/architecture.md` § The
 * to-do list -- where each rule lives):
 *
 * 1. **Nothing is written into the cached list ahead of the answer, and nothing
 *    after a failure** (`R-10`). An optimistic tick that is rolled back when the
 *    request fails is still a tick the person saw made, on the one list whose
 *    whole point is saying what is done -- so this test records every list the
 *    hook ever handed out, not only the last one.
 * 2. **A change that went through is followed by a fresh read** (`R-1`, and
 *    `spec/design/ui/todo-list.md` § Data: "the list is read again after every
 *    change that went through, which is also when other people's changes
 *    arrive"). The stand-in server below makes somebody else's change land at the
 *    same moment as each of ours, so only a read -- never the answer written into
 *    the cache by hand -- can show it.
 *
 * Stubbing follows `contexts/guestbook/hooks/useGuestbookEntries.test.tsx`:
 * `openapi-fetch` captures `globalThis.fetch` when `api/client.ts` is imported,
 * and undici's `Request` refuses an origin-less path, so both are replaced before
 * the module graph loads.
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

/**
 * Reaches the module the implementation wave writes, when the test runs.
 *
 * The specifier is a value rather than a literal, and that is load-bearing: under
 * jsdom Vite resolves a literal `import('./X')` while transforming this file, so a
 * module that does not exist yet failed the whole file at load time with no test
 * collected. A value is resolved when the import runs, and a missing module fails
 * the one test that reached for it. `typeof import(...)` keeps the module's types
 * and is erased before anything resolves it.
 */
function reach<T>(path: string): Promise<T> {
  return import(/* @vite-ignore */ path) as Promise<T>
}

type HooksModule = typeof import('./useTodoTasks')

function task(id: number, text: string, done = false): TodoTask {
  return {
    id: `00000000-0000-4000-8000-${String(id).padStart(12, '0')}`,
    text,
    done,
    created_at: `2026-09-24T09:0${id}:00Z`,
  }
}

const BREAD = task(1, 'Buy bread')

function json(body: unknown, status = 200): Response {
  return status === 204
    ? new Response(null, { status })
    : new Response(JSON.stringify(body), {
        status,
        headers: { 'content-type': 'application/json' },
      })
}

/** The body the service really sends on an unhandled failure (`app/core/errors.py`). */
const serverError = () => json({ detail: 'internal server error' }, 500)

/** What `fetch` does when nothing answers at all. */
const unreachable = () => new TypeError('Failed to fetch')

/** A client with retries off, so a failing test fails now rather than in a second. */
function wrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

/** A response the test hands over when it chooses, so the moment before the answer can be read. */
function held() {
  let resolve: (response: Response) => void = () => undefined
  let reject: (reason: unknown) => void = () => undefined
  const promise = new Promise<Response>((settle, fail) => {
    resolve = settle
    reject = fail
  })
  return { promise, resolve, reject }
}

/** Every hook of the module at once, as the page uses them. */
function renderAll(hooks: HooksModule, seen: TodoTask[][] = []) {
  return renderHook(
    () => {
      const list = hooks.useTodoTasks()
      if (list.data !== undefined) seen.push(list.data.items)
      return {
        list,
        add: hooks.useAddTodoTask(),
        mark: hooks.useMarkTodoTask(),
        correct: hooks.useCorrectTodoTask(),
        remove: hooks.useDeleteTodoTask(),
      }
    },
    { wrapper: wrapper() },
  )
}

beforeEach(() => {
  stubs.fetchStub.mockReset()
})

it('writes nothing into the list before the application answers [req:CR-2609-823a/R-10]', async () => {
  const hooks = await reach<HooksModule>('./useTodoTasks')
  let answer = held()
  let writesSent = 0
  stubs.fetchStub.mockImplementation((request: Request) => {
    if (request.method === 'GET') return Promise.resolve(json({ items: [BREAD], total: 1 }))
    writesSent += 1
    return answer.promise
  })
  const seen: TodoTask[][] = []
  const { result } = renderAll(hooks, seen)
  await waitFor(() => expect(result.current.list.isSuccess).toBe(true))

  // Each change held in flight, then failed: the list must read as stored the
  // whole time -- while the request travels, and after it came back refused.
  const changes = [
    {
      name: 'a tick',
      start: () => result.current.mark.mutate({ id: BREAD.id, done: true }),
      state: () => result.current.mark,
      fail: () => answer.reject(unreachable()),
    },
    {
      name: 'an add',
      start: () => result.current.add.mutate({ text: 'Water the plants' }),
      state: () => result.current.add,
      fail: () => answer.resolve(serverError()),
    },
    {
      name: 'a correction',
      start: () => result.current.correct.mutate({ id: BREAD.id, text: 'Buy rye bread' }),
      state: () => result.current.correct,
      fail: () => answer.reject(unreachable()),
    },
    {
      name: 'a deletion',
      start: () => result.current.remove.mutate(BREAD.id),
      state: () => result.current.remove,
      fail: () => answer.resolve(serverError()),
    },
  ]

  for (const [index, change] of changes.entries()) {
    answer = held()
    await act(() => change.start())
    await waitFor(() => expect(change.state().isPending, change.name).toBe(true))
    // On the wire, so the answer is failed while somebody is waiting for it.
    await waitFor(() => expect(writesSent, change.name).toBe(index + 1))

    expect(result.current.list.data?.items, `${change.name}, before the answer`).toEqual([BREAD])

    change.fail()
    await waitFor(() => expect(change.state().isError, change.name).toBe(true))

    expect(result.current.list.data?.items, `${change.name}, after it failed`).toEqual([BREAD])
  }

  // Not only the list at each checkpoint: every list the hook ever handed the
  // screen. A tick drawn and rolled back between two checkpoints is still a
  // change shown as made that never was.
  expect(seen.length).toBeGreaterThan(0)
  for (const items of seen) expect(items).toEqual([BREAD])
})

it('refetches the list after a change that went through [req:CR-2609-823a/R-1]', async () => {
  const hooks = await reach<HooksModule>('./useTodoTasks')

  // A stand-in for the service that also lets somebody else act at the moment
  // each of our changes lands. Only a fresh read can carry their change.
  let stored: TodoTask[] = [BREAD]
  let reads = 0
  const sent: { method: string; path: string; body: unknown }[] = []
  const elsewhere = task(5, 'Added by somebody else')

  stubs.fetchStub.mockImplementation(async (request: Request) => {
    const path = new URL(request.url).pathname
    const raw = await request.clone().text()
    const body: unknown = raw === '' ? undefined : JSON.parse(raw)
    if (request.method === 'GET') {
      reads += 1
      return json({ items: stored, total: stored.length })
    }
    sent.push({ method: request.method, path, body })
    const id = path.split('/').at(-1)
    if (request.method === 'POST') {
      const added = { ...task(9, (body as TodoTaskCreate).text), created_at: '2026-09-24T10:00:00Z' }
      stored = [added, elsewhere, ...stored]
      return json(added, 201)
    }
    if (request.method === 'PATCH') {
      stored = stored.map((each) => {
        if (each.id === id) {
          const change = body as TodoTaskUpdate
          return { ...each, text: change.text ?? each.text, done: change.done ?? each.done }
        }
        // Somebody else ticks their task at the same moment.
        if (each.id === elsewhere.id) return { ...each, done: !each.done }
        return each
      })
      return json(stored.find((each) => each.id === id))
    }
    stored = stored.filter((each) => each.id !== id)
    return json(null, 204)
  })

  const { result } = renderAll(hooks)
  await waitFor(() => expect(result.current.list.isSuccess).toBe(true))
  const texts = () => result.current.list.data?.items.map((each) => each.text)

  // Adding.
  let before = reads
  await act(() => result.current.add.mutate({ text: 'Water the plants' }))
  await waitFor(() => expect(result.current.add.isSuccess).toBe(true))
  await waitFor(() => expect(texts()).toEqual(['Water the plants', 'Added by somebody else', 'Buy bread']))
  expect(reads).toBeGreaterThan(before)

  // Ticking.
  before = reads
  await act(() => result.current.mark.mutate({ id: BREAD.id, done: true }))
  await waitFor(() => expect(result.current.mark.isSuccess).toBe(true))
  await waitFor(() =>
    expect(result.current.list.data?.items.map((each) => [each.text, each.done])).toEqual([
      ['Water the plants', false],
      ['Added by somebody else', true],
      ['Buy bread', true],
    ]),
  )
  expect(reads).toBeGreaterThan(before)

  // Correcting.
  before = reads
  await act(() => result.current.correct.mutate({ id: BREAD.id, text: 'Buy rye bread' }))
  await waitFor(() => expect(result.current.correct.isSuccess).toBe(true))
  await waitFor(() => expect(texts()).toEqual(['Water the plants', 'Added by somebody else', 'Buy rye bread']))
  expect(result.current.list.data?.items.find((each) => each.id === elsewhere.id)?.done).toBe(false)
  expect(reads).toBeGreaterThan(before)

  // Deleting, which answers 204 with no body -- and still goes through.
  before = reads
  await act(() => result.current.remove.mutate(BREAD.id))
  await waitFor(() => expect(result.current.remove.isSuccess).toBe(true))
  await waitFor(() => expect(texts()).toEqual(['Water the plants', 'Added by somebody else']))
  expect(reads).toBeGreaterThan(before)

  // And what each change put on the wire is the contract's: a tick carries `done`
  // alone and a correction `text` alone, so neither writes back a field somebody
  // else may be changing at that moment (`spec/design/api.md` § `TodoTaskUpdate`).
  expect(sent).toEqual([
    { method: 'POST', path: '/api/todo-tasks', body: { text: 'Water the plants' } },
    { method: 'PATCH', path: `/api/todo-tasks/${BREAD.id}`, body: { done: true } },
    { method: 'PATCH', path: `/api/todo-tasks/${BREAD.id}`, body: { text: 'Buy rye bread' } },
    { method: 'DELETE', path: `/api/todo-tasks/${BREAD.id}`, body: undefined },
  ])
})
