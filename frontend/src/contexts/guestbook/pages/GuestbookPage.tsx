import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { describeProblem, problemOf } from '@/api/problem'
import { DeleteEntryDialog } from '@/contexts/guestbook/components/DeleteEntryDialog'
import { EntryCard } from '@/contexts/guestbook/components/EntryCard'
import { EntryComposer } from '@/contexts/guestbook/components/EntryComposer'
import { EntryToolbar } from '@/contexts/guestbook/components/EntryToolbar'
import { PageFrame } from '@/components/shell/PageFrame'
import { GUESTBOOK_ROUTE } from '@/routes'
import { ErrorState, Skeleton } from '@/components/ui/Feedback'
import { useToast } from '@/components/ui/Toast'
import { useEntryQueryParams } from '@/contexts/guestbook/hooks/useEntryQueryParams'
import {
  useCreateGuestbookEntry,
  useDeleteGuestbookEntry,
  useGuestbookEntries,
  useUpdateGuestbookEntry,
} from '@/contexts/guestbook/hooks/useGuestbookEntries'
import {
  READ_FAILED_LABEL,
  describeEmpty,
  describeResult,
  entryCountLabel,
  loadMoreLabel,
} from '@/contexts/guestbook/lib/entryListCopy'
import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

/**
 * `S-01` -- the only screen in this application.
 *
 * One column: write at the top, narrow in the middle, read below. Four
 * operations and no second address for any of them -- a guest book is one thing
 * a person looks at, and an edit on its own URL would be a screen that exists
 * only to hold a form the card already has room for.
 *
 * Every request's failure is shown where the request was started: the list's
 * failure replaces the list, a write's failure is a toast over a card that still
 * holds what was typed. A write that loses the text on failure is a write people
 * do not retry.
 */

/** How many entries the first page shows, and how many "Load more" adds. */
const PAGE_STEP = 4

/** How long the search box waits for typing to stop before it asks the server. */
const SEARCH_SETTLE_MS = 250

