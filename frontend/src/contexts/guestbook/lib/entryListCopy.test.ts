import { describe, expect, it } from 'vitest'

import { describeEmpty, describeResult, entryCountLabel, loadMoreLabel } from './entryListCopy'

/**
 * The four sentences the list says about itself.
 *
 * Each is here because it has a case where the obvious implementation is wrong
 * in a way nobody would notice on a screenshot: a plural at one, a result line
 * that must not read as a page, an empty state that must not invite a first
 * entry into a book that already has fifty, and a button that must not promise
 * four when one remains.
 */

describe('entryCountLabel', () => {
  it('is singular only at exactly one', () => {
    expect(entryCountLabel(0)).toBe('0 entries')
    expect(entryCountLabel(1)).toBe('1 entry')
    expect(entryCountLabel(2)).toBe('2 entries')
  })
})

describe('describeResult', () => {
  it('says how much of the book is on screen when nothing is being searched for', () => {
    expect(describeResult({ search: '', shown: 4, total: 12, settled: true })).toBe('Showing 4 of 12')
  })

  it('counts matches and quotes the phrase back when there is one', () => {
    // Quoted verbatim: a search that silently normalised what it was given
    // would leave somebody staring at a result for a phrase they did not type.
    expect(describeResult({ search: 'anna', shown: 3, total: 3, settled: true })).toBe('3 matches for “anna”')
    expect(describeResult({ search: 'anna', shown: 1, total: 1, settled: true })).toBe('1 match for “anna”')
  })

  it('counts what matched, not what fits on the page [req:CR-2609-9b1e/R-7]', () => {
    // The whole reason the endpoint answers with two numbers. Reporting `shown`
    // here would tell somebody a search found four when it found forty.
    expect(describeResult({ search: 'anna', shown: 4, total: 40, settled: true })).toBe('40 matches for “anna”')
  })

  it('says zero matches rather than falling silent [req:CR-2609-9b1e/R-7]', () => {
    expect(describeResult({ search: 'zzz', shown: 0, total: 0, settled: true })).toBe('0 matches for “zzz”')
  })

  it('keeps the numbers and admits they are behind while a newer question travels [req:CR-2609-9b1e/R-6]', () => {
    // The screen kept the previous answer on display and said nothing, so the
    // count read as the answer to the phrase in the box. It was not: the
    // sentence below belongs to “anna”, and the suffix is what stops it being
    // read as a claim about whatever was typed after.
    expect(describeResult({ search: 'anna', shown: 2, total: 2, settled: false })).toBe(
      '2 matches for “anna” — updating…',
    )
    expect(describeResult({ search: '', shown: 4, total: 12, settled: false })).toBe(
      'Showing 4 of 12 — updating…',
    )
  })

  it('reads the same either way once the answer has landed [req:CR-2609-9b1e/R-6]', () => {
    // The stale form must be a suffix on the settled one and nothing else: two
    // sentences maintained apart are two sentences that drift.
    const settled = describeResult({ search: 'anna', shown: 3, total: 3, settled: true })
    const behind = describeResult({ search: 'anna', shown: 3, total: 3, settled: false })
    expect(behind.startsWith(settled)).toBe(true)
  })
})

describe('describeEmpty', () => {
  it('invites a first entry only when the book really is empty [req:CR-2609-9b1e/R-7]', () => {
    expect(describeEmpty('')).toBe('No entries yet. Be the first.')
  })

  it('blames the search when there is one [req:CR-2609-9b1e/R-6]', () => {
    // "Be the first" in front of a book of fifty entries reads as the
    // application having lost them.
    expect(describeEmpty('anna')).toBe('Nothing matches that search.')
  })
})

describe('loadMoreLabel', () => {
  it('offers the step while there is more than a step left', () => {
    expect(loadMoreLabel(10, 4)).toBe('Load 4 more')
  })

  it('never promises more than remains', () => {
    // The button promising four when one is left is a lie the next click
    // exposes -- by the button vanishing, which reads as a failure.
    expect(loadMoreLabel(1, 4)).toBe('Load 1 more')
    expect(loadMoreLabel(3, 4)).toBe('Load 3 more')
  })
})
