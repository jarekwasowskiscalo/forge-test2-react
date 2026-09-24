import { cn } from '@/lib/cn'
import type { GuestbookEntrySort } from '@/contexts/guestbook/hooks/useGuestbookEntries'

/**
 * How the book is narrowed and which end it is read from.
 *
 * Two controls and one sentence. The sentence is not decoration: with a search
 * running, the number of entries on screen and the number that matched are
 * different, and a screen that shows only the first cannot say whether a short
 * list is a small result or a first page.
 *
 * **Neither control owns any state.** The page holds the phrase and the order,
 * because both belong in the same place as the page size -- changing either has
 * to reset the other two, and three pieces of state in three components is
 * three chances for them to disagree.
 */
export interface EntryToolbarProps {
  search: string
  onSearchChange: (value: string) => void
  sort: GuestbookEntrySort
  onSortChange: (value: GuestbookEntrySort) => void
  /** The line under the controls, from `describeResult`. */
  resultLabel: string
  /**
   * Whether that line is the answer to an older question than the address's.
   *
   * It is the label's own truth, so it is marked in the same region the label
   * lives in rather than somewhere else on the screen: a reader who is told the
   * count and not told it is behind has been told the wrong number.
   */
  isStale: boolean
}

function pill(active: boolean): string {
  return cn(
    'rounded-lg border-0 px-3.5 py-1.5 text-meta cursor-pointer',
    active ? 'bg-ink font-medium text-inverse' : 'bg-transparent text-muted hover:text-ink',
  )
}

export function EntryToolbar({
  search,
  onSearchChange,
  sort,
  onSortChange,
  resultLabel,
  isStale,
}: EntryToolbarProps) {
  return (
    <>
      <section className="flex flex-wrap items-center gap-3 pt-5.5 pb-2">
        <div className="flex flex-1 basis-60 items-center gap-2.5 rounded-control border border-hairline bg-card px-3 py-2.5">
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
            className="shrink-0 text-faint"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" />
          </svg>
          <input
            type="search"
            aria-label="Search entries"
            placeholder="Search entries"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            className="w-full border-0 bg-transparent text-sm text-ink"
          />
        </div>

        {/* A group, not two loose buttons: the pair is one choice, and saying so
            is what lets a screen reader announce "Order, Newest selected"
            instead of two unrelated buttons that happen to sit together. */}
        <div
          role="group"
          aria-label="Order"
          className="flex gap-1 rounded-control border border-hairline bg-card p-0.75"
        >
          <button type="button" aria-pressed={sort === 'newest'} onClick={() => onSortChange('newest')} className={pill(sort === 'newest')}>
            Newest
          </button>
          <button type="button" aria-pressed={sort === 'oldest'} onClick={() => onSortChange('oldest')} className={pill(sort === 'oldest')}>
            Oldest
          </button>
        </div>
      </section>

      {/* Polite, so the count is announced after a search settles rather than
          re-read on every keystroke. `aria-busy` while an answer is on its way:
          the sentence says so in words too, and the attribute is what a reader
          who navigates by region gets without reading it. */}
      <p className="m-0 pt-2.5 pb-4.5 text-meta text-muted" aria-live="polite" aria-busy={isStale}>
        {resultLabel}
      </p>
    </>
  )
}
