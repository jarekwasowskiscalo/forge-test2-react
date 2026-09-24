import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'

import type { components } from '@/api/schema'
import { ToastProvider } from '@/components/ui/Toast'

import type { TodoTask } from '../lib/todoTask'

type TodoTaskCreate = components['schemas']['TodoTaskCreate']
type TodoTaskUpdate = components['schemas']['TodoTaskUpdate']

/**
 * The screen's behaviour, not its markup.
 *
 * Each part is proved where it is defined -- the rule in `lib/todoTask.test.ts`,
 * the field in `TodoTaskComposer.test.tsx`, a row in `TodoTaskRow.test.tsx`, the
 * cache in `useTodoTasks.test.tsx`. What is left is what exists only when they are
 * put together on one screen:
 *
 * - **an added task appears first, without a reload**, because the list is read
 *   again and the order is the answer's (`R-1`);
 * - **the order is the order the tasks arrive in**, never sorted again (`BR-11`);
 * - **empty, loading, failed and full are four different screens**, and the two
 *   that are easy to confuse -- a list with nothing in it and a list that could
 *   not be read; a list with nothing left to do and a list with no tasks -- are
 *   told apart (`R-3` clause 6, `R-10` clause 3);
 * - **a change that did not go through says so, in the words the person agreed**
 *   (`spec/design/ui/todo-list.md` § Copy, `Q-15`), **and is not shown as made**
 *   (`R-10`). "Could not be reached" when nothing answered at all; "answered with
 *   an error" when an answer came that carries no sentence of its own -- the
 *   service's real 500 body carries `detail: "internal server error"`, which is
 *   not a sentence for a person, and the screen must not print it as one; the
 *   refusal's own `message` when there is one.
 *
 * The network is stubbed at `fetch`, not at the hook, so the page's use of the
 * hook is what is tested. The stand-in server keeps the list in memory and answers
 * the way the contract says (`spec/design/api.md` § The to-do list's endpoints).
 * Every string is quoted from `spec/design/ui/todo-list.md` § Copy; the data is
 * synthetic and written here.
 */

/**
 * `Request` and `fetch`, stubbed before the module graph is imported -- the
 * reasons are the guestbook page test's: `openapi-fetch` captures
 * `globalThis.fetch` when `api/client.ts` is first imported, and undici's
 * `Request` refuses the origin-less `/api/...` path the client builds.
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

const EMPTY_LIST = 'No tasks yet. Add the first one above.'
const LOAD_FAILED = 'The tasks could not be loaded.'
const ADD_UNREACHABLE = 'The task was not added: the service could not be reached.'
const ADD_ERROR = 'The task was not added: the service answered with an error.'
const CHANGE_UNREACHABLE = 'The change was not made: the service could not be reached.'
const CHANGE_ERROR = 'The change was not made: the service answered with an error.'
/** The refusal's own sentence, as `spec/design/api.md` § The to-do list's refusals words it. */
const GONE = 'This task no longer exists. Somebody may have deleted it, and nothing was changed.'

function task(id: number, text: string, done = false, createdAt = `2026-09-24T09:0${id}:00Z`): TodoTask {
  return { id: `00000000-0000-4000-8000-${String(id).padStart(12, '0')}`, text, done, created_at: createdAt }
}

function json(body: unknown, status = 200): Response {
  return status === 204
    ? new Response(null, { status })
    : new Response(JSON.stringify(body), {
        status,
        headers: { 'content-type': 'application/json' },
      })
}

type Answer = (request: Request) => Promise<Response>

/** Nothing answered at all -- what `fetch` does on a dead connection. */
const unreachable: Answer = () => Promise.reject(new TypeError('Failed to fetch'))
/** The body the service really sends on an unhandled failure (`app/core/errors.py`). */
const serverError: Answer = () => Promise.resolve(json({ detail: 'internal server error' }, 500))

/**
 * A stand-in for the to-do list's four routes over a list in memory, newest first.
 *
 * A write can be answered otherwise -- a failure, a refusal -- by queueing an
 * answer for its method; the next write of that method takes it, and the list is
 * left as it was, which is what a write that did not go through does.
 */
