import { useEffect, useRef } from 'react'

import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'

import type { TodoTask } from '../lib/todoTask'

/**
 * The one question before a task is deleted (`R-7`,
 * `spec/design/ui/todo-list.md` § The delete question).
 *
 * Deleting is permanent -- a deleted task is gone, with no undo anywhere
 * (`BR-13`) -- anybody may delete any task, and "Delete" sits a few pixels from
 * "Edit". So nothing is sent until the person has answered, and the question
 * **quotes the task it is about**: rows differ only by their text, so a question
 * that does not name what it will destroy cannot be answered correctly.
 *
 * The focus starts on "Cancel", so an Enter pressed out of habit deletes nothing,
 * and Tab stays inside the question -- the guestbook's delete dialog and its focus
 * rules, as they are, over the same `Modal` primitive.
 *
 * **While the deletion travels the question cannot be closed**: both buttons are
 * locked, "Deleting…" says why, and Escape and a press on the backdrop do nothing
 * -- there is nothing left to cancel, and closing would only hide what is still
 * happening. The focus rests on the question itself meanwhile, because a locked
 * button lets go of it and it must not fall behind the question onto a page the
 * question is covering.
 */
export interface DeleteTodoTaskDialogProps {
  task: TodoTask
  onConfirm: () => void
  onCancel: () => void
  /** True while this task's deletion travels. */
  isPending?: boolean
}

export function DeleteTodoTaskDialog({
  task,
  onConfirm,
  onCancel,
  isPending = false,
}: DeleteTodoTaskDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const quoteRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    if (!isPending) return
    // The dialog container is the Modal's own, focusable by design (it catches
    // the focus a locked control drops); reached from inside rather than through
    // a new prop on a primitive that has one other caller.
    quoteRef.current?.closest<HTMLElement>('[role="dialog"]')?.focus()
  }, [isPending])

  return (
    <Modal
      title="Delete this task?"
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
              {isPending ? 'Deleting…' : 'Delete task'}
            </Button>
          </div>
        </>
      }
    >
      {/* The text as stored, in the quotation block; an unbroken run breaks
          anywhere rather than widening the question. */}
      <p ref={quoteRef} className="m-0 rounded-xl bg-surface px-3 py-2.5 text-sm wrap-anywhere">
        {task.text}
      </p>
    </Modal>
  )
}
