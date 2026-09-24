import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { RouterProvider } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'

import type { components } from '@/api/schema'
import { ToastProvider } from '@/components/ui/Toast'

/**
 * The composition root: which screen each address opens (`R-5`,
 * `spec/design/ui/system-states.md` § Interactions).
 *
 * The router under test is the application's own -- the `router` `main.tsx`
 * mounts -- driven to an address and rendered the way `main.tsx` renders it,
 * inside the query client and the toasts. A routing table rebuilt in the test
 * would prove a copy of it.
 *
 * The addresses are written out rather than read from `routes.ts`, and that is
 * the point: `/todo-list` and `/guestbook` are what a person types, bookmarks and
 * shares, fixed by `spec/design/ui/todo-list.md` (`route: /todo-list`) and by
 * `system-states.md`. A test that read the constant would follow it anywhere.
 *
 * "Opens the guestbook at the main address" is green on its first run, on
 * purpose: the redirect already stands, and until this file only the UI smoke
 * asserted it -- which cites no requirement, so nothing that counts held the
 * system to `R-5` clause 3 (`spec/design/testing.md` § CR-2609-823a, "Green by
 * design").
 *
 * This file sits beside the composition root, outside every context folder, so it
 * imports no context module (`tests/fitness/test_context_boundaries.py`): the
 * task is aliased from the generated contract, and the screens are reached
 * through the router.
 */

type TodoTask = components['schemas']['TodoTaskRead']

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
 * Reaches the composition root when the test runs, so a screen it binds that
 * fails to load mid-implementation fails the tests that open it rather than
 * un-collecting this file. A value rather than a literal specifier, because under
 * jsdom Vite resolves a literal `import()` while transforming the file.
 */
function reach<T>(path: string): Promise<T> {
  return import(/* @vite-ignore */ path) as Promise<T>
}

const WATER: TodoTask = {
  id: '00000000-0000-4000-8000-000000000001',
  text: 'Water the plants',
  done: false,
  created_at: '2026-09-24T09:00:00Z',
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

beforeEach(() => {
  stubs.fetchStub.mockReset()
  stubs.fetchStub.mockImplementation((request: Request) => {
    const path = new URL(request.url).pathname
    if (path === '/api/todo-tasks') return Promise.resolve(json({ items: [WATER], total: 1 }))
    if (path === '/api/guestbook-entries') {
      return Promise.resolve(json({ items: [], total: 0, total_all: 0 }))
    }
    return Promise.resolve(json({ detail: 'Not Found' }, 404))
  })
})

/** The application's router, at `address`, rendered as `main.tsx` renders it. */
async function open(address: string) {
  const { router } = await reach<typeof import('@/router')>('@/router')
  await router.navigate(address)
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </QueryClientProvider>,
  )
  return router
}

it('opens the to-do list at its own address [req:CR-2609-823a/R-5]', async () => {
  const router = await open('/todo-list')

  // The to-do list itself -- its title, its sentence and its list, read from the
  // service -- and not a redirect somewhere else or the page for a wrong address.
  expect(await screen.findByRole('heading', { name: 'Things to do' })).toBeInTheDocument()
  expect(
    screen.getByText(
      'No account, no sign-in, one list for everybody. Add what needs doing and tick it off when it is done. Anyone can edit or delete any task.',
    ),
  ).toBeInTheDocument()
  expect(await screen.findByRole('checkbox', { name: 'Water the plants' })).toBeInTheDocument()
  expect(screen.getByText('Tasks are public and editable by anyone with this link.')).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Nothing here' })).not.toBeInTheDocument()
  expect(router.state.location.pathname).toBe('/todo-list')
})

it('opens the guestbook at the main address [req:CR-2609-823a/R-5]', async () => {
  const router = await open('/')

  // The main address stays the guestbook's (`Q-5`): one screen at one address,
  // reached from `/` by a redirect rather than rendered at two.
  await waitFor(() => expect(router.state.location.pathname).toBe('/guestbook'))
  expect(await screen.findByRole('heading', { name: 'Leave a note' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Things to do' })).not.toBeInTheDocument()
})

it('answers an unknown address with the page that says nothing is there [req:CR-2609-823a/R-5]', async () => {
  const router = await open('/no-such-page')

  expect(await screen.findByRole('heading', { name: 'Nothing here' })).toBeInTheDocument()
  expect(screen.getByText('There is nothing at this address.')).toBeInTheDocument()
  // Not moved somewhere else: the address the person typed stays in the bar.
  expect(router.state.location.pathname).toBe('/no-such-page')
})
