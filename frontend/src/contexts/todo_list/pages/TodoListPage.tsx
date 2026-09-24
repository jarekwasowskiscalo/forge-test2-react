import { useEffect, useRef, useState } from 'react'

import { problemOf } from '@/api/problem'
import { PageFrame } from '@/components/shell/PageFrame'
import { ErrorState, Skeleton } from '@/components/ui/Feedback'
import { useToast } from '@/components/ui/Toast'

import { TodoTaskComposer } from '../components/TodoTaskComposer'
import { TodoTaskRow } from '../components/TodoTaskRow'
import {
  useAddTodoTask,
  useCorrectTodoTask,
  useDeleteTodoTask,
  useMarkTodoTask,
  useTodoTasks,
  useTodoTasksBeingMarked,
} from '../hooks/useTodoTasks'
import { TODO_TASK_DONE_NOTICES, todoTaskCountLabel, todoTaskFailure } from '../lib/todoTask'
import type { RefusedText, TodoTask } from '../lib/todoTask'

/**
 * `S-02` -- the one shared to-do list (`spec/design/ui/todo-list.md`,
 * `spec/contexts/todo_list.md` § `P-02`).
 *
 * One column: the add field at the top, the list right under it, newest first,
 * done and not done alike, with nothing to press to see more. Anybody who opens it
 * adds, ticks, corrects and deletes, with no sign-in, because there is no identity
 * here.
 *
 * **Four list states, and the two easy to confuse are told apart.** Loading is
 * rows in outline and no count; empty is a sentence saying how to begin, with no
 * error and `0 tasks`; failed is its own sentence above the shared error card, with
 * no count and never the empty sentence -- a list that could not be read is not a
 * list with nothing in it; and a list whose every task is done is simply the list
 * (`R-3`, `R-10`).
 *
 * **A change is shown as made only once the answer says it was stored**, and the
 * list is read again after every change that went through (`useTodoTasks.ts`).
 * Every failure is told where the write started, in the words the person agreed
 * (§ Copy, `Q-15`): a refusal of a text under its field, everything else in an
 * error notice over a screen that still shows what is stored -- the text typed
 * stays in its field, the box as it was, the row still there.
 *
 * The add field stays usable while the list loads or has failed: adding does not
 * depend on having read the list.
 */
