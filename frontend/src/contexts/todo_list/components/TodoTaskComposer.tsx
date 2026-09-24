import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'

import { normalizeText } from '@/lib/text'

import { TODO_TASK_TEXT_REFUSALS, todoTaskTextVerdict } from '../lib/todoTask'
import type { RefusedText } from '../lib/todoTask'

/**
 * The add field: one line and "Add task", in a white card
 * (`spec/design/ui/todo-list.md` § The add field).
 *
 * **Nothing stops input at a length.** No `maxLength`, no counter, no cut: a
 * `maxLength` counts UTF-16 code units, so on a text of emoji it stops at half the
 * bound -- the guestbook's defect (`D-04`), one context over. The field holds
 * whatever is typed or pasted, and the rule decides, in the unit the service
 * counts in; the sentence under the field is the bound.
 *
 * **The rule is the service's, applied before sending** (`BR-06`, `BR-07`), from
 * `lib/todoTask.ts`, and what is sent is the text as the shared rule leaves it --
 * normalized and trimmed -- so the screen judged the very string the service will
 * store. The sentence for the one reason a text is refused appears once the field
 * has been left or Enter pressed, never while typing, and goes as soon as the text
 * passes. Until then "Add task" is simply closed, and the empty field's placeholder
 * says what it is waiting for.
 *
 * **Enter is handled on the key, not by a form's implicit submission**, because a
 * form does not submit through a closed button -- and Enter on a refused text has
 * to say why rather than do nothing.
 *
 * The field carries no visible label, matching the mock-up; it is named "New task"
 * for everything that is not looking at the page.
 */
export interface TodoTaskComposerProps {
  /** An accepted text, as the shared rule leaves it. */
  onSubmit: (values: { text: string }) => void
  /** True while an add travels: the field and the button lock, the text stays. */
  isPending?: boolean
  /**
   * How many tasks this field has added. When it grows, the add went through and
   * the field empties itself for the next one; a failed add leaves the text where
   * it was, because retrying otherwise means typing it again.
   */
  addedCount?: number
  /** The service refused the text it was sent: its sentence stands under the field while it holds that text. */
  refusal?: RefusedText
}

export function TodoTaskComposer({
  onSubmit,
  isPending = false,
  addedCount = 0,
  refusal,
}: TodoTaskComposerProps) {
  const errorId = useId()
  const cardRef = useRef<HTMLDivElement>(null)
  const fieldRef = useRef<HTMLInputElement>(null)
  const [text, setText] = useState('')
  const [shown, setShown] = useState(false)

  // Emptied during the render in which the count grows, so the field is never
  // drawn for a frame still holding the task that was just added.
  const [seenAdded, setSeenAdded] = useState(addedCount)
  if (addedCount !== seenAdded) {
    setSeenAdded(addedCount)
    setText('')
    setShown(false)
  }

  const verdict = todoTaskTextVerdict(text)
  const sent = normalizeText(text)
  const sentence =
    shown && verdict !== 'accepted'
      ? TODO_TASK_TEXT_REFUSALS[verdict]
      : refusal !== undefined && refusal.text === sent
        ? refusal.sentence
        : undefined
  const canAdd = verdict === 'accepted' && !isPending

  /**
   * After any add, whether it went through or not, the focus goes back in the
   * field (`Q-16`) -- so the next task can be typed at once, or the text that
   * stayed sent again. Only when the add was sent from this card and the focus has
   * not been put somewhere else since: the field and the button lock while the add
   * travels, and a locked control lets go of the focus.
   */
  const hadFocus = useRef(false)
  const wasPending = useRef(isPending)
  useEffect(() => {
    if (wasPending.current && !isPending && hadFocus.current) {
      const active = document.activeElement
      const free =
        active === null ||
        active === document.body ||
        (cardRef.current?.contains(active) ?? false)
      if (free) fieldRef.current?.focus()
      hadFocus.current = false
    }
    wasPending.current = isPending
  }, [isPending])

  function submit() {
    if (isPending) return
    if (verdict !== 'accepted') {
      setShown(true)
      return
    }
    hadFocus.current = cardRef.current?.contains(document.activeElement) ?? false
    onSubmit({ text: sent })
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Enter' || event.nativeEvent.isComposing) return
    event.preventDefault()
    submit()
  }

  return (
    <section className="pt-7 pb-5">
      <div
        ref={cardRef}
        className="flex flex-col gap-2 rounded-card border border-hairline bg-card py-3 pr-3 pl-4.5"
      >
        <div className="flex items-center gap-3">
          <input
            ref={fieldRef}
            type="text"
            aria-label="New task"
            placeholder="What needs doing?"
            autoComplete="off"
            value={text}
            disabled={isPending}
            aria-invalid={sentence !== undefined}
            aria-describedby={sentence !== undefined ? errorId : undefined}
            onChange={(event) => {
              const next = event.target.value
              setText(next)
              if (todoTaskTextVerdict(next) === 'accepted') setShown(false)
            }}
            onBlur={() => setShown(verdict !== 'accepted')}
            onKeyDown={handleKeyDown}
            className="min-w-0 flex-1 border-0 bg-transparent p-0 text-base leading-6 text-ink disabled:cursor-progress disabled:text-muted"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!canAdd}
            className="shrink-0 cursor-pointer rounded-control border-0 bg-accent px-5 py-2.5 text-sm font-medium text-inverse enabled:hover:brightness-112 disabled:cursor-not-allowed disabled:opacity-35"
          >
            {isPending ? 'Adding…' : 'Add task'}
          </button>
        </div>
        {sentence !== undefined && (
          <span id={errorId} role="alert" className="text-xs font-medium text-danger">
            {sentence}
          </span>
        )}
      </div>
    </section>
  )
}
