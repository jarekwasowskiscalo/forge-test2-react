import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ToastProvider } from '@/components/ui/Toast'
import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

import { GuestbookPage } from './GuestbookPage'

/**
 * The screen's behaviour, not its markup.
 *
 * What is asserted here is only what lives **between** the parts, because each
 * part is tested where it is defined: the composer's rules in
 * `EntryComposer.test.tsx`, the card's editor in `EntryCard.test.tsx`, the
 * counts in `entryListCopy.test.ts`. That leaves four decisions that exist
 * nowhere else and each of which could plausibly have gone the other way:
 *
 * 1. Typing in the search box narrows the *server's* answer, after a pause --
 *    not the array already on screen.
 * 2. Narrowing or reordering resets the page size, so twelve loaded entries do
 *    not become twelve results for a phrase matching two.
 * 3. "Load more" appends the next piece by `offset`, and the address says how
 *    many are on screen. The ceiling on one request is a hundred, so a growing
 *    window stops at the hundredth entry and the rest of the guestbook becomes
 *    unreachable; what keeps the pieces from duplicating or dropping an entry is
 *    invalidating the whole query after a write, not asking for one big window.
 * 4. An edit is opened in one card at a time, and deleting goes through the
 *    dialog. A save in flight belongs to the entry it was sent for, and nothing
 *    that happens afterwards may reassign it.
 * 5. The question lives in the address, so a result can be linked to and
 *    survives a reload -- the destination `spec/design/conventions.md` § Frontend
 *    named for filters and paging before either existed. The address is also
 *    what the screen follows: a navigation reseeds the search box, never the
 *    other way round.
 * 6. What the list says about itself belongs to the answer on screen, not to the
 *    phrase in the address -- they are different things while one is travelling.
 *
 * The network is stubbed at `fetch`, not at the hooks: stubbing the hooks would
 * leave the page's use of them -- the key, the invalidation, the pending flag --
 * untested, which is the half most likely to be wrong.
 */

/**
 * `Request` and `fetch`, stubbed before the module graph is imported.
 *
 * `vi.hoisted` is load-bearing twice over. `openapi-fetch` captures
 * `globalThis.fetch` once, when `client.ts` calls `createClient()` at module
 * scope -- a stub installed in `beforeEach` would never be seen. And undici's
 * `Request` (the global on Node 24, which jsdom does not replace) refuses to
 * parse an origin-less `/api/...` path: the client sets no `baseUrl` on
 * purpose, so every request it builds is relative and would throw
 * "Failed to parse URL" before any stub of `fetch` was reached.
 */
