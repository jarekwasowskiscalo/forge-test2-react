import { useState } from 'react'

import { cn } from '@/lib/cn'
import { timeAgo } from '@/lib/relativeTime'
import {
  ENTRY_PROBLEM_MESSAGES,
  authorProblem,
  canSubmitEntry,
  messageProblem,
  normalizeEntryField,
  wasEdited,
} from '@/contexts/guestbook/lib/guestbookEntry'
import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

/**
 * One entry, and the two things anybody may do to it.
 *
 * **An edit happens here rather than in a form at the top of the page.** The
 * words being corrected stay where they were being read, and the list does not
 * scroll out from under the person correcting them. Anybody may edit and delete
 * anybody's entry -- there is no identity in this product, so there is no such
 * thing as "my entry" (`spec/contexts/guestbook.md` § Deliberate non-goals).
 *
 * "edited" is derived from comparing the two instants (`BR-02`), never read
 * from a flag: a stored flag is a second thing that has to be kept true.
 */
export interface EntryCardProps {
  entry: GuestbookEntry
  isEditing: boolean
  onEditStart: () => void
  onEditCancel: () => void
  onSave: (values: { author: string; message: string }) => void
  onDelete: () => void
  /** True while this entry's own write is in flight. */
  isSaving?: boolean
  /**
   * True while **any** entry's amendment is in flight, this one's included.
   *
   * "Edit" is closed while one is, and that is a decision rather than caution.
   * Opening a second editor mid-save moved the editor out from under the save:
   * the answer then closed whichever editor happened to be open, and the
   * "Saving…" marker followed it, so the entry actually being written stopped
   * being marked as written. One editor at a time is what the screen already
   * promises; this is what makes the promise hold while a write is in the air.
   */
  isSaveInFlight?: boolean
  isDeleting?: boolean
}

const ACTION =
  'cursor-pointer border-0 bg-transparent p-0 text-meta text-faint disabled:cursor-default disabled:opacity-50'

export function EntryCard({
  entry,
  isEditing,
  onEditStart,
  onEditCancel,
  onSave,
  onDelete,
  isSaving = false,
  isSaveInFlight = false,
  isDeleting = false,
}: EntryCardProps) {
  return (
    <article className="animate-rise rounded-card border border-hairline bg-card px-5 pt-5 pb-4.5">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-2.5">
          <span className="text-body font-semibold tracking-[-0.01em]">{entry.author}</span>
          {/* The machine-readable instant sits in `dateTime`, so the age in
              words never becomes the only record of when this was written. */}
          <time dateTime={entry.created_at} className="text-xs text-faint">
            {timeAgo(entry.created_at)}
            {wasEdited(entry) && ' · edited'}
          </time>
        </div>
        <div className="flex gap-3.5">
          <button
            type="button"
            onClick={onEditStart}
            disabled={isEditing || isDeleting || isSaveInFlight}
            className={cn(ACTION, 'hover:text-accent')}
          >
            {isEditing ? 'Editing' : 'Edit'}
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={isDeleting}
            className={cn(ACTION, 'hover:text-danger')}
          >
            {isDeleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>

      {isEditing ? (
        <EntryEditor
          // Remounted per entry, so opening an edit always starts from what
          // that entry currently holds rather than from the last one's text.
          key={entry.id}
          entry={entry}
          isSaving={isSaving}
          onSave={onSave}
          onCancel={onEditCancel}
        />
      ) : (
        <p className="mt-2.5 mb-0 text-base leading-relaxed whitespace-pre-wrap text-pretty">
          {entry.message}
        </p>
      )}
    </article>
  )
}

interface EntryEditorProps {
  entry: GuestbookEntry
  isSaving: boolean
  onSave: (values: { author: string; message: string }) => void
  onCancel: () => void
}

/**
 * The two fields, open over the entry they belong to.
 *
 * Not exported: an editor with no entry under it is not a thing this screen
 * has, and a component nobody can construct wrongly is one nobody has to be
 * told how to construct.
 *
 * The same rules as the composer, from the same module. Save is closed while
 * either field is empty, so an edit cannot do what a new entry is forbidden
 * from doing -- `BR-01` is about entries, not about how they arrived.
 */
function EntryEditor({ entry, isSaving, onSave, onCancel }: EntryEditorProps) {
  const [author, setAuthor] = useState(entry.author)
  const [message, setMessage] = useState(entry.message)

  const authorIssue = authorProblem(author)
  const messageIssue = messageProblem(message)
  const canSave = canSubmitEntry(author, message) && !isSaving

  return (
    <div className="mt-3.5 flex flex-col gap-3">
      <input
        aria-label="Edit name"
        value={author}
        disabled={isSaving}
        onChange={(event) => setAuthor(event.target.value)}
        aria-invalid={authorIssue !== undefined}
        className="rounded-control-tight border border-hairline px-3 py-2.5 text-sm font-medium text-ink"
      />
      <textarea
        aria-label="Edit message"
        value={message}
        rows={3}
        disabled={isSaving}
        onChange={(event) => setMessage(event.target.value)}
        aria-invalid={messageIssue !== undefined}
        className="resize-y rounded-control-tight border border-hairline px-3 py-2.5 font-sans text-body leading-[1.55] text-ink"
      />
      {/* One sentence at a time, and only once a field has actually been
          emptied. Two red lines under two fields somebody has not finished
          editing is the noise the composer's blur rule exists to avoid. */}
      {(authorIssue ?? messageIssue) !== undefined && (
        <span role="alert" className="text-xs font-medium text-danger">
          {ENTRY_PROBLEM_MESSAGES[(authorIssue ?? messageIssue)!]}
        </span>
      )}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={!canSave}
          onClick={() =>
            onSave({
              author: normalizeEntryField(author),
              message: normalizeEntryField(message),
            })
          }
          className="cursor-pointer rounded-control-tight border-0 bg-accent px-4 py-2 text-meta font-medium text-inverse hover:brightness-115 disabled:cursor-not-allowed disabled:opacity-35"
        >
          {isSaving ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="cursor-pointer rounded-control-tight border border-hairline bg-transparent px-4 py-2 text-meta text-muted hover:bg-surface-medium"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
