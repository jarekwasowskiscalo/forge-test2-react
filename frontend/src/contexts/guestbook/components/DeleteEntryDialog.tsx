import { useRef } from 'react'

import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

/**
 * The confirmation before an entry is destroyed.
 *
 * **The mock-up deletes on the first click and this does not**, deliberately.
 * Deleting is irreversible (`BR-03`), anybody may delete anybody's entry, and
 * the button that starts it sits a few pixels from "Edit". A mock-up is a
 * drawing of a layout; it is not a decision to remove the only warning a person
 * gets.
 *
 * The dialog quotes the entry back rather than asking "are you sure?" about an
 * unnamed thing: the cards differ only by their text, so a confirmation that
 * does not name what it will destroy cannot be answered correctly.
 *
 * Focus lands on Cancel, not on the destructive action -- an Enter pressed out
 * of habit should not delete anything.
 */
export interface DeleteEntryDialogProps {
  entry: GuestbookEntry
  onConfirm: () => void
  onCancel: () => void
  isPending?: boolean
}

export function DeleteEntryDialog({
  entry,
  onConfirm,
  onCancel,
  isPending = false,
}: DeleteEntryDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  return (
    <Modal
      title="Delete this entry?"
      // Undismissable once the request is in flight: there is nothing left to
      // cancel, and a backdrop press would only hide what is still happening.
      onDismiss={isPending ? undefined : onCancel}
      initialFocusRef={cancelRef}
      footer={
        <>
          <span className="text-xs text-muted">This cannot be undone.</span>
          <div className="ml-auto flex gap-2">
            <Button ref={cancelRef} variant="quiet" onClick={onCancel} disabled={isPending}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onConfirm} disabled={isPending}>
              {isPending ? 'Deleting…' : 'Delete entry'}
            </Button>
          </div>
        </>
      }
    >
      <p className="text-sm">
        <b>{entry.author}</b> wrote:
      </p>
      <p className="mt-2 rounded-xl bg-surface px-3 py-2.5 text-sm whitespace-pre-wrap">
        {entry.message}
      </p>
    </Modal>
  )
}