export function TodoListPage() {
  const list = useTodoTasks()
  const add = useAddTodoTask()
  const mark = useMarkTodoTask()
  const correct = useCorrectTodoTask()
  const remove = useDeleteTodoTask()
  const beingMarked = useTodoTasksBeingMarked()
  const toast = useToast()

  /** The row whose editor is open -- at most one, anywhere on the list. */
  const [editingId, setEditingId] = useState<string | undefined>(undefined)
  /** How many tasks the field has added; it empties itself when this grows. */
  const [added, setAdded] = useState(0)
  /** The task the last add stored, which arrives with the frame's entry animation. */
  const [arrivedId, setArrivedId] = useState<string | undefined>(undefined)
  /** Bumped after each deletion that went through, to look after the focus it leaves. */
  const [deletions, setDeletions] = useState(0)

  const listRef = useRef<HTMLUListElement>(null)
  const emptyRef = useRef<HTMLDivElement>(null)

  /**
   * A deleted row takes its question with it, and the focus that was in the
   * question has nowhere to go back to. It goes to the list -- or to the empty
   * sentence, when that was the last task -- and never to the page's start
   * (§ Keyboard and accessibility). After the commit, because the row leaves in a
   * render of its own.
   */
  useEffect(() => {
    if (deletions === 0) return
    const active = document.activeElement
    if (active === null || active === document.body) (listRef.current ?? emptyRef.current)?.focus()
  }, [deletions])

  function tellFailure(error: unknown, write: 'add' | 'change') {
    const failure = todoTaskFailure(problemOf(error), write)
    // A refusal of the text is told under the field that holds it (below), not
    // in a notice as well.
    if (failure.place === 'notice') toast.push(failure.sentence, 'error')
  }

  function handleAdd(values: { text: string }) {
    add.mutate(values, {
      onSuccess: (task) => {
        setAdded((count) => count + 1)
        setArrivedId(task.id)
        toast.push(TODO_TASK_DONE_NOTICES.added, 'success')
      },
      onError: (error) => tellFailure(error, 'add'),
    })
  }

  function handleMark(task: TodoTask, done: boolean) {
    // Per call rather than through `mutate`'s own callbacks: several ticks can
    // travel at once, and those callbacks fire for the last one sent alone. A
    // tick that went through gets no notice -- the box is its own confirmation.
    mark.mutateAsync({ id: task.id, done }).catch((error: unknown) => tellFailure(error, 'change'))
  }

  function handleSave(task: TodoTask, values: { text: string }) {
    correct.mutate(
      { id: task.id, text: values.text },
      {
        onSuccess: () => {
          // Only the editor that sent it: "Edit" is locked everywhere while a
          // correction travels, so it is still this one -- said here anyway,
          // because an answer must never close an editor it did not open.
          setEditingId((current) => (current === task.id ? undefined : current))
          toast.push(TODO_TASK_DONE_NOTICES.corrected, 'success')
        },
        // The editor stays open with what was typed, to be sent again or cancelled.
        onError: (error) => tellFailure(error, 'change'),
      },
    )
  }

  /** Settles once the deletion has been answered -- the row closes its question on it. */
  function handleDelete(task: TodoTask): Promise<void> {
    return remove.mutateAsync(task.id).then(
      () => {
        // A deletion of the row being edited closes its editor with it.
        setEditingId((current) => (current === task.id ? undefined : current))
        setDeletions((count) => count + 1)
        toast.push(TODO_TASK_DONE_NOTICES.deleted, 'success')
      },
      (error: unknown) => tellFailure(error, 'change'),
    )
  }

  const addRefusal = refusedText(add.isError ? add.error : undefined, add.variables?.text, 'add')
  const correctionRefusal = refusedText(
    correct.isError ? correct.error : undefined,
    correct.variables?.text,
    'change',
  )

  return (
    <PageFrame
      title="Things to do"
      lede="No account, no sign-in, one list for everybody. Add what needs doing and tick it off when it is done. Anyone can edit or delete any task."
      meta={list.isSuccess ? todoTaskCountLabel(list.data.total) : undefined}
      footer="Tasks are public and editable by anyone with this link."
    >
      <TodoTaskComposer
        onSubmit={handleAdd}
        isPending={add.isPending}
        addedCount={added}
        refusal={addRefusal}
      />

      {list.isPending && <TodoTaskSkeletons />}

      {list.isError && (
        <>
          <p className="m-0 mb-4 text-meta text-muted">The tasks could not be loaded.</p>
          <ErrorState problem={problemOf(list.error)} onRetry={() => void list.refetch()} />
        </>
      )}

      {list.isSuccess && list.data.items.length === 0 && (
        <div
          ref={emptyRef}
          tabIndex={-1}
          className="rounded-card border border-dashed border-line px-5 py-14 text-center text-body text-muted"
        >
          No tasks yet. Add the first one above.
        </div>
      )}

      {list.isSuccess && list.data.items.length > 0 && (
        // In the order the tasks arrive, sorted by nothing here (`BR-11`): the
        // service settles ties and directions, and a screen that sorted again
        // could only disagree with it. A tick and a correction never move a row.
        <ul
          ref={listRef}
          aria-label="Tasks"
          tabIndex={-1}
          className="m-0 list-none divide-y divide-hairline overflow-hidden rounded-card border border-hairline bg-card p-0"
        >
          {list.data.items.map((task) => (
            <TodoTaskRow
              key={task.id}
              task={task}
              isEditing={editingId === task.id}
              onEditStart={() => setEditingId(task.id)}
              onEditCancel={() => setEditingId(undefined)}
              onSave={(values) => handleSave(task, values)}
              onMark={({ done }) => handleMark(task, done)}
              onDelete={() => handleDelete(task)}
              isMarking={beingMarked.includes(task.id)}
              isSaving={correct.isPending && correct.variables?.id === task.id}
              isSaveInFlight={correct.isPending}
              isDeleting={remove.isPending && remove.variables === task.id}
              saveRefusal={correct.variables?.id === task.id ? correctionRefusal : undefined}
              isArriving={task.id === arrivedId}
            />
          ))}
        </ul>
      )}
    </PageFrame>
  )
}

/**
 * The text a write sent and the service refused, with the service's sentence --
 * or nothing, when the write did not fail on its text.
 */
function refusedText(
  error: Error | undefined,
  text: string | undefined,
  write: 'add' | 'change',
): RefusedText | undefined {
  if (error === undefined || text === undefined) return undefined
  const failure = todoTaskFailure(problemOf(error), write)
  return failure.place === 'field' ? { text, sentence: failure.sentence } : undefined
}

/**
 * Four rows in outline inside the list's card while the list is read.
 *
 * The height is reserved and nothing spins: the content does not jump under the
 * cursor when it arrives, and a spinner over an empty column could not be told
 * from a list with nothing in it -- the one thing this screen has to say clearly.
 */
function TodoTaskSkeletons() {
  const widths = ['w-2/5', 'w-3/5', 'w-1/2', 'w-4/5']
  return (
    <div
      role="status"
      aria-label="Loading tasks"
      className="divide-y divide-hairline overflow-hidden rounded-card border border-hairline bg-card"
    >
      {widths.map((width) => (
        <div key={width} className="flex items-center gap-4 px-5 py-4">
          <Skeleton className="size-5 shrink-0" />
          <Skeleton className={`h-2.5 ${width}`} />
        </div>
      ))}
    </div>
  )
}
