/**
 * The sentences the list says about itself: how many entries there are, how
 * many a search matched, what an empty result means, and how many more are
 * waiting behind the button.
 *
 * Its own module because every one of them is a **pure function of two numbers
 * and a phrase**, and because all four have to agree about the same thing:
 * "nothing here" and "nothing matches" are different sentences, and an empty
 * list on its own cannot say which one it is. What separates them is the
 * **phrase**, not the count -- an empty list under a search means no match, an
 * empty list under no search means an empty guest book, and the length of the
 * list is the same zero in both cases. The counts do the other half of the
 * work: `total` says how many the search matched and `totalAll` how many the
 * book holds, which is what lets the result line and the header disagree
 * without either being wrong (`spec/design/ui/guestbook.md` -- the empty states
 * are "decided by whether the phrase is empty, not by whether the list is").
 *
 * English (`spec/design/conventions.md` § Language). English has two plural forms
 * and one rule, so the plural is decided inline here and needs no module of its own.
 */

/** `1` -> `"1 entry"`, `7` -> `"7 entries"`. The count in the header. */
export function entryCountLabel(totalAll: number): string {
  return `${totalAll} ${totalAll === 1 ? 'entry' : 'entries'}`
}

export interface ResultDescription {
  /**
   * The phrase these numbers are the answer to, already trimmed. Empty means no
   * search.
   *
   * **The phrase the answer came back for, never the one in the address.** The
   * two are the same only once the screen has settled; in between, the address
   * has already moved on and the numbers have not, and a sentence built from one
   * of each says `2 matches for “Zzz”` over two entries that match nothing of
   * the sort.
   */
  search: string
  /** How many entries are on screen right now. */
  shown: number
  /** How many the search matched, page or no page. */
  total: number
  /**
   * False while a newer question is still travelling.
   *
   * The numbers are not wrong when this is false. They are the answer to an
   * older question, which is a different thing and has to read as one.
   */
  settled: boolean
}

/**
 * What a line gains while a newer question is still travelling.
 *
 * A suffix rather than a second sentence, so the count and the fact that it is
 * behind are read in one breath -- and, in the live region that carries this,
 * announced as one utterance rather than two.
 */
const STALE_SUFFIX = ' — updating…'

/**
 * The line under the toolbar: `3 matches for “anna”`, or `Showing 4 of 12`.
 *
 * Two sentences and not one, because they answer different questions. Without a
 * search the reader wants to know how much of the book they have; with one they
 * want to know whether the search worked at all -- and "Showing 0 of 0" answers
 * that with a number instead of a word.
 *
 * The quotation marks are typographic, matching the mock-up, and the phrase is
 * quoted back verbatim: a search that silently normalised what it was given
 * would leave somebody staring at a result for a phrase they did not type.
 *
 * **An unsettled answer keeps its numbers and says it is behind.** Dropping them
 * would be honest too, and worse: the count is the one thing somebody watching a
 * search wants, and taking it away between every phrase and its answer is the
 * flicker the previous answer is kept on screen to avoid.
 */
export function describeResult({ search, shown, total, settled }: ResultDescription): string {
  const answer =
    search === ''
      ? `Showing ${shown} of ${total}`
      : `${total} ${total === 1 ? 'match' : 'matches'} for “${search}”`
  return settled ? answer : `${answer}${STALE_SUFFIX}`
}

/**
 * What the result line says when the read failed.
 *
 * A blank would also stop the screen claiming the old numbers still hold, and
 * that is not enough: this line lives in an `aria-live` region, so a reader who
 * does not see the error state beside the list is told nothing at all by one.
 * What went wrong belongs to `ErrorState`; this says only that the numbers above
 * are gone.
 */
export const READ_FAILED_LABEL = 'The entries could not be loaded.'

/**
 * What an empty list means -- and it means two different things.
 *
 * A book with nothing in it invites a first entry. A search with no hits must
 * not, because "be the first" in front of a book of fifty entries reads as the
 * application having lost them.
 */
export function describeEmpty(search: string): string {
  return search === '' ? 'No entries yet. Be the first.' : 'Nothing matches that search.'
}

/**
 * `Load 4 more` -- and never a number bigger than what is actually left.
 *
 * The button promising four when one remains is a small lie that the very next
 * click exposes, and it is exposed by the button disappearing, which reads as a
 * failure rather than as the end of the list.
 */
export function loadMoreLabel(remaining: number, step: number): string {
  return `Load ${Math.min(remaining, step)} more`
}
