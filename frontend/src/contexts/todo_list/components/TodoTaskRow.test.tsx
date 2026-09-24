import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { expect, it, vi } from 'vitest'

import type { TodoTask } from '../lib/todoTask'

/**
 * One task's row: its box, its text drawn done or not done, its correction in
 * place, and the one question before it is deleted.
 *
 * What a row decides, and nothing the page decides:
 *
 * - **done shows three ways at once** -- the box checked, the text struck through
 *   in the muted text colour, and the checked state assistive technology reads --
 *   so colour is never the only carrier, and the done text is never greyed with
 *   opacity or the disabled colour, which is the contrast defect
 *   `spec/design/ui/system-states.md` § Tokens records (`BR-09`, `R-4` clauses 5
 *   and 6);
 * - **a tick sends the state the person chose**, `done` alone, and the box keeps
 *   showing what is stored until the answer (`BR-09`, `R-10`);
 * - **a correction is made in place and sends `text` alone**, and one the rule
 *   refuses is not sent and says why (`BR-06`, `BR-07`, `BR-10`);
 * - **a delete asks first** -- the question and its two answers exist only on the
 *   screen, so this file is the only proof of `R-7` clauses 1 and 3.
 *
 * Which row is being edited is the page's: at most one editor is ever open, and a
 * row cannot know about its neighbours. So the row takes `isEditing` and asks to
 * start or stop, as the guestbook's card does, and the tests below stand in for the
 * page with a few lines of state.
 *
 * Every string is quoted from `spec/design/ui/todo-list.md` § Copy and § Accessibility
 * labels, or from `spec/design/api.md` § The to-do list's refusals for the three
 * sentences about a text. The data is synthetic and written here.
 */

/**
 * Reaches a module the implementation wave writes, when the test runs.
 *
 * The specifier is a value rather than a literal, and that is load-bearing: under
 * jsdom Vite resolves a literal `import('./X')` while transforming this file, so a
 * module that does not exist yet failed the whole file at load time with no test
 * collected. A value is resolved when the import runs, and a missing module fails
 * the one test that reached for it. `typeof import(...)` keeps the module's types
 * and is erased before anything resolves it.
 */
function reach<T>(path: string): Promise<T> {
  return import(/* @vite-ignore */ path) as Promise<T>
}

type RowModule = typeof import('./TodoTaskRow')
type RowProps = Parameters<RowModule['TodoTaskRow']>[0]

const EMPTY = 'A task needs text. Type what there is to do.'
const MULTILINE =
  'A task is one line, and this text has a line break inside it, which may not be visible. Remove the line break and try again.'
const TOO_LONG = 'A task can be at most 200 characters. Shorten it and try again.'

function task(id: number, text: string, done = false): TodoTask {
  return {
    id: `00000000-0000-4000-8000-${String(id).padStart(12, '0')}`,
    text,
    done,
    created_at: `2026-09-24T09:0${id}:00Z`,
  }
}

/** Handlers a row may call, each a spy, so a test can say what was -- and was not -- sent. */
function handlers() {
  return {
    onEditStart: vi.fn(),
    onEditCancel: vi.fn(),
    onSave: vi.fn(),
    onMark: vi.fn(),
    onDelete: vi.fn(),
  }
}

const box = (text: string) => screen.getByRole('checkbox', { name: text })

/**
 * The class names on an element and on everything above it, nearest first,
 * leaving out the ones a variant switches on (`hover:`, `disabled:` ...). jsdom
 * loads no stylesheet, so a computed colour is not there to read; the class is the
 * token (`--color-muted` is `text-muted`), and it is what a reviewer would read.
 */
function classesAround(element: Element): string[][] {
  const layers: string[][] = []
  for (let node: Element | null = element; node !== null && node !== document.body; node = node.parentElement) {
    layers.push(Array.from(node.classList).filter((name) => !name.includes(':')))
  }
  return layers
}

/** The text colour that wins for this element: the nearest palette class above it. */
function textColourOf(element: Element): string | undefined {
  const palette = ['text-ink', 'text-muted', 'text-faint', 'text-disabled', 'text-accent', 'text-danger', 'text-inverse']
  for (const layer of classesAround(element)) {
    const found = layer.find((name) => palette.includes(name))
    if (found !== undefined) return found
  }
  return undefined
}

