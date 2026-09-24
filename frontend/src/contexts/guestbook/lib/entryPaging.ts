import { PAGE_SIZE_MAX } from '@/contexts/guestbook/lib/guestbookEntry'

/**
 * How much of the guestbook is on screen, and what to ask for next.
 *
 * Its own module because every rule here is a **pure function of four numbers**
 * and none of them needs React, a router or a cache to be decided. The screen
 * was getting this wrong in a way no component test could see: `?shown=` used to
 * mean "how big one request may be", which is a server's parameter wearing a
 * reader's name. Clamped to the contract's ceiling, it stopped counting at a
 * hundred, the query key stopped moving, and "Load more" kept offering entries
 * it could no longer fetch.
 *
 * **`?shown=` means how many entries are on screen.** One request cannot carry
 * more than `PAGE_SIZE_MAX` of them, so the screen restores an address by
 * repeating requests -- each one inside the contract's bounds
 * (`spec/design/api.md` § Collection read parameters), none of them a `422`.
 */

/**
 * The most a single address may put on screen.
 *
 * A ceiling is needed because restoring `?shown=` costs one request per
 * `PAGE_SIZE_MAX` entries, and a hand-typed `?shown=999999` over a large
 * guestbook would spend them all. Ten pieces is the number: it is far past any
 * address a person arrives at by pressing a button, and it bounds the cost of
 * one somebody typed. Stated as a multiple rather than as `1000`, so it moves
 * with the contract's own ceiling instead of drifting from it.
 */
export const SHOWN_MAX = PAGE_SIZE_MAX * 10

/** One read of the guestbook, in the endpoint's own two parameters. */
export interface PageRequest {
  offset: number
  limit: number
}

/**
 * `shown` from the address, or the first piece. A hostile value is not a count.
 *
 * Below one piece is not a smaller screen, it is a malformed address: `step` is
 * the floor. Above `SHOWN_MAX` it is clamped rather than passed through, for the
 * same reason the old clamp existed -- an address somebody mistyped should show
 * the guestbook, not an error and not five hundred requests.
 */
export function shownFrom(raw: string | null, step: number): number {
  const asked = Number(raw)
  if (!Number.isInteger(asked) || asked < step) return step
  return Math.min(asked, SHOWN_MAX)
}

/**
 * The first read for an address that says `shown` entries are on screen.
 *
 * As much of the restore as one request may carry. Asking for four and then
 * repeating twenty-five times would put the same entries on screen at
 * twenty-five times the cost.
 */
export function firstPageRequest(shown: number): PageRequest {
  return { offset: 0, limit: Math.min(shown, PAGE_SIZE_MAX) }
}

export interface PageCursor {
  /** How many entries are already loaded. */
  loaded: number
  /** How many the address says should be. */
  shown: number
  /** How many match the current question, in total. */
  total: number
  /** How many one press of "Load more" adds. */
  step: number
}

/**
 * The next read, or `undefined` when the whole result is on screen.
 *
 * Two regimes and one function, because they differ only in how much to ask
 * for. Below `shown` the screen is still **restoring an address** and asks for
 * the rest in whole pieces; at or above it, it is answering a press of "Load
 * more" and asks for `step`. Both start at `loaded`, which is what makes the
 * pieces meet exactly: the order is total (`BR-04`), so an offset is a place in
 * it rather than a guess.
 *
 * `undefined` at the end is not a detail -- it is what takes the button off the
 * screen, and the absence of it is what left "Load N more" promising entries it
 * could not deliver.
 */
export function nextPageRequest({ loaded, shown, total, step }: PageCursor): PageRequest | undefined {
  if (loaded >= total) return undefined
  const wanted = loaded < shown ? shown - loaded : step
  return { offset: loaded, limit: Math.min(wanted, PAGE_SIZE_MAX) }
}
