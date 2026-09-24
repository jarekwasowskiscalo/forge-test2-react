import { describe, expect, it } from 'vitest'

import { PAGE_SIZE_MAX } from '@/contexts/guestbook/lib/guestbookEntry'

import { SHOWN_MAX, firstPageRequest, nextPageRequest, shownFrom } from './entryPaging'

/**
 * The arithmetic that decides how much of the guestbook is on screen.
 *
 * It is tested here rather than through the screen because the defect it was
 * written for was invisible from the screen: the old clamp answered correctly
 * for every book smaller than the contract's ceiling, which is every book
 * anybody had. The rules below are checked **at** the ceiling and past it, which
 * is where the arithmetic is the only thing left holding.
 */

const STEP = 4

describe('reading `?shown=` out of the address', () => {
  it('opens on one piece when the address says nothing', () => {
    expect(shownFrom(null, STEP)).toBe(STEP)
  })

  it('takes a number bigger than the contract ceiling at face value', () => {
    // The whole defect in one assertion. `?shown=` used to be clamped to
    // `PAGE_SIZE_MAX`, which silently redefined it from "how many are on screen"
    // to "how big one request may be" -- and once the two met, pressing for more
    // changed nothing at all.
    expect(shownFrom('104', STEP)).toBe(104)
    expect(shownFrom(String(PAGE_SIZE_MAX), STEP)).toBe(PAGE_SIZE_MAX)
  })

  it('refuses a value that is not a count', () => {
    // An address somebody mistyped should show the guestbook rather than an
    // error, so each of these falls back to the first piece.
    expect(shownFrom('nonsense', STEP)).toBe(STEP)
    expect(shownFrom('-4', STEP)).toBe(STEP)
    expect(shownFrom('4.5', STEP)).toBe(STEP)
    expect(shownFrom('', STEP)).toBe(STEP)
    // Below one piece is a malformed address, not a smaller screen.
    expect(shownFrom('1', STEP)).toBe(STEP)
  })

  it('still has a ceiling, because restoring one costs requests', () => {
    expect(shownFrom('999999', STEP)).toBe(SHOWN_MAX)
    expect(SHOWN_MAX % PAGE_SIZE_MAX).toBe(0)
  })
})

describe('what to ask for', () => {
  it('asks for as much of the restore as one request may carry', () => {
    expect(firstPageRequest(STEP)).toEqual({ offset: 0, limit: STEP })
    expect(firstPageRequest(8)).toEqual({ offset: 0, limit: 8 })
    // Never past the contract's own bound -- the value that would come back a
    // `422` and put an error on screen for an address somebody merely typed.
    expect(firstPageRequest(104)).toEqual({ offset: 0, limit: PAGE_SIZE_MAX })
    expect(firstPageRequest(SHOWN_MAX)).toEqual({ offset: 0, limit: PAGE_SIZE_MAX })
  })

  it('carries on from where the last piece ended', () => {
    expect(nextPageRequest({ loaded: 4, shown: 4, total: 9, step: STEP })).toEqual({
      offset: 4,
      limit: STEP,
    })
  })

  it('finishes a restore in whole pieces rather than one press at a time', () => {
    // An address saying a hundred and four are on screen is two requests, not
    // twenty-six: the same entries either way, and the cost is the difference.
    expect(nextPageRequest({ loaded: 100, shown: 104, total: 400, step: STEP })).toEqual({
      offset: 100,
      limit: 4,
    })
    expect(nextPageRequest({ loaded: 0, shown: 250, total: 400, step: STEP })).toEqual({
      offset: 0,
      limit: PAGE_SIZE_MAX,
    })
  })

  it('goes back to one press at a time once the address is satisfied', () => {
    expect(nextPageRequest({ loaded: 104, shown: 104, total: 400, step: STEP })).toEqual({
      offset: 104,
      limit: STEP,
    })
  })

  it('stops at the end of the guestbook, whatever the address asked for', () => {
    // This `undefined` is what takes the button off the screen. Without it the
    // button stayed for ever, offering entries it could no longer fetch.
    expect(nextPageRequest({ loaded: 9, shown: 9, total: 9, step: STEP })).toBeUndefined()
    expect(nextPageRequest({ loaded: 9, shown: SHOWN_MAX, total: 9, step: STEP })).toBeUndefined()
    expect(nextPageRequest({ loaded: 0, shown: STEP, total: 0, step: STEP })).toBeUndefined()
  })

  it('never asks for more than one request may carry, at any point', () => {
    // Walked rather than sampled: every piece of a book bigger than the ceiling
    // has to stay inside it, and each has to start where the last one stopped.
    const total = 250
    let loaded = 0
    const offsets: number[] = []
    for (;;) {
      const next = nextPageRequest({ loaded, shown: SHOWN_MAX, total, step: STEP })
      if (next === undefined) break
      expect(next.limit).toBeLessThanOrEqual(PAGE_SIZE_MAX)
      expect(next.limit).toBeGreaterThan(0)
      expect(next.offset).toBe(loaded)
      offsets.push(next.offset)
      loaded = Math.min(loaded + next.limit, total)
    }
    expect(loaded).toBe(total)
    expect(offsets).toEqual([0, 100, 200])
  })
})