export function GuestbookPage() {
  /**
   * The question lives in the address, not in this component
   * (`spec/design/conventions.md` § Frontend). A result nobody can link to is a
   * result nobody can send, and a search that a refresh forgets is a search
   * somebody has to type twice.
   */
  const { typed, search, sort, shown, onSearchChange, onSortChange, onShownChange } =
    useEntryQueryParams(PAGE_STEP, SEARCH_SETTLE_MS)

  const [editingId, setEditingId] = useState<string | undefined>(undefined)
  const [confirmingDelete, setConfirmingDelete] = useState<GuestbookEntry | undefined>(undefined)

  /**
   * Bumped after every **successful** add, to remount the composer empty.
   *
   * A counter rather than clearing the fields, because the composer owns its own
   * inputs and their touched state -- clearing from the outside would need this
   * page to hold all of it, which is the coupling `EntryComposer` exists to
   * avoid. Only on success, deliberately: a failed write must leave the text
   * where it was, because retrying otherwise means typing it again.
   */
  const [writes, setWrites] = useState(0)

  const navigate = useNavigate()
  const page = useGuestbookEntries({ search, sort }, { shown, step: PAGE_STEP })
  const create = useCreateGuestbookEntry()
  const update = useUpdateGuestbookEntry()
  const remove = useDeleteGuestbookEntry()
  const toast = useToast()

  const entries = page.data?.entries ?? []
  const total = page.data?.total ?? 0
  const totalAll = page.data?.totalAll ?? 0

  /**
   * The list on screen answers an older question than the address does.
   *
   * `keepPreviousData` is what puts it there, and saying so is the other half of
   * that decision: entries kept on screen without a word about it are entries
   * the screen is passing off as the answer to the phrase in the box.
   */
  const isStale = page.isPlaceholderData
  const remaining = total - entries.length

  function reportFailure(error: unknown) {
    toast.push(describeProblem(problemOf(error)).detail, 'error')
  }

  function handleCreate(values: { author: string; message: string }) {
    create.mutate(values, {
      onSuccess: () => {
        setWrites((count) => count + 1)
        // Back to the top of an unfiltered book, because that is where the entry
        // just written is -- posting into a search that does not match it would
        // otherwise look like the write having failed. The navigation alone:
        // the search box follows the address now, so clearing it by hand here
        // would be a second way of saying the same thing, and the two could
        // disagree. It used to need both, which was the coupling showing.
        navigate(GUESTBOOK_ROUTE, { replace: true })
        toast.push('Entry posted.', 'success')
      },
      onError: reportFailure,
    })
  }

  function handleSave(entry: GuestbookEntry, values: { author: string; message: string }) {
    update.mutate(
      { id: entry.id, body: values },
      {
        onSuccess: () => {
          // Only the editor that sent this save, the way the delete path below
          // has always done it: an answer to one operation must not close an
          // editor somebody opened over a different entry in the meantime.
          setEditingId((current) => (current === entry.id ? undefined : current))
          toast.push('Entry updated.', 'success')
        },
        onError: reportFailure,
      },
    )
  }

  function handleConfirmDelete() {
    if (confirmingDelete === undefined) return
    const doomed = confirmingDelete
    remove.mutate(doomed.id, {
      onSuccess: () => {
        // An entry being edited that somebody just deleted would leave the
        // editor writing to an id that no longer resolves, and the save would
        // refuse with a 404 nobody could act on.
        if (editingId === doomed.id) setEditingId(undefined)
        setConfirmingDelete(undefined)
        toast.push('Entry deleted.', 'success')
      },
      onError: (error) => {
        setConfirmingDelete(undefined)
        reportFailure(error)
      },
    })
  }

  return (
    <PageFrame
      title="Leave a note"
      lede="No account, no sign-in. Write something, and it appears below straight away. Anyone can edit or remove an entry."
      meta={page.isSuccess ? entryCountLabel(totalAll) : undefined}
    >
      <EntryComposer key={`new-${writes}`} onSubmit={handleCreate} isPending={create.isPending} />

      <EntryToolbar
        search={typed}
        onSearchChange={onSearchChange}
        sort={sort}
        onSortChange={onSortChange}
        isStale={isStale}
        resultLabel={
          page.isError
            ? READ_FAILED_LABEL
            : page.data !== undefined
              ? describeResult({
                  // The phrase the numbers came back for, which is not the one
                  // in the address until the screen has settled.
                  search: page.data.answering.search,
                  shown: entries.length,
                  total,
                  settled: !isStale,
                })
              : ' '
        }
      />

      {page.isPending && <EntrySkeletons count={PAGE_STEP} />}

      {page.isError && (
        <ErrorState problem={problemOf(page.error)} onRetry={() => void page.refetch()} />
      )}

      {page.data !== undefined && !page.isError && (
        <>
          <section className="flex flex-col gap-3" aria-busy={isStale}>
            {entries.map((entry) => (
              <EntryCard
                key={entry.id}
                entry={entry}
                isEditing={editingId === entry.id}
                onEditStart={() => setEditingId(entry.id)}
                onEditCancel={() => setEditingId(undefined)}
                onSave={(values) => handleSave(entry, values)}
                onDelete={() => setConfirmingDelete(entry)}
                // Bound to the operation, not to whichever editor is open: the
                // marker belongs on the entry whose PATCH is actually in flight.
                isSaving={update.isPending && update.variables?.id === entry.id}
                isSaveInFlight={update.isPending}
                isDeleting={remove.isPending && confirmingDelete?.id === entry.id}
              />
            ))}
          </section>

          {entries.length === 0 && (
            <div className="rounded-card border border-dashed border-line px-5 py-14 text-center text-body text-muted">
              {describeEmpty(search)}
            </div>
          )}

          {page.hasNextPage === true && !isStale && (
            <div className="flex justify-center pt-7">
              <button
                type="button"
                onClick={() => onShownChange(entries.length + PAGE_STEP)}
                className="cursor-pointer rounded-control border border-hairline bg-card px-5.5 py-2.5 text-sm text-ink hover:border-accent hover:text-accent"
              >
                {loadMoreLabel(remaining, PAGE_STEP)}
              </button>
            </div>
          )}
        </>
      )}

      {confirmingDelete !== undefined && (
        <DeleteEntryDialog
          entry={confirmingDelete}
          isPending={remove.isPending}
          onConfirm={handleConfirmDelete}
          onCancel={() => setConfirmingDelete(undefined)}
        />
      )}
    </PageFrame>
  )
}

/**
 * Cards in outline while the first page loads.
 *
 * Card-shaped and not a spinner, because the height is reserved: the content
 * does not jump under the cursor at the moment it arrives. A spinner over an
 * empty column would also be indistinguishable from a book with nothing in it,
 * which is the one thing this screen has to be able to say clearly.
 */
function EntrySkeletons({ count }: { count: number }) {
  return (
    <div className="flex flex-col gap-3" role="status" aria-label="Loading entries">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="rounded-card border border-hairline bg-card px-5 py-5">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="mt-3.5 h-2.5 w-full" />
          <Skeleton className="mt-2 h-2.5 w-4/5" />
        </div>
      ))}
    </div>
  )
}
