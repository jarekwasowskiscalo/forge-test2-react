import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent, RefObject } from 'react'

import { Checkbox } from '@/components/ui/Checkbox'
import { cn } from '@/lib/cn'
import { normalizeText } from '@/lib/text'

import { TODO_TASK_TEXT_REFUSALS, todoTaskTextVerdict } from '../lib/todoTask'
import type { RefusedText, TodoTask } from '../lib/todoTask'
import { DeleteTodoTaskDialog } from './DeleteTodoTaskDialog'

/**
 * One task: its box, its text drawn done or not done, its correction in place,
 * and the one question before it is deleted (`spec/design/ui/todo-list.md` § A
 * task's row).
 *
 * **Done shows three ways at once** -- the box filled and ticked, the text struck
 * through in `--color-muted`, and the checked state assistive technology reads --
 * so colour is never the only carrier (`BR-09`). The done text is never greyed with
 * `--color-disabled` or with opacity: it measures 7.09:1 on the card and stays
 * exactly as readable as any other text, which is the contrast defect
 * `spec/design/ui/system-states.md` § Tokens records, kept out of this screen.
 *
 * **A tick sends the state the person chose, and the box goes on showing what is
 * stored until the answer.** The box is a controlled input over `task.done`, so a
 * press asks for the other state and changes nothing on screen by itself; while the
 * tick travels the box is locked on the stored state with "Saving…" beside it, and
 * when the list is read again it shows what the service stored (`R-10`).
 *
 * **Which row is being edited is the page's**, because at most one editor is ever
 * open and a row cannot see its neighbours -- the guestbook card's arrangement. The
 * row asks to start and to stop, and draws what it is told.
 *
 * **The delete question is the row's.** It exists only on the screen, it is about
 * this task alone, and nothing is sent until it is answered (`R-7`). The page is
 * told only the answer, and tells the row back while the deletion travels; the
 * question closes once the deletion itself has been answered, either way -- on the
 * promise `onDelete` returns, not on watching `isDeleting` rise and fall, because
 * a deletion answered before the screen drew it travelling never rises at all.
 *
 * **The focus goes back where the person was** (`Q-16`): a locked control lets go
 * of it, so when the answer comes it is put back -- on the box after a tick, in the
 * edit field after a correction that did not go through, on "Edit" when the editor
 * closes, on "Delete" when the question closes -- but only when it was on the
 * control that was locked and nobody has moved it since. A person who put the
 * focus somewhere else meanwhile keeps it where they put it.
 */
export interface TodoTaskRowProps {
  task: TodoTask
  /** True when this row's editor is the one open on the screen. */
  isEditing: boolean
  onEditStart: () => void
  onEditCancel: () => void
  /** A correction: the new text alone, as the shared rule leaves it. */
  onSave: (values: { text: string }) => void
  /** A tick: the state chosen, alone. */
  onMark: (values: { done: boolean }) => void
  /**
   * The question was answered "Delete task". When it returns a promise, the
   * question closes once that promise settles -- the deletion's answer, whichever
   * way it went; the notice saying so is the caller's.
   */
  onDelete: () => void | Promise<unknown>
  /** True while this task's tick travels. */
  isMarking?: boolean
  /** True while this task's correction travels. */
  isSaving?: boolean
  /**
   * True while **any** task's correction travels, this one's included. "Edit" is
   * locked on every row meanwhile, so the answer can only close the editor that
   * sent it -- the guestbook card's lock, for the reason its docstring gives.
   */
  isSaveInFlight?: boolean
  /** True while this task's deletion travels. */
  isDeleting?: boolean
  /** The service refused a correction's text: shown under the edit field while it holds that text. */
  saveRefusal?: RefusedText
  /** True for a row that has just arrived by an add: it plays the frame's one entry animation. */
  isArriving?: boolean
}

/** The quiet text buttons on the right: `--color-faint`, 5.40:1 on the card. */
const ACTION =
  'cursor-pointer border-0 bg-transparent p-0 text-meta leading-6 text-faint disabled:cursor-default disabled:opacity-50'

