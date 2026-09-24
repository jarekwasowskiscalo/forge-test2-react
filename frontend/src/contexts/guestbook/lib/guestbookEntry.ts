import type { components } from '@/api/schema'

import { normalizeText, textLength } from '@/lib/text'

export type GuestbookEntry = components['schemas']['GuestbookEntryRead']

/**
 * The rules an entry has to satisfy, applied before the request leaves the
 * browser.
 *
 * They are a **copy** of the server's rules, deliberately, and the server is
 * the one that decides: this exists so a person sees "too long" while they are
 * still typing rather than after a round trip, not so the browser gets to be
 * the authority. The two are kept honest by
 * `spec/design/api.md` § Refusals naming the same bounds and by
 * `guestbookEntry.test.ts` reading them from the same constants below.
 *
 * The bounds are stated once here and imported by the composer and the card. A
 * component that hardcodes `80` is a component that keeps its own opinion when
 * the rule moves.
 */
export const AUTHOR_MAX_LENGTH = 80
export const MESSAGE_MAX_LENGTH = 1000
/**
 * The largest page the list may ask for -- `PAGE_SIZE_MAX` beside the schemas
 * (`app/contexts/guestbook/schemas/guestbook_entries.py`), copied here for the
 * same reason as the two lengths and held equal by the same fitness test.
 */
export const PAGE_SIZE_MAX = 100
/**
 * The longest search phrase the list endpoint will consider -- `QUERY_MAX_LENGTH`
 * beside the schemas (`app/contexts/guestbook/schemas/guestbook_entries.py`),
 * copied here for the same reason as the two lengths and held equal by the same
 * fitness test.
 *
 * It had no copy at all until the two sides were made to agree about what a
 * length is: the generated contract carries no `maxLength`, so a phrase one
 * character too long left the browser, crossed the wire and came back a 422 with
 * nothing here having measured it.
 */
export const QUERY_MAX_LENGTH = 200

/** Why an entry cannot be submitted, or `undefined` when it can. */
export type EntryProblem =
  | 'author_empty'
  | 'author_too_long'
  | 'message_empty'
  | 'message_too_long'

/**
 * The sentence shown under the offending field.
 *
 * English, finished, and naming the consequence rather than the constraint --
 * "Add a name or a signature" tells somebody what to do; "author: required"
 * tells them what the validator is called.
 */
export const ENTRY_PROBLEM_MESSAGES: Record<EntryProblem, string> = {
  author_empty: 'Add a name or a signature — an entry without one is not saved.',
  author_too_long: `A signature can be at most ${AUTHOR_MAX_LENGTH} characters.`,
  message_empty: 'Write something — an empty entry is not saved.',
  message_too_long: `An entry can be at most ${MESSAGE_MAX_LENGTH} characters.`,
}

/**
 * Trim and normalize the way the server does, so the browser measures the same
 * string the database will store.
 *
 * **That sentence used to be false, and the code under it was the reason.** It
 * said "trim the way the server trims" over a bare `value.trim()`, which removes
 * 25 code points where Python's `str.strip()` removes 29 -- and which leaves the
 * BOM that Python keeps. Six code points were whitespace on one side and content
 * on the other, in both directions. The rule is now written down once, in
 * `@/lib/text` and in `app/platform/schemas/text.py`, and proved against one
 * corpus both languages read.
 *
 * The server normalizes before it measures (`NormalizedText` is a
 * `BeforeValidator`, so it runs ahead of the length constraint), which means a
 * name of nothing but spaces is empty rather than 5 characters long. A frontend
 * that measured the untrimmed value would call that entry valid and then be
 * surprised by a 422.
 */
export function normalizeEntryField(value: string): string {
  return normalizeText(value)
}

/** The problem with `author`, or `undefined` if there is none. */
export function authorProblem(author: string): EntryProblem | undefined {
  const value = normalizeEntryField(author)
  if (textLength(value) === 0) return 'author_empty'
  if (textLength(value) > AUTHOR_MAX_LENGTH) return 'author_too_long'
  return undefined
}

/** The problem with `message`, or `undefined` if there is none. */
export function messageProblem(message: string): EntryProblem | undefined {
  const value = normalizeEntryField(message)
  if (textLength(value) === 0) return 'message_empty'
  if (textLength(value) > MESSAGE_MAX_LENGTH) return 'message_too_long'
  return undefined
}

/** Whether the pair may be submitted at all. */
export function canSubmitEntry(author: string, message: string): boolean {
  return authorProblem(author) === undefined && messageProblem(message) === undefined
}

/**
 * Whether this entry has been edited since it was written.
 *
 * String comparison, not `Date` parsing: both values come from the same server
 * in the same ISO-8601 format, and an entry that was never edited carries the
 * two timestamps as one identical instant by construction (`BR-02`). Parsing
 * them into `Date` first would introduce a millisecond-rounding question the
 * data does not have.
 */
export function wasEdited(entry: GuestbookEntry): boolean {
  return entry.updated_at !== entry.created_at
}