function serve(initial: TodoTask[]) {
  const server = {
    tasks: [...initial],
    next: { POST: [] as Answer[], PATCH: [] as Answer[], DELETE: [] as Answer[] },
    list: undefined as Answer | undefined,
  }
  let added = 0
  stubs.fetchStub.mockImplementation(async (request: Request) => {
    const path = new URL(request.url).pathname
    const method = request.method
    if (method === 'GET' && path === '/api/todo-tasks') {
      if (server.list !== undefined) return server.list(request)
      return json({ items: server.tasks, total: server.tasks.length })
    }
    if (method !== 'POST' && method !== 'PATCH' && method !== 'DELETE') return json({ detail: 'Not Found' }, 404)
    const queued = server.next[method].shift()
    if (queued !== undefined) return queued(request)

    const raw = await request.clone().text()
    if (method === 'POST') {
      const body = JSON.parse(raw) as TodoTaskCreate
      added += 1
      const created = task(50 + added, body.text, false, `2026-09-24T12:0${added}:00Z`)
      server.tasks = [created, ...server.tasks]
      return json(created, 201)
    }
    const id = path.split('/').at(-1)
    const found = server.tasks.find((each) => each.id === id)
    if (found === undefined) {
      return json({ detail: { code: 'todo_task_not_found', message: GONE, id } }, 404)
    }
    if (method === 'PATCH') {
      // A field that is absent or null is left alone (`spec/design/api.md` § `TodoTaskUpdate`).
      const body = (raw === '' ? {} : JSON.parse(raw)) as TodoTaskUpdate
      const changed: TodoTask = { ...found, text: body.text ?? found.text, done: body.done ?? found.done }
      server.tasks = server.tasks.map((each) => (each.id === id ? changed : each))
      return json(changed)
    }
    server.tasks = server.tasks.filter((each) => each.id !== id)
    return json(null, 204)
  })
  return server
}

async function openScreen() {
  const { TodoListPage } = await reach<typeof import('./TodoListPage')>('./TodoListPage')
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <MemoryRouter initialEntries={['/todo-list']}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <TodoListPage />
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
  return userEvent.setup()
}

const newTaskField = () => screen.getByRole('textbox', { name: 'New task' })
const box = (text: string) => screen.getByRole('checkbox', { name: text })

/** Asserts the rows on screen are exactly these, top to bottom. */
function expectRows(texts: string[]) {
  const boxes = screen.getAllByRole('checkbox')
  expect(boxes).toHaveLength(texts.length)
  expect(texts.map((text) => boxes.indexOf(box(text)))).toEqual(texts.map((_, index) => index))
}

beforeEach(() => {
  stubs.fetchStub.mockReset()
})

it('shows an added task first without a reload [req:CR-2609-823a/R-1]', async () => {
  serve([task(2, 'Second'), task(1, 'First')])
  const user = await openScreen()
  await screen.findByRole('checkbox', { name: 'Second' })

  await user.type(newTaskField(), 'Third')
  await user.click(screen.getByRole('button', { name: 'Add task' }))

  // First, on the screen already open: the list was read again, not reloaded.
  await waitFor(() => expectRows(['Third', 'Second', 'First']))
  expect(box('Third')).not.toBeChecked()
  expect(await screen.findByText('Task added.')).toBeInTheDocument()
  expect(screen.getByText('3 tasks')).toBeInTheDocument()
  // The field is emptied for the next one.
  expect(newTaskField()).toHaveValue('')
})

it('shows the tasks in the order they arrive [req:CR-2609-823a/R-3]', async () => {
  // Deliberately in no order a screen could compute: neither newest first by
  // `created_at` nor alphabetical. The order is the answer's (`BR-11`) -- the
  // service settles ties and directions, and a screen that sorts again can only
  // disagree with it.
  serve([
    task(1, 'Gamma', false, '2026-09-20T09:00:00Z'),
    task(2, 'Alpha', true, '2026-09-24T09:00:00Z'),
    task(3, 'Beta', false, '2026-09-22T09:00:00Z'),
  ])
  await openScreen()
  await screen.findByRole('checkbox', { name: 'Gamma' })

  expectRows(['Gamma', 'Alpha', 'Beta'])
  expect(screen.getByText('3 tasks')).toBeInTheDocument()
})

