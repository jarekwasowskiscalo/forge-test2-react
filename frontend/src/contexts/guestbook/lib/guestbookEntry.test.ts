import { describe, expect, it } from 'vitest'

import {
  AUTHOR_MAX_LENGTH,
  MESSAGE_MAX_LENGTH,
  authorProblem,
  canSubmitEntry,
  messageProblem,
  normalizeEntryField,
  wasEdited,
} from './guestbookEntry'
import type { GuestbookEntry } from './guestbookEntry'

/**
 * The frontend's copy of the server's rules, and the boundaries it has to
 * agree with the server about.
 *
 * The bounds are read from the exported constants rather than written as `80`
 * and `1000`, so this file cannot be the thing that keeps a stale number alive
 * after the rule moves. What it does pin is the *behaviour at the boundary*:
 * exactly at the limit is allowed, one over is not -- the off-by-one that a
 * `>` written as `>=` produces, which no screen would show until somebody typed
 * a name of exactly eighty characters.
 */

function entry(overrides: Partial<GuestbookEntry> = {}): GuestbookEntry {
  return {
    id: '0d0d5c3a-6d9c-4a1e-9a4a-2f7f6f0e5b11',
    author: 'Anna',
    message: 'Good morning',
    created_at: '2026-08-30T20:00:00Z',
    updated_at: '2026-08-30T20:00:00Z',
    ...overrides,
  }
}

describe('normalizeEntryField', () => {
  it('trims ascii padding the way the server does [req:CR-2609-9b1e/R-2]', () => {
    // The server normalizes before it measures, so a frontend that measured the
    // untrimmed value would call "   " a five-character name.
    //
    // This case is ASCII, and its title no longer claims more than that. It used
    // to read "trims the way the server trims, so both measure the same string"
    // over two assertions about the ordinary space -- a character in the
    // INTERSECTION of the two runtimes' whitespace sets, so the test could not
    // fail on the six code points where they actually disagreed. The claim about
    // both sides measuring one string is now made where it can be checked:
    // `entryText.test.ts`, against a corpus the server's suite reads too.
    expect(normalizeEntryField('  Anna  ')).toBe('Anna')
    expect(normalizeEntryField('   ')).toBe('')
  })

  it('trims what only the server used to trim [req:CR-2609-9b1e/R-2]', () => {
    // `String.prototype.trim` leaves all five of these; `str.strip()` removes
    // them. One case here so the disagreement is visible beside the rule it
    // broke, rather than only inside the corpus.
    for (const code of [0x001c, 0x001d, 0x001e, 0x001f, 0x0085]) {
      expect(normalizeEntryField(String.fromCodePoint(code))).toBe('')
    }
  })

  it('measures a signature of emoji in code points [req:CR-2609-9b1e/R-2]', () => {
    // 41 grinning faces: 41 code points, 82 UTF-16 code units. The server has
    // always stored this and the browser has always refused it.
    expect(authorProblem(String.fromCodePoint(0x1f600).repeat(41))).toBeUndefined()
    expect(
      authorProblem(String.fromCodePoint(0x1f600).repeat(AUTHOR_MAX_LENGTH + 1)),
    ).toBe('author_too_long')
  })
})

describe('authorProblem', () => {
  it('refuses an empty signature', () => {
    expect(authorProblem('')).toBe('author_empty')
  })

  it('refuses a signature of nothing but whitespace [req:CR-2609-9b1e/R-2]', () => {
    expect(authorProblem('   ')).toBe('author_empty')
  })

  it('accepts a signature of exactly the maximum length [req:CR-2609-9b1e/R-2]', () => {
    expect(authorProblem('a'.repeat(AUTHOR_MAX_LENGTH))).toBeUndefined()
  })

  it('refuses one character past the maximum', () => {
    expect(authorProblem('a'.repeat(AUTHOR_MAX_LENGTH + 1))).toBe('author_too_long')
  })

  it('measures the trimmed value, so surrounding spaces do not spend the budget [req:CR-2609-9b1e/R-2]', () => {
    expect(authorProblem(`  ${'a'.repeat(AUTHOR_MAX_LENGTH)}  `)).toBeUndefined()
  })
})

describe('messageProblem', () => {
  it('refuses an empty message', () => {
    expect(messageProblem('')).toBe('message_empty')
    expect(messageProblem(' \n ')).toBe('message_empty')
  })

  it('accepts a message of exactly the maximum length and refuses one more', () => {
    expect(messageProblem('x'.repeat(MESSAGE_MAX_LENGTH))).toBeUndefined()
    expect(messageProblem('x'.repeat(MESSAGE_MAX_LENGTH + 1))).toBe('message_too_long')
  })
})

describe('canSubmitEntry', () => {
  it('needs both fields to be right', () => {
    expect(canSubmitEntry('Anna', 'Good morning')).toBe(true)
    expect(canSubmitEntry('', 'Good morning')).toBe(false)
    expect(canSubmitEntry('Anna', '')).toBe(false)
  })
})

describe('wasEdited', () => {
  it('is false for an entry that was never edited [req:CR-2609-9b1e/R-4]', () => {
    // `BR-02`: a freshly created entry carries the two timestamps as one
    // identical instant, by construction rather than by rounding.
    expect(wasEdited(entry())).toBe(false)
  })

  it('is true once updated_at has moved [req:CR-2609-9b1e/R-4]', () => {
    expect(wasEdited(entry({ updated_at: '2026-08-30T21:00:00Z' }))).toBe(true)
  })
})
