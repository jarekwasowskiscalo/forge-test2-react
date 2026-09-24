import { describe, expect, it } from 'vitest'

import { timeAgo } from './relativeTime'

/**
 * The thresholds, asserted on both sides of each one.
 *
 * A boundary proved only where it holds is a boundary nobody has shown sits in
 * the right place: `< 60` written as `<= 60` passes every test that never asks
 * about the sixtieth minute. Every case below is built by subtracting an exact
 * amount from a fixed `now`, which is the reason `timeAgo` takes `now` as an
 * argument at all -- a version reading the clock itself could only be tested by
 * waiting.
 */

const NOW = new Date('2026-08-31T12:00:00Z')

/** `minutes` before `NOW`, as the ISO string the API would have sent. */
function minutesAgo(minutes: number): string {
  return new Date(NOW.getTime() - minutes * 60_000).toISOString()
}

describe('the thresholds', () => {
  it('says "just now" for anything under a minute', () => {
    expect(timeAgo(minutesAgo(0), NOW)).toBe('just now')
    expect(timeAgo(NOW.toISOString(), NOW)).toBe('just now')
  })

  it('counts minutes up to the hour, and hours from it', () => {
    expect(timeAgo(minutesAgo(1), NOW)).toBe('1 minute ago')
    expect(timeAgo(minutesAgo(2), NOW)).toBe('2 minutes ago')
    expect(timeAgo(minutesAgo(59), NOW)).toBe('59 minutes ago')
    expect(timeAgo(minutesAgo(60), NOW)).toBe('1 hour ago')
  })

  it('counts hours up to the day, and days from it', () => {
    expect(timeAgo(minutesAgo(23 * 60), NOW)).toBe('23 hours ago')
    expect(timeAgo(minutesAgo(24 * 60), NOW)).toBe('1 day ago')
    expect(timeAgo(minutesAgo(2 * 24 * 60), NOW)).toBe('2 days ago')
  })

  it('stops counting days after a month and gives the date instead', () => {
    // Past a month, "43 days ago" is a number nobody converts into a date in
    // their head, so the entry starts saying when it was written.
    expect(timeAgo(minutesAgo(29 * 24 * 60), NOW)).toBe('29 days ago')
    expect(timeAgo(minutesAgo(30 * 24 * 60), NOW)).toBe('1 Aug 2026')
  })
})

describe('the plural', () => {
  it('is singular only at exactly one', () => {
    expect(timeAgo(minutesAgo(1), NOW)).toContain('1 minute ')
    expect(timeAgo(minutesAgo(2), NOW)).toContain('2 minutes ')
  })
})

describe('a timestamp that arrived without its zone', () => {
  it('is read as the UTC it is, not as local time on this machine', () => {
    // The same instant, minus the marker -- what a producer that drops it sends.
    // Read as local it would be off by the machine's offset -- and off in the
    // direction nobody checks, where a fresh entry claims to be hours old.
    const withZone = new Date(NOW.getTime() - 5 * 60_000).toISOString()
    const withoutZone = withZone.replace('Z', '')

    expect(timeAgo(withoutZone, NOW)).toBe(timeAgo(withZone, NOW))
    expect(timeAgo(withoutZone, NOW)).toBe('5 minutes ago')
  })

  it('leaves a timestamp that does carry an offset alone', () => {
    // 11:00 at +02:00 is 09:00 UTC, which is three hours before NOW. Appending
    // a `Z` to this would have made it one hour.
    expect(timeAgo('2026-08-31T11:00:00+02:00', NOW)).toBe('3 hours ago')
  })
})

describe('what it refuses to do', () => {
  it('reads a future timestamp as "just now" rather than as a negative age', () => {
    // Clocks disagree by seconds all the time, and "in -1 minutes" is a bug
    // report about nothing.
    const ahead = new Date(NOW.getTime() + 5 * 60_000).toISOString()

    expect(timeAgo(ahead, NOW)).toBe('just now')
  })

  it('hands back what it was given when that is not a timestamp at all', () => {
    // Rendering "Invalid Date" would put a JavaScript noun on a guest's screen.
    // Echoing the value at least names what arrived.
    expect(timeAgo('not-a-date', NOW)).toBe('not-a-date')
  })
})