export function TodoTaskRow({
  task,
  isEditing,
  onEditStart,
  onEditCancel,
  onSave,
  onMark,
  onDelete,
  isMarking = false,
  isSaving = false,
  isSaveInFlight = false,
  isDeleting = false,
  saveRefusal,
  isArriving = false,
}: TodoTaskRowProps) {
  const boxId = useId()
  const rowRef = useRef<HTMLLIElement>(null)
  const boxRef = useRef<HTMLInputElement>(null)
  const editRef = useRef<HTMLButtonElement>(null)
  const deleteRef = useRef<HTMLButtonElement>(null)

  const [asking, setAsking] = useState(false)

  function confirmDelete() {
    const answered = onDelete()
    // Closed from the same chain of promises the caller's notice is pushed in, so
    // both land in one commit: a notice inserted while the question still made the
    // page behind it inert is a notice nobody hears (`Modal.tsx`, the reason its
    // own effect is a layout one).
    const close = () => setAsking(false)
    if (answered !== undefined) void answered.then(close, close)
  }

  /** Whether the tick in flight was sent from the box while it had the focus. */
  const boxHadFocus = useRef(false)
  const focusIsFree = () => focusIsFreeWithin(rowRef)

  useWhenSettled(isMarking, () => {
    if (boxHadFocus.current && focusIsFree()) boxRef.current?.focus()
    boxHadFocus.current = false
  })
  useWhenSettled(isEditing, () => {
    // The editor closed on "Save" or "Cancel". Closed because another row's
    // "Edit" was pressed, the focus is already in that row's editor.
    if (focusIsFree()) editRef.current?.focus()
  })
  /**
   * The Modal hands the focus back to "Delete" itself, except when "Delete" is
   * still locked at that moment -- the question can close before the page has
   * drawn the deletion as over -- so it is handed over here once the button can
   * take it, unless the person has put the focus somewhere else meanwhile.
   */
  const focusBackToDelete = useRef(false)
  useWhenSettled(asking, () => {
    focusBackToDelete.current = true
  })
  useEffect(() => {
    if (!focusBackToDelete.current || isDeleting) return
    focusBackToDelete.current = false
    if (focusIsFree()) deleteRef.current?.focus()
  })

  const editWord = isEditing ? 'Editing' : 'Edit'
  const deleteWord = isDeleting ? 'Deleting…' : 'Delete'

  return (
    <li
      ref={rowRef}
      className={cn('flex items-start gap-4 px-5 py-3.5', isArriving && 'motion-safe:animate-rise')}
    >
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <Checkbox
          ref={boxRef}
          id={boxId}
          checked={task.done}
          disabled={isMarking}
          // While the row is editing, the text that labels the box is replaced by
          // the edit field, so the stored text names the box instead.
          aria-label={isEditing ? task.text : undefined}
          onChange={(event) => {
            boxHadFocus.current = document.activeElement === event.currentTarget
            onMark({ done: event.currentTarget.checked })
          }}
        />
        {isEditing ? (
          <TodoTaskEditor
            // Remounted per task, so an editor always starts from what that task
            // holds now rather than from the last one's text.
            key={task.id}
            task={task}
            isSaving={isSaving}
            refusal={saveRefusal}
            onSave={onSave}
            onCancel={onEditCancel}
          />
        ) : (
          <label
            htmlFor={boxId}
            className={cn(
              'min-w-0 cursor-pointer text-base leading-6 wrap-anywhere',
              task.done ? 'text-muted line-through' : 'text-ink',
            )}
          >
            {task.text}
          </label>
        )}
      </div>

      {isMarking && <span className="shrink-0 text-meta leading-6 text-faint">Saving…</span>}

      <span className="flex shrink-0 gap-3.5">
        <button
          ref={editRef}
          type="button"
          onClick={onEditStart}
          disabled={isEditing || isSaveInFlight || isDeleting}
          aria-label={`${editWord} “${task.text}”`}
          className={cn(ACTION, 'enabled:hover:text-accent')}
        >
          {editWord}
        </button>
        <button
          ref={deleteRef}
          type="button"
          onClick={() => setAsking(true)}
          disabled={isDeleting}
          aria-label={`${deleteWord} “${task.text}”`}
          className={cn(ACTION, 'enabled:hover:text-danger')}
        >
          {deleteWord}
        </button>
      </span>

      {asking && (
        <DeleteTodoTaskDialog
          task={task}
          isPending={isDeleting}
          onConfirm={confirmDelete}
          onCancel={() => setAsking(false)}
        />
      )}
    </li>
  )
}

