import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { useEntryQueryParams } from './useEntryQueryParams'

/**
 * Which way the flow runs between the address and the search box.
 *
 * This hook had no test of its own, deliberately: its only observable behaviour
 * was said to be the state of the screen. That held while the hook only ever
 * wrote to the address. It stopped holding the moment the question was **read**
 * from the address too, because the interesting cases are navigations arriving
 * at a mounted hook -- Back, Forward, a link followed in place -- and the screen
 * test would have to build this same harness to reach them.
 *
 * The defect being held down: `setParams` from `useSearchParams` is a callback
 * closing over the current parameters, so its identity changes on **every**
 * navigation. An effect that listed it therefore re-ran as if somebody had
 * typed, and wrote the pre-navigation phrase straight back into the address --
 * taking the paging with it, and making Back look broken.
 */

const STEP = 4
const SETTLE_MS = 20

/**
 * The hook, wired to a box and to whatever a test needs to drive.
 *
 * A real `<input>` rather than a bare `renderHook`, because the value in the box
 * is half of what is being asserted: a hook whose returned string is right while
 * the field shows something else is a hook that passes and a screen that lies.
 */
function Harness() {
  const { typed, search, sort, shown, onSearchChange, onSortChange, onShownChange } =
    useEntryQueryParams(STEP, SETTLE_MS)
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <>
      <input aria-label="Search entries" value={typed} onChange={(e) => onSearchChange(e.target.value)} />
      <span data-testid="address">{`${location.pathname}${location.search}`}</span>
      <span data-testid="search">{search}</span>
      <span data-testid="sort">{sort}</span>
      <span data-testid="shown">{shown}</span>
      <button type="button" onClick={() => navigate('/guestbook?q=brian')}>
        Go to brian
      </button>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
      <button type="button" onClick={() => navigate(1)}>
        Forward
      </button>
      <button type="button" onClick={() => onSortChange('oldest')}>
        Oldest
      </button>
      <button type="button" onClick={() => onShownChange(8)}>
        More
      </button>
    </>
  )
}

function renderHarness(initialUrl = '/guestbook', earlier: string[] = []) {
  return render(
    <MemoryRouter initialEntries={[...earlier, initialUrl]}>
      <Harness />
    </MemoryRouter>,
  )
}

function address(): string {
  return screen.getByTestId('address').textContent ?? ''
}

function box(): HTMLInputElement {
  return screen.getByRole<HTMLInputElement>('textbox', { name: 'Search entries' })
}

/** Wait past the debounce, so a write that was going to happen has happened. */
async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, SETTLE_MS * 3))
  })
}

describe('arriving with a question already asked', () => {
  it('starts on exactly what the link says, box included [req:CR-2609-9b1e/R-6]', async () => {
    renderHarness('/guestbook?q=anna&sort=oldest&shown=8')

    expect(box().value).toBe('anna')
    expect(screen.getByTestId('search').textContent).toBe('anna')
    expect(screen.getByTestId('sort').textContent).toBe('oldest')
    expect(screen.getByTestId('shown').textContent).toBe('8')

    // And nothing is written back: a screen that rewrote the address it was
    // opened on would break every link somebody sent.
    await settle()
    expect(address()).toBe('/guestbook?q=anna&sort=oldest&shown=8')
  })

  it('leaves the ordinary address alone [req:CR-2609-9b1e/R-6]', async () => {
    renderHarness()
    await settle()
    expect(address()).toBe('/guestbook')
  })
})

describe('typing', () => {
  it('reaches the address once the typing settles, and resets the piece [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderHarness('/guestbook?shown=8')

    await user.type(box(), 'anna')
    await waitFor(() => expect(address()).toBe('/guestbook?q=anna'))
    // Narrowing starts the piece over, or eight loaded entries become eight
    // results for a phrase that matches two.
    expect(screen.getByTestId('shown').textContent).toBe(String(STEP))
  })

  it('leaves one history entry for a phrase, not one per letter [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    // Something to go back TO, because every write replaces: without an earlier
    // entry there is nothing behind the screen to press Back into, and the test
    // would prove only that.
    renderHarness('/guestbook', ['/guestbook?q=seed'])

    await user.type(box(), 'anna')
    await waitFor(() => expect(address()).toBe('/guestbook?q=anna'))

    // One press leaves the phrase entirely. Pushing per keystroke would put
    // `?q=ann` here, and Back would walk the letters off one at a time.
    await user.click(screen.getByRole('button', { name: 'Back' }))
    await waitFor(() => expect(address()).toBe('/guestbook?q=seed'))
    expect(box().value).toBe('seed')
  })

  it('takes the phrase out of the address when the box is emptied [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderHarness('/guestbook?q=anna')

    await user.clear(box())
    await waitFor(() => expect(address()).toBe('/guestbook'))
  })
})

describe('a navigation arriving at a mounted hook', () => {
  it('wins, and the deferred write does not come back [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup()
    renderHarness('/guestbook?q=anna')
    expect(box().value).toBe('anna')

    await user.click(screen.getByRole('button', { name: 'Go to brian' }))

    // The box follows the address, at once.
    await waitFor(() => expect(box().value).toBe('brian'))
    expect(screen.getByTestId('search').textContent).toBe('brian')

    // And still does after the debounce has had every chance to fire. This is
    // the exact inverse of what was observed: the hook went back to `?q=anna`.
    await settle()
    expect(address()).toBe('/guestbook?q=brian')
    expect(box().value).toBe('brian')
  })

  it('cancels a write deferred from before it, and leaves Forward working [req:CR-2609-9b1e/R-6]', async () => {
    const user = userEvent.setup({ delay: null })
    renderHarness('/guestbook?q=anna')

    // Typed, but not yet settled: the write is in the air when Back happens.
    await user.type(box(), 'x')
    await user.click(screen.getByRole('button', { name: 'Go to brian' }))
    await waitFor(() => expect(box().value).toBe('brian'))

    await user.click(screen.getByRole('button', { name: 'Back' }))
    await waitFor(() => expect(address()).toBe('/guestbook?q=anna'))
    await settle()

    // `annax` would have been written by the timer that outlived the
    // navigation; with `replace: true` it would also have overwritten the
    // history entry and taken Forward with it.
    expect(address()).toBe('/guestbook?q=anna')
    expect(box().value).toBe('anna')

    await user.click(screen.getByRole('button', { name: 'Forward' }))
    await waitFor(() => expect(address()).toBe('/guestbook?q=brian'))
    await settle()
    expect(address()).toBe('/guestbook?q=brian')
    expect(box().value).toBe('brian')
  })
})

describe('the other two parameters', () => {
  it('write the order and reset the piece [req:CR-2609-9b1e/R-3]', async () => {
    const user = userEvent.setup()
    renderHarness('/guestbook?shown=8')

    await user.click(screen.getByRole('button', { name: 'Oldest' }))
    await waitFor(() => expect(address()).toBe('/guestbook?sort=oldest'))
    expect(screen.getByTestId('shown').textContent).toBe(String(STEP))
  })

  it('record how much is on screen, and nothing else [req:CR-2609-9b1e/R-7]', async () => {
    const user = userEvent.setup()
    renderHarness('/guestbook?q=anna')

    await user.click(screen.getByRole('button', { name: 'More' }))
    await waitFor(() => expect(screen.getByTestId('shown').textContent).toBe('8'))
    // Writing the address is the whole of it. What that number means for the
    // requests is the reading hook's business, which is what keeps one fact in
    // one place.
    expect(address()).toBe('/guestbook?q=anna&shown=8')
  })
})