const stubs = vi.hoisted(() => {
  const RealRequest = globalThis.Request

  function RequestWithBase(input: RequestInfo | URL, init?: RequestInit): Request {
    const absoluteInput =
      typeof input === 'string' && input.startsWith('/') ? `http://localhost${input}` : input
    return new RealRequest(absoluteInput, init)
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

/** Nine entries, newest first, so a page of four leaves five behind. */
const BOOK: GuestbookEntry[] = Array.from({ length: 9 }, (_, index) => ({
  id: `${index}1111111-1111-4111-8111-111111111111`,
  author: index === 0 ? 'Anna' : `Guest ${index}`,
  message: index === 0 ? 'The first message' : `Message ${index}`,
  created_at: `2026-08-${30 - index}T20:00:00Z`,
  updated_at: `2026-08-${30 - index}T20:00:00Z`,
}))

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

/**
 * A stand-in for the endpoint: it really reads `q`, `sort`, `limit` and `offset`.
 *
 * A stub that ignored the parameters and always answered the same page would
 * let every assertion below pass against a screen that never sent them -- which
 * is the failure these tests exist to catch. `offset` is read for the same
 * reason the screen now sends it: a stub that served every piece from the top
 * would hide a screen that had stopped moving through the book.
 */
function serveBook(book: GuestbookEntry[]) {
  return (request: Request): Response => {
    if (request.method !== 'GET') return new Response(null, { status: 204 })

    const params = new URL(request.url).searchParams
    const phrase = (params.get('q') ?? '').toLowerCase()
    const limit = Number(params.get('limit') ?? '20')
    const offset = Number(params.get('offset') ?? '0')

    const matching = book.filter(
      (entry) =>
        phrase === '' ||
        entry.author.toLowerCase().includes(phrase) ||
        entry.message.toLowerCase().includes(phrase),
    )
    const ordered = params.get('sort') === 'oldest' ? [...matching].reverse() : matching

    return json({
      items: ordered.slice(offset, offset + limit),
      total: matching.length,
      total_all: book.length,
    })
  }
}

const answerLikeTheServer = serveBook(BOOK)

/** Every `limit` the screen has asked for so far, in order. */
function limitsAsked(): number[] {
  return stubs.fetchStub.mock.calls
    .map((call) => new URL(call[0].url).searchParams.get('limit'))
    .filter((limit): limit is string => limit !== null)
    .map(Number)
}

/** Renders the current address into the tree, so a test can assert about it. */
function Address() {
  const { pathname, search } = useLocation()
  return <span data-testid="address">{`${pathname}${search}`}</span>
}

function renderPage(initialUrl = '/guestbook') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <GuestbookPage />
          <Address />
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

/** The address as it currently stands. */
function address(): string {
  return screen.getByTestId('address').textContent ?? ''
}

/** The signatures currently rendered as cards, top to bottom. */
function authorsOnScreen(): string[] {
  return screen.getAllByRole('article').map((card) => {
    const heading = card.querySelector('span')
    return heading?.textContent ?? ''
  })
}

beforeEach(() => {
  stubs.fetchStub.mockReset()
  stubs.fetchStub.mockImplementation((request: Request) =>
    Promise.resolve(answerLikeTheServer(request)),
  )
})

describe('what the screen shows first', () => {
  it('opens on one page of the newest entries and says how big the book is', async () => {
    renderPage()

    await screen.findByText('The first message')

    expect(authorsOnScreen()).toEqual(['Anna', 'Guest 1', 'Guest 2', 'Guest 3'])
    // The header counts the book; the result line counts what is on screen.
    // They are different numbers here on purpose -- a screen deriving either
    // from the other would show four in both places.
    expect(screen.getByText('9 entries')).toBeInTheDocument()
    expect(screen.getByText('Showing 4 of 9')).toBeInTheDocument()
  })

  it('does not re-order what the server sent [req:CR-2609-9b1e/R-3]', async () => {
    renderPage()
    await screen.findByText('The first message')

    // `BR-04` is the server's, and a list that sorts what it was handed can
    // disagree with the paging the server did -- and then an entry appears twice.
    const requested = new URL(stubs.fetchStub.mock.calls[0]![0].url).searchParams
    expect(requested.get('sort')).toBe('newest')
    expect(authorsOnScreen()).toEqual(['Anna', 'Guest 1', 'Guest 2', 'Guest 3'])
  })
})

describe('searching', () => {
  it('asks the server for the phrase rather than filtering what is on screen', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'anna')

    // "Anna" is on the first page, so a screen filtering its own array would
    // pass this. The request is what proves it did not.
    await waitFor(() => {
      const last = stubs.fetchStub.mock.calls.at(-1)![0]
      expect(new URL(last.url).searchParams.get('q')).toBe('anna')
    })
    await screen.findByText('1 match for “anna”')
  })

  it('finds an entry that was never on the first page', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')
    expect(screen.queryByText('Message 8')).not.toBeInTheDocument()

    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'Message 8')

    await screen.findByText('Message 8')
  })

  it('says nothing matches, not that the book is empty', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'zzz')

    // "Be the first" in front of a book of nine reads as the application
    // having lost them.
    await screen.findByText('Nothing matches that search.')
    expect(screen.queryByText('No entries yet. Be the first.')).not.toBeInTheDocument()
  })
})

describe('reordering', () => {
  it('asks the server for the other end of the book [req:CR-2609-9b1e/R-3]', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    await user.click(screen.getByRole('button', { name: 'Oldest' }))

    await waitFor(() => expect(authorsOnScreen()[0]).toBe('Guest 8'))
    const last = stubs.fetchStub.mock.calls.at(-1)![0]
    expect(new URL(last.url).searchParams.get('sort')).toBe('oldest')
  })
})