it('says the list is empty and how to begin, with no error [req:CR-2609-823a/R-3]', async () => {
  const server = serve([])
  let release: () => void = () => undefined
  server.list = () =>
    new Promise<Response>((resolve) => {
      release = () => resolve(json({ items: [], total: 0 }))
    })
  await openScreen()

  // While the list is read: outline rows read aloud as loading, no count, and not
  // the empty sentence -- a list nobody has read yet is not a list with nothing in
  // it. The add field is usable meanwhile.
  expect(await screen.findByRole('status', { name: 'Loading tasks' })).toBeInTheDocument()
  expect(screen.queryByText(EMPTY_LIST)).not.toBeInTheDocument()
  expect(screen.queryByText(/^\d+ tasks?$/)).not.toBeInTheDocument()
  expect(newTaskField()).toBeEnabled()

  await waitFor(() => expect(stubs.fetchStub).toHaveBeenCalled())
  release()

  // The screen's first week: a sentence saying what to do, and nothing that reads
  // as an error.
  expect(await screen.findByText(EMPTY_LIST)).toBeInTheDocument()
  expect(screen.getByText('0 tasks')).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(screen.queryByText(LOAD_FAILED)).not.toBeInTheDocument()
  expect(screen.queryByRole('status', { name: 'Loading tasks' })).not.toBeInTheDocument()
  // Where to begin is right there: the field and its button.
  expect(newTaskField()).toHaveAttribute('placeholder', 'What needs doing?')
  expect(screen.getByRole('button', { name: 'Add task' })).toBeInTheDocument()
})

it('shows a list whose tasks are all done and does not call it empty [req:CR-2609-823a/R-3]', async () => {
  serve([task(2, 'Water the plants', true), task(1, 'Buy bread', true)])
  await openScreen()
  await screen.findByRole('checkbox', { name: 'Water the plants' })

  // Nothing left to do is not no tasks: the done ones are shown, ticked.
  expectRows(['Water the plants', 'Buy bread'])
  expect(box('Water the plants')).toBeChecked()
  expect(box('Buy bread')).toBeChecked()
  expect(screen.getByText('2 tasks')).toBeInTheDocument()
  expect(screen.queryByText(EMPTY_LIST)).not.toBeInTheDocument()
})

it('says a marking that did not go through was not made [req:CR-2609-823a/R-10]', async () => {
  const server = serve([task(1, 'Buy bread')])
  server.next.PATCH.push(unreachable, serverError)
  const user = await openScreen()
  await screen.findByRole('checkbox', { name: 'Buy bread' })

  // Nothing answered.
  await user.click(box('Buy bread'))
  expect(await screen.findByText(CHANGE_UNREACHABLE)).toBeInTheDocument()
  await waitFor(() => expect(box('Buy bread')).toBeEnabled())
  expect(box('Buy bread')).not.toBeChecked()

  // An answer with no sentence of its own.
  await user.click(box('Buy bread'))
  expect(await screen.findByText(CHANGE_ERROR)).toBeInTheDocument()
  await waitFor(() => expect(box('Buy bread')).toBeEnabled())
  expect(box('Buy bread')).not.toBeChecked()
  // The service's own words for a 500 are not a sentence for a person.
  expect(screen.queryByText(/internal server error/i)).not.toBeInTheDocument()
})

it('says a task that did not go through was not added [req:CR-2609-823a/R-10]', async () => {
  const server = serve([])
  server.next.POST.push(unreachable, serverError)
  const user = await openScreen()
  await screen.findByText(EMPTY_LIST)

  await user.type(newTaskField(), 'Water the plants')
  await user.click(screen.getByRole('button', { name: 'Add task' }))

  expect(await screen.findByText(ADD_UNREACHABLE)).toBeInTheDocument()
  // No row appears, the list is still the empty one, and the text stays in the
  // field so it can be sent again.
  await waitFor(() => expect(newTaskField()).toBeEnabled())
  expect(screen.queryByRole('checkbox', { name: 'Water the plants' })).not.toBeInTheDocument()
  expect(screen.getByText(EMPTY_LIST)).toBeInTheDocument()
  expect(newTaskField()).toHaveValue('Water the plants')

  await user.click(screen.getByRole('button', { name: 'Add task' }))

  expect(await screen.findByText(ADD_ERROR)).toBeInTheDocument()
  await waitFor(() => expect(newTaskField()).toBeEnabled())
  expect(screen.queryByRole('checkbox', { name: 'Water the plants' })).not.toBeInTheDocument()
  expect(screen.queryByText(/internal server error/i)).not.toBeInTheDocument()
  expect(screen.queryByText('Task added.')).not.toBeInTheDocument()
})

