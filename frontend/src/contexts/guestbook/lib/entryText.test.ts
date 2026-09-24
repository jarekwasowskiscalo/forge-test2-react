import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

import { TRIMMED, normalizeText, textLength } from './entryText'
import { AUTHOR_MAX_LENGTH, MESSAGE_MAX_LENGTH, QUERY_MAX_LENGTH } from './guestbookEntry'

/**
 * The browser's half of one rule that two languages keep.
 *
 * This file and `tests/unit/test_entry_text_rules.py` read the SAME BYTES and
 * assert the same verdicts and the same lengths against them. That is the only
 * shape that can prove the two sides measure one string identically, because
 * agreement is not a property either side has by itself -- and it is why this is
 * the one module in `frontend/src` allowed to reach into the corpus.
 * `golden-set/README.md` section "The frontend and the text-measurement corpus"
 * carries the exception; `tests/fitness/test_golden_set.py` names this path and
 * keeps refusing every other one.
 *
 * `readFileSync` rather than a JSON import, following
 * `frontend/src/styles/theme.test.ts`: the file sits outside `frontend/`, so a
 * static import would have to be added to tsconfig's `include`, while reading it
 * at run time needs nothing and cannot drift from the bytes Python reads.
 *
 * What this replaces is `test_length_constants.py` being the only binding between
 * the sides. That test compares the literal 80 here with the literal 80 beside the
 * model and passes -- it has always passed, including throughout the whole life of
 * the defect, because a number can only be checked against a number. A UNIT has to
 * be checked against data.
 */

interface TextCase {
  case: string
  description: string
  field: 'author' | 'message' | 'q'
  input: string
  verdict: 'accepted' | 'empty' | 'too_long'
  length?: number
}

const CORPUS = fileURLToPath(
  new URL('../../../../../golden-set/fixtures/text-measurement.json', import.meta.url),
)

const CASES: TextCase[] = (
  JSON.parse(readFileSync(CORPUS, 'utf8')) as { cases: TextCase[] }
).cases

const BOUNDS: Record<TextCase['field'], number> = {
  author: AUTHOR_MAX_LENGTH,
  message: MESSAGE_MAX_LENGTH,
  q: QUERY_MAX_LENGTH,
}

/** What the rule says about one case -- the corpus's claim, recomputed here. */
function verdictOf(entry: TextCase): TextCase['verdict'] {
  const text = normalizeText(entry.input)
  if (text.length === 0) return 'empty'
  return textLength(text) > BOUNDS[entry.field] ? 'too_long' : 'accepted'
}

describe('the shared text-measurement corpus', () => {
  it('is reachable and not empty, so the assertions below mean something [req:CR-2609-9b1e/R-2]', () => {
    // A corpus that failed to load would make every `it.each` below vacuous, and
    // a suite of zero assertions reads on a dashboard exactly like a suite that
    // passed.
    expect(CASES.length).toBeGreaterThan(30)
  })

  it.each(CASES.map((entry) => [entry.case, entry] as const))(
    'gives %s the verdict the corpus states [req:CR-2609-9b1e/R-2]',
    (_name, entry) => {
      expect(verdictOf(entry)).toBe(entry.verdict)
    },
  )

  it.each(CASES.filter((entry) => entry.verdict === 'accepted').map((e) => [e.case, e] as const))(
    'measures %s to exactly the length the corpus states [req:CR-2609-9b1e/R-2]',
    (_name, entry) => {
      // The verdict alone would pass with the wrong unit: "accepted" is true of
      // eighty emoji however they are counted, as long as the count fits. The
      // LENGTH is what names the unit.
      expect(textLength(normalizeText(entry.input))).toBe(entry.length)
    },
  )
})

describe('the rule itself', () => {
  it('trims the union of both runtimes and nothing else [req:CR-2609-9b1e/R-2]', () => {
    // Stated as arithmetic rather than as a list nobody recounts. The BOM is the
    // one this runtime already removed; the four C0 separators and NEL are the
    // ones only Python did.
    expect(TRIMMED.size).toBe(30)
    for (const code of [0x001c, 0x001d, 0x001e, 0x001f, 0x0085, 0xfeff]) {
      expect(TRIMMED.has(String.fromCodePoint(code))).toBe(true)
    }
    // Deliberately absent, and written down rather than inherited.
    expect(TRIMMED.has(String.fromCodePoint(0x200b))).toBe(false)
    expect(TRIMMED.has(String.fromCodePoint(0x180e))).toBe(false)
  })

  it('makes the two spellings of one word one value [req:CR-2609-9b1e/R-2]', () => {
    const decomposed = `e${String.fromCodePoint(0x0301)}`.repeat(AUTHOR_MAX_LENGTH)
    const precomposed = String.fromCodePoint(0x00e9).repeat(AUTHOR_MAX_LENGTH)

    expect(normalizeText(decomposed)).toBe(normalizeText(precomposed))
    expect(textLength(normalizeText(decomposed))).toBe(AUTHOR_MAX_LENGTH)
  })

  it('leaves whitespace inside a value alone [req:CR-2609-9b1e/R-2]', () => {
    const inside = `Anna${String.fromCodePoint(0x0085)}B`

    expect(normalizeText(inside)).toBe(inside)
    expect(textLength(normalizeText(inside))).toBe(6)
  })
})

describe('the detectors, with proof that they fire', () => {
  it('would go red if length were measured in utf-16 units again [req:CR-2609-9b1e/R-2]', () => {
    // The old rule, run against the corpus written for it. A suite that cannot
    // show the old behaviour failing has not shown that it tests the new one.
    const disagreed = CASES.filter(
      (entry) =>
        entry.verdict === 'accepted' && normalizeText(entry.input).length !== entry.length,
    )

    expect(disagreed.length).toBeGreaterThan(0)
    expect(disagreed.map((entry) => entry.case)).toContain('emoji_at_maximum')
  })

  it('would go red if trimming went back to the runtime default [req:CR-2609-9b1e/R-2]', () => {
    // `trim()` leaves the five code points only Python ever removed, so a
    // signature of nothing but a next line would stop being empty.
    const disagreed = CASES.filter(
      (entry) => entry.input.normalize('NFC').trim() !== normalizeText(entry.input),
    )

    expect(disagreed.map((entry) => entry.case)).toContain('only_the_next_line')
    expect(disagreed.map((entry) => entry.case)).toContain('only_the_unit_separator')
  })

  it('would go red if normalization were skipped [req:CR-2609-9b1e/R-2]', () => {
    const raw = `e${String.fromCodePoint(0x0301)}`.repeat(AUTHOR_MAX_LENGTH)

    expect(textLength(raw)).toBeGreaterThan(AUTHOR_MAX_LENGTH)
    expect(textLength(normalizeText(raw))).toBe(AUTHOR_MAX_LENGTH)
  })
})