describe('loading more', () => {
  it('offers only what is actually left, and stops offering at the end', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    // Nine entries, four shown: four more, then one.
    await user.click(screen.getByRole('button', { name: 'Load 4 more' }))
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(8))

    await user.click(await screen.findByRole('button', { name: 'Load 1 more' }))
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(9))

    expect(screen.queryByRole('button', { name: /Load/ })).not.toBeInTheDocument()
    expect(screen.getByText('Showing 9 of 9')).toBeInTheDocument()
  })

  it('appends the next piece by offset [req:CR-2609-9b1e/R-7]', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    await user.click(screen.getByRole('button', { name: 'Load 4 more' }))

    // `offset=4`, not `limit=8`. The window that grew from the start was chosen
    // to make duplication impossible while somebody posts, and it did -- right
    // up to the hundredth entry, where the contract's ceiling stopped it and
    // took the rest of the guestbook with it. Invalidating the whole query
    // after a write buys the same property over a total order, at every size.
    await waitFor(() => {
      const last = new URL(stubs.fetchStub.mock.calls.at(-1)![0].url).searchParams
      expect(last.get('offset')).toBe('4')
      expect(last.get('limit')).toBe('4')
    })

    // Each entry exactly once across the two pieces.
    expect(authorsOnScreen()).toEqual([
      'Anna',
      'Guest 1',
      'Guest 2',
      'Guest 3',
      'Guest 4',
      'Guest 5',
      'Guest 6',
      'Guest 7',
    ])
  })

  it('neither duplicates nor loses an entry when the book changes underneath [req:CR-2609-9b1e/R-7]', async () => {
    // Several pieces on screen, then a write: the danger the growing window was
    // chosen to avoid, met here by replaying every piece over the new order.
    const shrinking = [...BOOK]
    stubs.fetchStub.mockImplementation((request: Request) => {
      if (request.method === 'DELETE') {
        shrinking.splice(1, 1)
        return Promise.resolve(new Response(null, { status: 204 }))
      }
      return Promise.resolve(serveBook(shrinking)(request))
    })

    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')
    await user.click(screen.getByRole('button', { name: 'Load 4 more' }))
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(8))

    const doomed = screen.getByText('Message 1').closest('article')
    await user.click(within(doomed as HTMLElement).getByRole('button', { name: 'Delete' }))
    await user.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Delete entry' }))

    await waitFor(() => expect(screen.queryByText('Message 1')).not.toBeInTheDocument())
    const remaining = authorsOnScreen()
    expect(new Set(remaining).size).toBe(remaining.length)
    expect(remaining).toEqual(['Anna', 'Guest 2', 'Guest 3', 'Guest 4', 'Guest 5', 'Guest 6', 'Guest 7', 'Guest 8'])
  })

  it('starts the page over when the list is narrowed', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')
    await user.click(screen.getByRole('button', { name: 'Load 4 more' }))
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(8))

    await user.click(screen.getByRole('button', { name: 'Oldest' }))

    // Otherwise eight loaded entries become eight results for a phrase matching
    // two -- and, the other way round, a narrow page reading as "that is all".
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(4))
  })
})

describe('past the ceiling on one request', () => {
  /**
   * A guestbook bigger than a single request may carry.
   *
   * A hundred and four, deliberately: the contract's ceiling is a hundred, and
   * the entries past it are the ones that used to be unreachable -- the address
   * went on counting, the request did not, and the button offered a piece it
   * could no longer fetch.
   */
  const LONG_BOOK: GuestbookEntry[] = Array.from({ length: 104 }, (_, index) => ({
    id: `${String(index).padStart(2, '0')}111111-1111-4111-8111-111111111111`,
    author: `Guest ${index}`,
    message: `Message ${index}`,
    created_at: `2026-08-30T20:00:00Z`,
    updated_at: `2026-08-30T20:00:00Z`,
  }))

  beforeEach(() => {
    stubs.fetchStub.mockImplementation((request: Request) =>
      Promise.resolve(serveBook(LONG_BOOK)(request)),
    )
  })

  it('reaches the last entry, each one exactly once [req:CR-2609-9b1e/R-7]', async () => {
    const user = userEvent.setup()
    // Straight to the ceiling, so the test is about the entries past it rather
    // than about twenty-five presses of a button.
    renderPage('/guestbook?shown=100')
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(100))

    await user.click(await screen.findByRole('button', { name: 'Load 4 more' }))

    await waitFor(() => expect(authorsOnScreen()).toHaveLength(104))
    const shown = authorsOnScreen()
    expect(new Set(shown).size).toBe(104)
    expect(shown.at(-1)).toBe('Guest 103')
  })

  it('takes the button away once nothing is left [req:CR-2609-9b1e/R-7]', async () => {
    renderPage('/guestbook?shown=104')

    await waitFor(() => expect(authorsOnScreen()).toHaveLength(104))
    // It used to stay for ever: `remaining` was computed against a list that
    // could not grow past a hundred, so the condition was permanently true.
    await waitFor(() => expect(screen.queryByRole('button', { name: /Load/ })).not.toBeInTheDocument())
    expect(screen.getByText('Showing 104 of 104')).toBeInTheDocument()
  })

  it('never asks for more than one request may carry [req:CR-2609-9b1e/R-7]', async () => {
    renderPage('/guestbook?shown=99999')

    await waitFor(() => expect(authorsOnScreen()).toHaveLength(104))
    // Passed through, an address somebody mistyped reaches the endpoint as a
    // `422` and the screen shows an error for a typo.
    expect(Math.max(...limitsAsked())).toBeLessThanOrEqual(100)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('restores the same range after a reload, from the address alone [req:CR-2609-9b1e/R-7]', async () => {
    const user = userEvent.setup()
    const first = renderPage('/guestbook?shown=100')
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(100))
    await user.click(await screen.findByRole('button', { name: 'Load 4 more' }))
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(104))

    // The press wrote the address, and the address is now the whole record of
    // how much is on screen.
    expect(address()).toBe('/guestbook?shown=104')
    first.unmount()

    // The same address, a fresh screen, a fresh cache: a link to a place in a
    // long guestbook that opened somewhere else would be a link worth nothing.
    renderPage('/guestbook?shown=104')
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(104))
    expect(authorsOnScreen().at(-1)).toBe('Guest 103')
  })

  it('starts the piece over when the question changes halfway down [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderPage('/guestbook?shown=100')
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(100))

    await user.click(screen.getByRole('button', { name: 'Oldest' }))

    // Not one entry of the old order may stay: a hundred loaded entries must not
    // become a hundred results for a question that was never asked of them.
    await waitFor(() => expect(authorsOnScreen()).toHaveLength(4))
    expect(address()).toBe('/guestbook?sort=oldest')
  })
})

