/**
 * Instants, as the API sends them.
 *
 * `parseInstant` is the one door through which a timestamp enters the screen. It
 * exists for the case the contract forbids and a fixture or a pasted value still
 * produces: a string with no zone marker. (Formatting an instant as
 * `YYYY-MM-DD HH:MM` lived here too, for screens this template does not have;
 * `relativeTime.ts` is the only formatter the guestbook needs, and the rest went
 * with the product it came from.)
 */

/**
 * A timestamp already carries a zone: `Z`, or an offset like `+02:00`.
 *
 * Anchored at the end, because that is the only place a zone may appear -- and
 * `-` has to be matched there rather than anywhere, or the date's own hyphens
 * would look like an offset.
 */
const HAS_A_ZONE = /([Zz]|[+-]\d{2}:?\d{2})$/

/**
 * One instant from what the API sent, with or without its zone marker.
 *
 * `spec/design/api.md` says instants travel as ISO-8601 with an offset, and the
 * application honours that. The rule here is broader than the contract on
 * purpose: a bare `2026-08-31T18:52:00` -- from a producer that dropped the
 * marker, a fixture, a pasted value -- is parsed by every browser as **local**
 * time, while the value is UTC and only the marker is missing. Without this the
 * whole screen is silently wrong by the machine's offset, and wrong in the
 * direction nobody checks: two hours west of Warsaw an entry written a moment
 * ago says it was written two hours ago, which reads as stale data rather than
 * as a timezone. So a string with no zone is read as the UTC it is.
 */
export function parseInstant(iso: string): Date {
  return new Date(HAS_A_ZONE.test(iso) ? iso : `${iso}Z`)
}
