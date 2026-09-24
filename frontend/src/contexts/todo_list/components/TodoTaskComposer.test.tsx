import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'

/**
 * The add field: one line, "Add task", and the service's rule applied before sending.
 *
 * The rule itself is proved in `lib/todoTask.test.ts`, against the corpus both
 * sides read. What is proved here is the seam between that rule and the field --
 * the place the guestbook's defect lived (`D-04`): a rule that counts correctly
 * behind a field that stops input at a length, or counts it in another unit,
 * refuses on the screen what the service stores. So the four claims are:
 *
 * - the field holds whatever is typed or pasted: no `maxlength`, nothing cut at
 *   the bound, and two hundred emoji -- four hundred UTF-16 units -- are one task
 *   (`R-2` clause 5, `spec/design/ui/todo-list.md` § The add field);
 * - one past the bound is held too, and refused with the sentence, never cut;
 * - a line break the field can still receive -- U+2028 arrives by paste, often
 *   invisibly -- is refused with its own sentence (`BR-07`);
 * - what is sent is the text as the shared rule leaves it, so the screen judged
 *   the same string the service will store.
 *
 * The sentences are the service's, word for word (`spec/design/api.md` § The to-do
 * list's refusals; the screen's own verdict uses the same three --
 * `spec/design/ui/todo-list.md` § The refusals this screen can show).
 *
 * The component and the bound are reached from inside each test: neither exists
 * until the implementation wave, and a module-level import would un-collect every
 * case in this file instead of failing each one as itself.
 */

/**
 * Reaches a module the implementation wave writes, when the test runs.
 *
 * The specifier is a value rather than a literal, and that is load-bearing. This
 * file runs under jsdom, where vitest transforms it the way a browser bundle is
 * transformed, and there Vite resolves a literal `import('./X')` while
 * transforming: a module that does not exist yet failed the whole file at load
 * time, with "no tests" collected. Measured before it was written down. A value is
 * resolved only when the import runs, so a missing module fails the one test that
 * reached for it -- which is the failure the RED proof declares. The type still
 * comes from the module, through `typeof import(...)`, which is erased before
 * anything resolves it.
 */
function reach<T>(path: string): Promise<T> {
  return import(/* @vite-ignore */ path) as Promise<T>
}

const TOO_LONG = 'A task can be at most 200 characters. Shorten it and try again.'
const MULTILINE =
  'A task is one line, and this text has a line break inside it, which may not be visible. Remove the line break and try again.'

/** U+1F600, outside the Basic Multilingual Plane: one code point, two UTF-16 units. */
const GRINNING_FACE = String.fromCodePoint(0x1f600)

async function renderComposer() {
  const { TodoTaskComposer } =
    await reach<typeof import('./TodoTaskComposer')>('./TodoTaskComposer')
  const { TODO_TASK_TEXT_MAX_LENGTH } =
    await reach<typeof import('../lib/todoTask')>('../lib/todoTask')
  const onSubmit = vi.fn()
  render(<TodoTaskComposer onSubmit={onSubmit} />)
  return { onSubmit, max: TODO_TASK_TEXT_MAX_LENGTH, user: userEvent.setup() }
}

const newTaskField = () => screen.getByRole('textbox', { name: 'New task' })
const addButton = () => screen.getByRole('button', { name: 'Add task' })

it('takes 200 pasted emoji whole and lets the task be added [req:CR-2609-823a/R-2]', async () => {
  const { onSubmit, max, user } = await renderComposer()
  // Built from the constant, never written as 200: a test that spells the number
  // keeps proving the old rule after the rule moves.
  const atTheBound = GRINNING_FACE.repeat(max)

  // Nothing stops input at a length. A `maxlength` counts UTF-16 units, so on this
  // text it would cut at a hundred emoji -- the defect, one context over.
  expect(newTaskField()).not.toHaveAttribute('maxlength')

  await user.click(newTaskField())
  await user.paste(atTheBound)

  expect(newTaskField()).toHaveValue(atTheBound)
  expect(addButton()).toBeEnabled()

  await user.click(addButton())

  expect(onSubmit).toHaveBeenCalledTimes(1)
  expect(onSubmit).toHaveBeenCalledWith({ text: atTheBound })
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

it('holds 201 emoji, says the text is too long and sends nothing [req:CR-2609-823a/R-2]', async () => {
  const { onSubmit, max, user } = await renderComposer()
  const pastTheBound = GRINNING_FACE.repeat(max + 1)

  await user.click(newTaskField())
  await user.paste(pastTheBound)

  // Held, not cut: a field that silently dropped the last emoji would store a
  // text the person never wrote, and say nothing about why.
  expect(newTaskField()).toHaveValue(pastTheBound)
  expect(addButton()).toBeDisabled()

  // Enter asks for the add; with a refused text it gets the sentence instead.
  await user.keyboard('{Enter}')

  expect(await screen.findByRole('alert')).toHaveTextContent(TOO_LONG)
  expect(newTaskField()).toHaveAttribute('aria-invalid', 'true')
  expect(newTaskField()).toHaveValue(pastTheBound)
  expect(onSubmit).not.toHaveBeenCalled()
})

it('says a text with a line break inside is one line and sends nothing [req:CR-2609-823a/R-2]', async () => {
  const { onSubmit, user } = await renderComposer()
  // U+2028 LINE SEPARATOR: a one-line field drops a line feed and a carriage
  // return, but this one survives a paste and shows nothing where it stands.
  const twoLines = `Buy bread${String.fromCodePoint(0x2028)}and milk`

  await user.click(newTaskField())
  await user.paste(twoLines)
  expect(addButton()).toBeDisabled()

  await user.keyboard('{Enter}')

  // Its own reason, not "empty" and not "too long": the person has to be told
  // what to remove, and the break may be invisible to them.
  expect(await screen.findByRole('alert')).toHaveTextContent(MULTILINE)
  expect(newTaskField()).toHaveAttribute('aria-invalid', 'true')
  expect(onSubmit).not.toHaveBeenCalled()
})

it('sends the text as the shared rule leaves it [req:CR-2609-823a/R-1]', async () => {
  const { onSubmit, user } = await renderComposer()
  // An em space in front, a space behind, two and three spaces inside, and an
  // "e" followed by a combining acute accent. The rule trims the ends, keeps the
  // inside as typed (`R-2` clause 4) and composes the accent (NFC) -- so the
  // screen sends the very string it judged, and the service stores that string.
  const asTyped = `${String.fromCodePoint(0x2003)}Buy  two   lamps for the cafe${String.fromCodePoint(0x0301)} `

  await user.click(newTaskField())
  await user.paste(asTyped)
  await user.click(addButton())

  expect(onSubmit).toHaveBeenCalledTimes(1)
  expect(onSubmit).toHaveBeenCalledWith({
    text: `Buy  two   lamps for the caf${String.fromCodePoint(0x00e9)}`,
  })
})