it('says a correction or a deletion that did not go through was not made [req:CR-2609-823a/R-10]', async () => {
  const server = serve([task(1, 'Buy bread')])
  server.next.PATCH.push(unreachable)
  server.next.DELETE.push(serverError)
  const user = await openScreen()
  await screen.findByRole('checkbox', { name: 'Buy bread' })

  // A correction nothing answered: said so, the editor stays open with what was
  // typed, and the stored text is unchanged -- "Cancel" brings it back.
  await user.click(screen.getByRole('button', { name: 'Edit “Buy bread”' }))
  const field = screen.getByRole('textbox', { name: 'Edit task' })
  await user.clear(field)
  await user.type(field, 'Buy rye bread')
  await user.click(screen.getByRole('button', { name: 'Save' }))

  expect(await screen.findByText(CHANGE_UNREACHABLE)).toBeInTheDocument()
  await waitFor(() => expect(screen.getByRole('textbox', { name: 'Edit task' })).toBeEnabled())
  expect(screen.getByRole('textbox', { name: 'Edit task' })).toHaveValue('Buy rye bread')
  expect(screen.queryByText('Task updated.')).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(box('Buy bread')).toBeInTheDocument()
  expect(screen.queryByText('Buy rye bread')).not.toBeInTheDocument()

  // A deletion answered with an error: the question closes, said so, and the task
  // is still on the list.
  await user.click(screen.getByRole('button', { name: 'Delete “Buy bread”' }))
  await user.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Delete task' }))

  expect(await screen.findByText(CHANGE_ERROR)).toBeInTheDocument()
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  expectRows(['Buy bread'])
  expect(screen.queryByText('Task deleted.')).not.toBeInTheDocument()
})

it('says the list failed to load, not that it is empty [req:CR-2609-823a/R-10]', async () => {
  const server = serve([task(1, 'Buy bread')])
  server.list = unreachable
  const user = await openScreen()

  // Its own sentence, above the shared error card, which names what went wrong
  // and offers to try again.
  expect(await screen.findByText(LOAD_FAILED)).toBeInTheDocument()
  const card = screen.getByText('Could not reach the service').closest<HTMLElement>('[role="alert"]')
  if (card === null) throw new Error('the error card is not announced as an alert')

  // Not the empty list: no empty sentence, and no count -- a list that could not
  // be read has no number, and "0 tasks" would be a claim about it.
  expect(screen.queryByText(EMPTY_LIST)).not.toBeInTheDocument()
  expect(screen.queryByText(/^\d+ tasks?$/)).not.toBeInTheDocument()
  expect(newTaskField()).toBeEnabled()

  // "Try again" reads the list again.
  server.list = undefined
  await user.click(within(card).getByRole('button', { name: 'Try again' }))
  expect(await screen.findByRole('checkbox', { name: 'Buy bread' })).toBeInTheDocument()
  expect(screen.queryByText(LOAD_FAILED)).not.toBeInTheDocument()
})

it('says a task refused as gone no longer exists and does not show it done [req:CR-2609-823a/R-10]', async () => {
  const server = serve([task(1, 'Buy bread')])
  // Somebody else deleted it after this screen read the list.
  server.next.PATCH.push((request) =>
    Promise.resolve(
      json(
        { detail: { code: 'todo_task_not_found', message: GONE, id: new URL(request.url).pathname.split('/').at(-1) } },
        404,
      ),
    ),
  )
  const user = await openScreen()
  await screen.findByRole('checkbox', { name: 'Buy bread' })

  await user.click(box('Buy bread'))

  // The refusal's own sentence, as the service words it -- a refusal is a change
  // that did not go through as much as a dead connection is.
  expect(await screen.findByText(GONE)).toBeInTheDocument()
  await waitFor(() => expect(box('Buy bread')).toBeEnabled())
  expect(box('Buy bread')).not.toBeChecked()
})
