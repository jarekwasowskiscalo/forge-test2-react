import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import type { GuestbookEntrySort } from '@/contexts/guestbook/hooks/useGuestbookEntries'
import { normalizeText } from '@/contexts/guestbook/lib/entryText'
import { shownFrom } from '@/contexts/guestbook/lib/entryPaging'

/**
 * The question the screen is asking, kept **in the address**.
 *
 * `spec/design/conventions.md` § Frontend puts filters, ordering and paging in
 * the URL, and the reason is the whole of this module: a screen showing a
 * search nobody can link to is a screen whose result cannot be sent to anybody,
 * and one that forgets the search on reload is a screen that punishes a
 * refresh. Both were named as the destination before the search existed.
 *
 * Three parameters, and each is absent from the address at its default, so the
 * ordinary URL stays `/guestbook` rather than
 * `/guestbook?q=&sort=newest&shown=4`.
 *
 * **Every write replaces rather than pushes.** Typing a six-letter phrase would
 * otherwise leave six history entries, and Back would walk the letters off one
 * at a time instead of leaving the screen.
 *
 * **The address wins, and the box follows it.** The flow runs one way: a
 * navigation -- a link, Back, Forward, the jump after a successful post -- is
 * the truth, and the box is reseeded from it. Only typing that happened *after*
 * that navigation may write back. The rule used to be the other way round by
 * accident: `setParams` from `useSearchParams` closes over the current
 * parameters, so its identity changes on **every** navigation, and an effect
 * listing it re-ran as if somebody had typed. The pre-navigation phrase then
 * went straight back into the address, taking the paging with it, and Back
 * looked broken.
 */

const SEARCH = 'q'
const SORT = 'sort'
const SHOWN = 'shown'

export interface EntryQueryParams {
  /** What is in the box right now -- echoes every keystroke. */
  typed: string
  /** What the address says, and therefore what is asked of the server. */
  search: string
  sort: GuestbookEntrySort
  /** How many entries the address asks to see. */
  shown: number
  onSearchChange: (value: string) => void
  onSortChange: (value: GuestbookEntrySort) => void
  /** Ask the address for a different number of entries on screen. */
  onShownChange: (value: number) => void
}

/**
 * What is in the box, and the address it was seeded from.
 *
 * One state and not two, because the pair is one fact: a draft is only a draft
 * *relative to* the address it started from. Splitting them lets a render
 * happen between the two setters, and that render is exactly the moment a stale
 * write slips out.
 */
interface SearchDraft {
  text: string
  /** The `search` this draft was seeded from, or last written to. */
  from: string
}

export function useEntryQueryParams(step: number, settleMs: number): EntryQueryParams {
  const [params, setParams] = useSearchParams()

  const search = params.get(SEARCH) ?? ''
  const sort: GuestbookEntrySort = params.get(SORT) === 'oldest' ? 'oldest' : 'newest'
  const shown = shownFrom(params.get(SHOWN), step)

  /**
   * The box's own value, seeded from the address and reseeded by every
   * navigation.
   *
   * Local rather than read straight from the URL, because the address is only
   * written after the typing settles -- reading it back would make every
   * keystroke wait a quarter of a second to appear. It carries the `search` it
   * came from, because a draft is only a draft *relative to* an address: without
   * that, a draft left over from one address silently becomes an edit of the
   * next one.
   */
  const [draft, setDraft] = useState<SearchDraft>({ text: search, from: search })

  /**
   * A `search` that is not where this draft came from is somebody else's doing
   * -- a link, Back, Forward, or the jump after a post -- and the box follows
   * it.
   *
   * Adjusted **during the render** rather than in an effect, which is what React
   * prescribes for state that has to follow something else: the render is
   * discarded and re-run with the new value before anything reaches the screen.
   * In an effect, the box would show the replaced phrase for a frame and, worse,
   * the write-back below would see a draft and an address that disagree and
   * would resolve the disagreement in the draft's favour -- which is the defect
   * this module is being repaired for.
   */
  if (draft.from !== search) setDraft({ text: search, from: search })

  /** What the box shows, correct on the discarded render too. */
  const typed = draft.from === search ? draft.text : search
  const settled = useDebouncedValue(normalizeText(typed), settleMs)

  useEffect(() => {
    // Nothing was typed since this draft was seeded. Whatever re-ran this
    // effect -- and `setParams` changes identity on every navigation, so
    // something will -- it was not a person.
    if (settled === search) return
    // A value deferred from before a navigation reseeded the box. This is the
    // cancellation, written as a refusal: the timer itself is already cleared,
    // because `typed` changed with the navigation and `useDebouncedValue` clears
    // on every change of its value. What survives a cleared timer is the value
    // it settled on last, and that is what this refuses to write.
    if (settled !== normalizeText(typed)) return

    setParams(
      (current) => {
        const next = new URLSearchParams(current)
        if (settled === '') next.delete(SEARCH)
        else next.set(SEARCH, settled)
        // Narrowing starts the page over: twelve loaded entries must not become
        // twelve results for a phrase that matches two.
        next.delete(SHOWN)
        return next
      },
      { replace: true },
    )
  }, [settled, typed, search, setParams])

  return {
    typed,
    search,
    sort,
    shown,
    onSearchChange: (value) => setDraft({ text: value, from: search }),
    onSortChange: (value) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          if (value === 'newest') next.delete(SORT)
          else next.set(SORT, value)
          next.delete(SHOWN)
          return next
        },
        { replace: true },
      ),
    onShownChange: (value) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          next.set(SHOWN, String(value))
          return next
        },
        { replace: true },
      ),
  }
}
