import { describe, expect, it } from 'vitest'

import { parseInstant } from './datetime'

/**
 * The rule under test is the one the contract cannot enforce at the wire: a
 * timestamp with no zone marker is UTC, never the machine's local time. Every
 * expectation is an absolute instant (`Date.UTC`), so the assertions hold in
 * whatever timezone CI happens to run.
 */
describe('parseInstant', () => {
  it('honours the zone marker the API sent, Z or an offset either way', () => {
    const instant = Date.UTC(2026, 7, 31, 18, 52)
    expect(parseInstant('2026-08-31T18:52:00Z').getTime()).toBe(instant)
    expect(parseInstant('2026-08-31T20:52:00+02:00').getTime()).toBe(instant)
    expect(parseInstant('2026-08-31T13:52:00-05:00').getTime()).toBe(instant)
  })

  it('reads a string with no marker as the UTC it is, never as local time', () => {
    expect(parseInstant('2026-08-31T18:52:00').getTime()).toBe(Date.UTC(2026, 7, 31, 18, 52))
  })

  it('does not mistake the hyphens of the date for a negative offset', () => {
    expect(parseInstant('2026-08-31T00:00:00').getTime()).toBe(Date.UTC(2026, 7, 31))
  })
})