describe('what the list says about itself', () => {
  it('attributes the count to the answer on screen, not to the phrase in the box [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    // The second answer is held, so the moment between the phrase and its
    // answer can be read. A stub answering at once never shows this state --
    // which is exactly why the screen shipped claiming the old count was the
    // new one.
    let release: (() => void) | undefined
    stubs.fetchStub.mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          release = () => resolve(json({ items: [], total: 0, total_all: 9 }))
        }),
    )

    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'zzz')
    await waitFor(() => expect(release).toBeDefined())

    // Before the answer: the entries are still the unfiltered ones, so the
    // sentence must not call them matches for "zzz" -- and the wait has to be
    // visible, which until now it was not at all.
    await waitFor(() => expect(screen.getByText(/updating/)).toBeInTheDocument())
    expect(screen.queryByText(/for \u201czzz\u201d/)).not.toBeInTheDocument()
    expect(screen.getByText('Showing 4 of 9 \u2014 updating\u2026')).toBeInTheDocument()
    expect(screen.getByText('Showing 4 of 9 \u2014 updating\u2026')).toHaveAttribute('aria-busy', 'true')

    // After the answer: the count and the list come from the same question.
    release?.()
    await screen.findByText('0 matches for \u201czzz\u201d')
    expect(screen.queryByRole('article')).not.toBeInTheDocument()
  })

  it('says the read failed instead of carrying the old numbers [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    stubs.fetchStub.mockImplementation(() => Promise.resolve(json({ detail: 'boom' }, 503)))
    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'zzz')

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    // The live region is what a reader who cannot see the error state gets.
    // Old counts there would tell them the search succeeded.
    await waitFor(() => expect(screen.getByText('The entries could not be loaded.')).toBeInTheDocument())
    expect(screen.queryByText(/Showing 4 of 9/)).not.toBeInTheDocument()
  })
})