interface TodoTaskEditorProps {
  task: TodoTask
  isSaving: boolean
  refusal: RefusedText | undefined
  onSave: (values: { text: string }) => void
  onCancel: () => void
}

/**
 * The edit field, open in the row over the text it replaces, with "Save" and
 * "Cancel" under it.
 *
 * Not exported: an editor with no task under it is not a thing this screen has.
 *
 * The same rule as the add field, from the same module, so a correction cannot do
 * what a new task is forbidden from doing (`R-6` clause 4). The rule's sentence
 * appears once the field is left or Enter is pressed, never while typing, and goes
 * as soon as the text passes. **Escape does nothing here**: a stray key must not
 * lose an edit.
 */
function TodoTaskEditor({ task, isSaving, refusal, onSave, onCancel }: TodoTaskEditorProps) {
  const errorId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const fieldRef = useRef<HTMLInputElement>(null)
  const [text, setText] = useState(task.text)
  const [shown, setShown] = useState(false)

  const verdict = todoTaskTextVerdict(text)
  const sent = normalizeText(text)
  const sentence =
    shown && verdict !== 'accepted'
      ? TODO_TASK_TEXT_REFUSALS[verdict]
      : refusal !== undefined && refusal.text === sent
        ? refusal.sentence
        : undefined
  const canSave = verdict === 'accepted' && !isSaving

  /** Whether the correction in flight was sent while the focus was in this editor. */
  const hadFocus = useRef(false)
  useWhenSettled(isSaving, () => {
    // Still open, so the correction did not go through: back in the field, with
    // what was typed, to be sent again or cancelled.
    if (hadFocus.current && focusIsFreeWithin(containerRef)) fieldRef.current?.focus()
    hadFocus.current = false
  })

  function save() {
    if (isSaving) return
    if (verdict !== 'accepted') {
      setShown(true)
      return
    }
    hadFocus.current = containerRef.current?.contains(document.activeElement) ?? false
    onSave({ text: sent })
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Enter' || event.nativeEvent.isComposing) return
    event.preventDefault()
    save()
  }

  return (
    <div ref={containerRef} className="flex min-w-0 flex-1 flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <input
          ref={fieldRef}
          type="text"
          aria-label="Edit task"
          autoComplete="off"
          // The editor opens because the person asked for it, and the focus goes
          // where the words are.
          autoFocus
          value={text}
          disabled={isSaving}
          aria-invalid={sentence !== undefined}
          aria-describedby={sentence !== undefined ? errorId : undefined}
          onChange={(event) => {
            const next = event.target.value
            setText(next)
            if (todoTaskTextVerdict(next) === 'accepted') setShown(false)
          }}
          onBlur={() => setShown(verdict !== 'accepted')}
          onKeyDown={handleKeyDown}
          className="w-full rounded-control-tight border border-hairline bg-card px-3 py-2 text-base leading-6 text-ink disabled:bg-surface"
        />
        {sentence !== undefined && (
          <span id={errorId} role="alert" className="text-xs font-medium text-danger">
            {sentence}
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={save}
          disabled={!canSave}
          className="cursor-pointer rounded-control-tight border-0 bg-accent px-4 py-2 text-meta font-medium text-inverse enabled:hover:brightness-112 disabled:cursor-not-allowed disabled:opacity-35"
        >
          {isSaving ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="cursor-pointer rounded-control-tight border border-hairline bg-transparent px-4 py-2 text-meta text-muted enabled:hover:bg-surface-medium disabled:cursor-default disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

/**
 * Runs `settle` after the commit in which `flag` falls from true to false -- when
 * the answer to a write has come and the control it locked is usable again.
 */
function useWhenSettled(flag: boolean, settle: () => void): void {
  const previous = useRef(flag)
  useEffect(() => {
    if (previous.current && !flag) settle()
    previous.current = flag
  })
}

/**
 * Whether the focus may be put back: it was dropped (it rests on the page itself,
 * which is where a locked or removed control leaves it) or it is still inside the
 * part of the screen that was locked. Anywhere else, the person put it there.
 */
function focusIsFreeWithin(region: RefObject<HTMLElement | null>): boolean {
  const active = document.activeElement
  if (active === null || active === document.body) return true
  return region.current?.contains(active) ?? false
}