it('shows a done task differently from a not-done one [req:CR-2609-823a/R-4]', async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  render(
    <div>
      <TodoTaskRow task={task(1, 'Call the plumber', true)} isEditing={false} {...handlers()} />
      <TodoTaskRow task={task(2, 'Buy bread')} isEditing={false} {...handlers()} />
    </div>,
  )

  // The state assistive technology reads, on a box the task's text names.
  expect(box('Call the plumber')).toBeChecked()
  expect(box('Buy bread')).not.toBeChecked()

  // The strike-through, in the muted text colour -- and never greyed out: the
  // done text has to stay as readable as any other text (`R-4` clause 6).
  const doneText = screen.getByText('Call the plumber')
  const doneClasses = classesAround(doneText).flat()
  expect(doneClasses).toContain('line-through')
  expect(textColourOf(doneText)).toBe('text-muted')
  expect(doneClasses.filter((name) => name.startsWith('opacity-'))).toEqual([])
  expect(doneClasses).not.toContain('text-disabled')

  // The not-done text carries neither, so the two states are two looks.
  const openText = screen.getByText('Buy bread')
  expect(classesAround(openText).flat()).not.toContain('line-through')
  expect(textColourOf(openText)).not.toBe('text-muted')
})

it('sends the state the person chose [req:CR-2609-823a/R-4]', async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  const user = userEvent.setup()
  const open = handlers()
  const done = handlers()
  const bread = task(1, 'Buy bread')
  const plumber = task(2, 'Call the plumber', true)
  const { rerender } = render(
    <div>
      <TodoTaskRow task={bread} isEditing={false} {...open} />
      <TodoTaskRow task={plumber} isEditing={false} {...done} />
    </div>,
  )

  await user.click(box('Buy bread'))

  // `done` and nothing else, carrying the state chosen -- never "the opposite of
  // whatever is stored", which is what lets two people ticking the same task
  // both end with it done (`BR-09`).
  expect(open.onMark.mock.calls).toEqual([[{ done: true }]])
  // Nothing is shown as made before the application answers: the box still says
  // what is stored.
  expect(box('Buy bread')).not.toBeChecked()

  // While the tick travels: the box locked on the stored state, "Saving…" beside it.
  rerender(
    <div>
      <TodoTaskRow task={bread} isEditing={false} isMarking {...open} />
      <TodoTaskRow task={plumber} isEditing={false} {...done} />
    </div>,
  )
  expect(box('Buy bread')).toBeDisabled()
  expect(box('Buy bread')).not.toBeChecked()
  expect(screen.getByText('Saving…')).toBeInTheDocument()

  // The other way, and through the text: the text is the box's label, so pressing
  // it ticks the box too.
  await user.click(screen.getByText('Call the plumber'))
  expect(done.onMark.mock.calls).toEqual([[{ done: false }]])
})

/**
 * Three tasks and one open editor at a time, as the page holds them. A save
 * stands for the answer that went through: the page reads the list again and the
 * row is handed the stored text.
 */
function ListOfThree({ Row, onSave }: { Row: RowModule['TodoTaskRow']; onSave: RowProps['onSave'] }) {
  const [tasks, setTasks] = useState([task(3, 'Third'), task(2, 'Buy bred'), task(1, 'First')])
  const [editing, setEditing] = useState<string | undefined>(undefined)
  return (
    <div>
      {tasks.map((each) => (
        <Row
          key={each.id}
          task={each}
          isEditing={editing === each.id}
          onEditStart={() => setEditing(each.id)}
          onEditCancel={() => setEditing(undefined)}
          onSave={(body) => {
            onSave(body)
            setTasks((current) =>
              current.map((other) => (other.id === each.id ? { ...other, text: body.text } : other)),
            )
            setEditing(undefined)
          }}
          onMark={vi.fn()}
          onDelete={vi.fn()}
        />
      ))}
    </div>
  )
}

it("shows a corrected text in the task's place [req:CR-2609-823a/R-6]", async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  const user = userEvent.setup()
  const onSave = vi.fn()
  render(<ListOfThree Row={TodoTaskRow} onSave={onSave} />)

  await user.click(screen.getByRole('button', { name: 'Edit “Buy bred”' }))

  // In place, seeded with what is stored, the focus already in it.
  const field = screen.getByRole('textbox', { name: 'Edit task' })
  expect(field).toHaveValue('Buy bred')
  expect(field).toHaveFocus()

  await user.clear(field)
  await user.type(field, 'Buy bread')
  await user.click(screen.getByRole('button', { name: 'Save' }))

  // `text` and nothing else: a correction never writes the done mark back, so a
  // tick sent at the same moment by somebody else is kept (`BR-10`).
  expect(onSave.mock.calls).toEqual([[{ text: 'Buy bread' }]])
  expect(Object.keys(onSave.mock.calls[0]?.[0] as object)).toEqual(['text'])

  // The new text stands where the old one stood: the list did not move.
  expect(screen.queryByRole('textbox', { name: 'Edit task' })).not.toBeInTheDocument()
  expect(screen.queryByText('Buy bred')).not.toBeInTheDocument()
  const boxes = screen.getAllByRole('checkbox')
  expect(boxes).toHaveLength(3)
  expect(['Third', 'Buy bread', 'First'].map((text) => boxes.indexOf(box(text)))).toEqual([0, 1, 2])
})