describe('correcting and destroying', () => {
  it('opens the editor inside the entry that was chosen, and only that one', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    const annasCard = screen.getByText('The first message').closest('article')
    expect(annasCard).not.toBeNull()
    await user.click(within(annasCard as HTMLElement).getByRole('button', { name: 'Edit' }))

    expect(await screen.findByRole('textbox', { name: 'Edit name' })).toHaveValue('Anna')
    // One editor, not four: two cards open at once is a state nothing on this
    // screen could resolve.
    expect(screen.getAllByRole('textbox', { name: 'Edit message' })).toHaveLength(1)
  })

  it('leaves a save in flight attached to the entry that sent it [req:CR-2609-9b1e/R-4]', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    // Hold the PATCH. Everything this test is about happens while it is in the
    // air, and a mutation that resolves at once has no "while".
    let release: (() => void) | undefined
    stubs.fetchStub.mockImplementation((request: Request) => {
      if (request.method !== 'PATCH') return Promise.resolve(answerLikeTheServer(request))
      return new Promise<Response>((resolve) => {
        release = () => resolve(json({ ...BOOK[0]!, message: 'corrected' }))
      })
    })

    const annasCard = screen.getByText('The first message').closest('article')
    await user.click(within(annasCard as HTMLElement).getByRole('button', { name: 'Edit' }))
    await user.clear(screen.getByRole('textbox', { name: 'Edit message' }))
    await user.type(screen.getByRole('textbox', { name: 'Edit message' }), 'corrected')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    // The marker is on the entry whose PATCH is actually travelling.
    await screen.findByRole('button', { name: 'Saving\u2026' })

    // And no second editor may be opened over it: the answer to one save used
    // to close whichever editor happened to be open, so opening another entry
    // here lost the editing context of a save nobody had finished.
    const other = screen.getByText('Message 1').closest('article')
    expect(within(other as HTMLElement).getByRole('button', { name: 'Edit' })).toBeDisabled()

    release?.()
    await waitFor(() =>
      expect(screen.queryByRole('textbox', { name: 'Edit message' })).not.toBeInTheDocument(),
    )
    // Unlocked again the moment the save settles -- a lock that outlived its
    // operation would be the same defect wearing the opposite sign.
    await waitFor(() =>
      expect(
        within(screen.getByText('Message 1').closest('article') as HTMLElement).getByRole('button', {
          name: 'Edit',
        }),
      ).toBeEnabled(),
    )
  })

  it('quotes the entry in the delete confirmation', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    const annasCard = screen.getByText('The first message').closest('article')
    await user.click(within(annasCard as HTMLElement).getByRole('button', { name: 'Delete' }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Anna')).toBeInTheDocument()
    expect(within(dialog).getByText('The first message')).toBeInTheDocument()
    // The consequence, stated: this is the only warning a person gets.
    expect(within(dialog).getByText('This cannot be undone.')).toBeInTheDocument()
  })
})

describe('when the read fails', () => {
  it('says so where the list would have been, instead of showing an empty book', async () => {
    stubs.fetchStub.mockImplementation(() => Promise.resolve(json({ detail: 'boom' }, 503)))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText('No entries yet. Be the first.')).not.toBeInTheDocument()
  })
})

describe('the question lives in the address', () => {
  it('leaves the address clean while the screen is asking its default question', async () => {
    renderPage()
    await screen.findByText('The first message')

    // `?q=&sort=newest&shown=4` says the same thing as `/guestbook` and is
    // worse to read, to link and to type.
    expect(address()).toBe('/guestbook')
  })

  it('writes the phrase, the order and the page size into it', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('The first message')

    await user.type(screen.getByRole('searchbox', { name: 'Search entries' }), 'Message')
    await waitFor(() => expect(address()).toContain('q=Message'))

    await user.click(screen.getByRole('button', { name: 'Oldest' }))
    await waitFor(() => expect(address()).toContain('sort=oldest'))

    await user.click(await screen.findByRole('button', { name: /Load/ }))
    await waitFor(() => expect(address()).toContain('shown=8'))
  })

  it('starts a deep link on exactly what the link says', async () => {
    renderPage('/guestbook?q=Message+8&sort=oldest')

    await screen.findByText('Message 8')

    // The box is seeded too, or the phrase would be invisible to the person who
    // followed the link and impossible to edit without retyping.
    expect(screen.getByRole('searchbox', { name: 'Search entries' })).toHaveValue('Message 8')
    expect(screen.getByRole('button', { name: 'Oldest' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('1 match for \u201cMessage 8\u201d')).toBeInTheDocument()
  })

  it('refuses a hand-edited page size the endpoint would reject', async () => {
    renderPage('/guestbook?shown=99999')
    await screen.findByText('The first message')

    // Passed through, this reaches the endpoint as a 422 and the screen shows an
    // error for an address somebody merely mistyped.
    await waitFor(() => {
      const last = new URL(stubs.fetchStub.mock.calls.at(-1)![0].url).searchParams
      expect(Number(last.get('limit'))).toBeLessThanOrEqual(100)
    })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('clears the question after a post, so the new entry is where it is looked for', async () => {
    const user = userEvent.setup()
    renderPage('/guestbook?q=Message+8&sort=oldest')
    await screen.findByText('Message 8')

    await user.type(screen.getByRole('textbox', { name: 'Your name' }), 'Clara')
    await user.type(screen.getByRole('textbox', { name: 'Your message' }), 'A brand new entry')
    await user.click(screen.getByRole('button', { name: 'Post entry' }))

    // Posting into a search that does not match the new entry looks exactly like
    // the write having failed.
    await waitFor(() => expect(address()).toBe('/guestbook'))
    expect(screen.getByRole('searchbox', { name: 'Search entries' })).toHaveValue('')
  })
})
