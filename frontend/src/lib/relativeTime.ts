/**
 * How long ago something was written, in words.
 *
 * Its own module and not part of `datetime.ts`, because the two answer
 * different questions and `datetime.ts` answers its one under a rule this one
 * is exempt from: `YYYY-MM-DD` for a timestamp an operator copies into a
 * ticket. An entry's age is not that -- it is prose inside a
 * sentence a guest reads once -- so it is allowed to say "2 hours ago", and the
 * two renderers must not be able to reach each other's rules.
 *
 * **The wording is English** (`spec/design/conventions.md` § Language). One plural
 * rule, applied by comparing the count to one, and no `Intl.RelativeTimeFormat`:
 * the thresholds below are a product decision about when a number stops being
 * useful, and `Intl` would decide them itself and differently per browser.
 *
 * The instant is parsed by `datetime.ts`, not by `new Date` here -- the two
 * renderers have to agree about what a zone-less timestamp means.
 */

import { parseInstant } from './datetime'

/** Everything past this many days is a date, not an age. */
const DAYS_BEFORE_A_DATE = 30

const MINUTE_MS = 60_000
const HOUR_MS = 60 * MINUTE_MS
const DAY_MS = 24 * HOUR_MS

/** `1 minute ago` / `2 minutes ago`. English has two forms and one rule. */
function ago(count: number, unit: string): string {
  return `${count} ${unit}${count === 1 ? '' : 's'} ago`
}

/**
 * `"2026-08-31T18:22:00Z"` -> `"2 hours ago"`, and past a month `"31 Aug 2026"`.
 *
 * `now` is an argument rather than a `Date.now()` read inside, so the thresholds
 * can be asserted at the exact instant either side of each one. A function that
 * reads the clock itself is a function whose boundary behaviour can only be
 * tested by waiting.
 *
 * A future timestamp reads as "just now" rather than as a negative age. Clocks
 * disagree by seconds all the time, and "in -1 minutes" is a bug report about
 * nothing; the entry was, for every purpose a guest has, written now.
 */
export function timeAgo(iso: string, now: Date = new Date()): string {
  const written = parseInstant(iso)
  if (Number.isNaN(written.getTime())) return iso

  const elapsed = now.getTime() - written.getTime()
  if (elapsed < MINUTE_MS) return 'just now'

  const minutes = Math.round(elapsed / MINUTE_MS)
  if (minutes < 60) return ago(minutes, 'minute')

  const hours = Math.round(elapsed / HOUR_MS)
  if (hours < 24) return ago(hours, 'hour')

  const days = Math.round(elapsed / DAY_MS)
  if (days < DAYS_BEFORE_A_DATE) return ago(days, 'day')

  return formatWrittenOn(written)
}

/**
 * `"31 Aug 2026"` -- what an entry older than a month says instead of its age.
 *
 * Assembled from `en-GB` parts rather than the browser's locale: the copy on
 * this screen is English by decision, and a machine set to `en-US` would
 * otherwise render `Aug 31, 2026` in the middle of a page that says nothing
 * else differently.
 */
function formatWrittenOn(written: Date): string {
  return written.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