it('keeps the old text and says why when a correction is refused [req:CR-2609-823a/R-6]', async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  const { TODO_TASK_TEXT_MAX_LENGTH } =
    await reach<typeof import('../lib/todoTask')>('../lib/todoTask')
  const user = userEvent.setup()
  const onSave = vi.fn()
  const bread = task(1, 'Buy bread')

  function OneRow() {
    const [editing, setEditing] = useState(false)
    return (
      <TodoTaskRow
        task={bread}
        isEditing={editing}
        onEditStart={() => setEditing(true)}
        onEditCancel={() => setEditing(false)}
        onSave={onSave}
        onMark={vi.fn()}
        onDelete={vi.fn()}
      />
    )
  }
  render(<OneRow />)

  await user.click(screen.getByRole('button', { name: 'Edit “Buy bread”' }))
  const field = screen.getByRole('textbox', { name: 'Edit task' })

  // An edit may not do what a new task is forbidden: each of the three reasons,
  // each in its own words, and none of them sent (`R-6` clause 4).
  await user.clear(field)
  await user.keyboard('{Enter}')
  expect(await screen.findByRole('alert')).toHaveTextContent(EMPTY)
  expect(field).toHaveAttribute('aria-invalid', 'true')
  expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

  await user.paste(`Buy bread${String.fromCodePoint(0x2028)}and milk`)
  await user.keyboard('{Enter}')
  expect(screen.getByRole('alert')).toHaveTextContent(MULTILINE)

  await user.clear(field)
  await user.paste('a'.repeat(TODO_TASK_TEXT_MAX_LENGTH + 1))
  await user.keyboard('{Enter}')
  expect(screen.getByRole('alert')).toHaveTextContent(TOO_LONG)
  expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()

  expect(onSave).not.toHaveBeenCalled()

  // "Cancel" brings back the stored text: the refused correction changed nothing.
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(screen.queryByRole('textbox', { name: 'Edit task' })).not.toBeInTheDocument()
  expect(box('Buy bread')).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(onSave).not.toHaveBeenCalled()
})

it('asks before deleting and sends nothing until confirmed [req:CR-2609-823a/R-7]', async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  const user = userEvent.setup()
  const beta = handlers()
  render(
    <div>
      <TodoTaskRow task={task(1, 'Beta')} isEditing={false} {...beta} />
    </div>,
  )

  await user.click(screen.getByRole('button', { name: 'Delete “Beta”' }))

  // The question names what it will destroy, says it cannot be taken back, and
  // starts on the way out, so an Enter pressed out of habit deletes nothing.
  const question = await screen.findByRole('dialog')
  expect(within(question).getByText('Delete this task?')).toBeInTheDocument()
  // Quoted, in whatever marks the quotation is drawn with.
  expect(within(question).getByText(/Beta/)).toBeInTheDocument()
  expect(within(question).getByText('This cannot be undone.')).toBeInTheDocument()
  expect(within(question).getByRole('button', { name: 'Cancel' })).toHaveFocus()

  // Nothing is sent while the person decides, and the task is still there behind
  // the question.
  expect(beta.onDelete).not.toHaveBeenCalled()
  expect(screen.getByRole('checkbox', { name: 'Beta', hidden: true })).toBeInTheDocument()

  await user.click(within(question).getByRole('button', { name: 'Delete task' }))

  // The one deletion, once.
  expect(beta.onDelete).toHaveBeenCalledTimes(1)
})

it('leaves the task as it was when the deletion is cancelled [req:CR-2609-823a/R-7]', async () => {
  const { TodoTaskRow } = await reach<RowModule>('./TodoTaskRow')
  const user = userEvent.setup()
  const beta = handlers()
  render(
    <div>
      <TodoTaskRow task={task(1, 'Beta')} isEditing={false} {...beta} />
    </div>,
  )

  // "Cancel" ...
  await user.click(screen.getByRole('button', { name: 'Delete “Beta”' }))
  await user.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Cancel' }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

  // ... and Escape, the other way out the question offers.
  await user.click(screen.getByRole('button', { name: 'Delete “Beta”' }))
  await screen.findByRole('dialog')
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

  // Neither sent anything or changed anything.
  expect(beta.onDelete).not.toHaveBeenCalled()
  expect(beta.onMark).not.toHaveBeenCalled()
  expect(beta.onSave).not.toHaveBeenCalled()
  expect(box('Beta')).not.toBeChecked()
  expect(screen.getByText('Beta')).toBeInTheDocument()
})
