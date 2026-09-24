import type { components } from '@/api/schema'
import { refusalType } from '@/api/problem'
import type { Problem } from '@/api/problem'
import { normalizeText, textLength } from '@/lib/text'

/**
 * The to-do list's rules in the browser: what a task is, when its text may be
 * sent, and what the screen says when a change did not go through.
 *
 * The type is the contract's, aliased and never written out: a second copy of
 * `TodoTaskRead` here would be a contract nothing regenerates
 * (`spec/design/conventions.md` § Frontend).
 */
export type TodoTask = components['schemas']['TodoTaskRead']

/**
 * The longest a task's text may be, in code points once normalized and trimmed
 * (`BR-06`).
 *
 * A **copy** of `TODO_TASK_TEXT_MAX_LENGTH` beside `TodoTask`
 * (`app/contexts/todo_list/models/todo_task.py`), because the browser cannot
 * import Python, and legal only because `tests/fitness/test_length_constants.py`
 * holds the two literals equal. The line stays in the shape that test reads: a
 * bare integer literal at the start of its line.
 *
 * The published contract carries no `maxLength` for `text` -- the bound is a
 * refusal with a code, not a schema constraint (`spec/design/api.md` § Shapes,
 * `TodoTaskCreate`) -- so nothing generated would carry it here either.
 */
export const TODO_TASK_TEXT_MAX_LENGTH = 200

/**
 * The seven code points that make a text more than one line (`BR-07`, assumption
 * `A-1` of `CR-2609-823a`), written as numbers the way `@/lib/text` writes its trim
 * set, so an editor or a checkout cannot silently rewrite them.
 *
 * A copy of `LINE_BREAKS` beside `TodoTask`, held equal to it AS A SET by
 * `tests/fitness/test_length_constants.py`: a copy that lost one of the seven lets
 * through a text the service refuses, and one that gained one refuses a text the
 * service would store. Every one of them is also in the trim set, which is why a
 * line break at either end is trimmed rather than refused.
 */
export const LINE_BREAKS: readonly number[] = [
  0x000a, // line feed -- a one-line field drops it, a paste around the field does not
  0x000b, // line tabulation
  0x000c, // form feed
  0x000d, // carriage return
  0x0085, // next line
  0x2028, // line separator -- survives a paste, and shows nothing where it stands
  0x2029, // paragraph separator
]

const LINE_BREAK_CHARACTERS: ReadonlySet<string> = new Set(
  LINE_BREAKS.map((code) => String.fromCodePoint(code)),
)

/** What the rule says about a text: sendable, or the one reason it is not. */
export type TodoTaskTextVerdict = 'accepted' | 'empty' | 'multiline' | 'too_long'

/** The three reasons a text is refused. */
export type TodoTaskTextRefusal = Exclude<TodoTaskTextVerdict, 'accepted'>

/**
 * The service's rule, applied before sending (`spec/design/ui/todo-list.md`
 * § The add field): normalize and trim with the shared rule, then empty, then
 * more than one line, then longer than the bound in code points.
 *
 * **The order is the rule, not a style.** A text that is both too long and on two
 * lines is refused as two lines (`BR-07`): its trouble is the break, and telling
 * somebody to shorten it would not make it a task. An empty text cannot hold a
 * line break -- every one of the seven is trimmed from the ends -- so a text earns
 * exactly one of the three, the same one the service gives it
 * (`spec/design/api.md` § The to-do list's refusals, "One refusal per request").
 *
 * The screen accepts exactly the texts the service accepts (`R-2` clause 5);
 * `todoTask.test.ts` proves it against the corpus the server's suite reads too.
 */
export function todoTaskTextVerdict(text: string): TodoTaskTextVerdict {
  const value = normalizeText(text)
  if (textLength(value) === 0) return 'empty'
  for (const character of value) {
    if (LINE_BREAK_CHARACTERS.has(character)) return 'multiline'
  }
  if (textLength(value) > TODO_TASK_TEXT_MAX_LENGTH) return 'too_long'
  return 'accepted'
}

/**
 * The sentence shown under a field for each reason, word for word the service's
 * (`spec/design/api.md` § The to-do list's refusals), so one text is refused on
 * the screen and by the service for the same reason in the same words (`BR-06`).
 *
 * "Characters" in the last one is the word a person uses; the rule counts code
 * points, as every bound in the contract does.
 */
export const TODO_TASK_TEXT_REFUSALS: Record<TodoTaskTextRefusal, string> = {
  empty: 'A task needs text. Type what there is to do.',
  multiline:
    'A task is one line, and this text has a line break inside it, which may not be visible. Remove the line break and try again.',
  too_long: `A task can be at most ${TODO_TASK_TEXT_MAX_LENGTH} characters. Shorten it and try again.`,
}

/**
 * The three refusal codes about a task's text. The service answers them beside
 * the field they are about, never in a notice -- the same place the screen's own
 * verdict stands (`spec/design/ui/todo-list.md` § The refusals this screen can
 * show).
 */
const TEXT_REFUSAL_CODES: readonly string[] = [
  'todo_task_text_empty',
  'todo_task_text_multiline',
  'todo_task_text_too_long',
]

/**
 * A text the service refused although the screen's rule let it through, and the
 * service's sentence for it.
 *
 * The field shows the sentence while it still holds that text, and not once the
 * person has changed it: a refusal is about the text that was sent, so it is
 * attributed to that text rather than kept in a flag somebody has to remember to
 * clear.
 */
export interface RefusedText {
  /** The text as it was sent -- normalized and trimmed. */
  text: string
  sentence: string
}

/** How many tasks the list holds, as the header says it: `0 tasks`, `1 task`, `6 tasks`. */
export function todoTaskCountLabel(total: number): string {
  return `${total} ${total === 1 ? 'task' : 'tasks'}`
}

/** What went through, as the notice says it (`spec/design/ui/todo-list.md` § Copy). */
export const TODO_TASK_DONE_NOTICES = {
  added: 'Task added.',
  corrected: 'Task updated.',
  deleted: 'Task deleted.',
} as const

/** Which kind of write did not go through: an add, or a tick, correction or deletion. */
export type TodoTaskWrite = 'add' | 'change'

/**
 * The words for a write that did not go through, when nothing tells the person
 * more (`spec/design/ui/todo-list.md` § Copy, the user's `Q-15`).
 *
 * "Could not be reached" only when no answer came at all; "answered with an
 * error" when an answer came that carries no sentence of its own. The service's
 * body for an unhandled failure is `{"detail": "internal server error"}`, which is
 * words for an operator's log and not a sentence for a person, so it is never
 * printed as one.
 */
const NOT_MADE: Record<TodoTaskWrite, { unreachable: string; error: string }> = {
  add: {
    unreachable: 'The task was not added: the service could not be reached.',
    error: 'The task was not added: the service answered with an error.',
  },
  change: {
    unreachable: 'The change was not made: the service could not be reached.',
    error: 'The change was not made: the service answered with an error.',
  },
}

/**
 * Where a failed write is told, and in which words.
 *
 * - `field`: a refusal of the text itself, shown under the field that holds it,
 *   in the service's own sentence -- the text stays as typed.
 * - `notice`: everything else, in an error notice over a screen left as stored.
 */
export interface TodoTaskFailure {
  place: 'field' | 'notice'
  sentence: string
}

/**
 * Turn the problem a write came back with into what the screen says.
 *
 * Three cases, told apart by what came back rather than by a status code:
 *
 * 1. **Nothing answered** (`problemOf` gives such a failure the status `0`): the
 *    "could not be reached" sentence.
 * 2. **A refusal with a code** carries a finished sentence of its own, and it is
 *    shown as written (`spec/design/api.md` § The to-do list's refusals): under the
 *    field for the three about a text, in a notice for the rest -- a task that no
 *    longer exists says so, and nothing else on the screen changes.
 * 3. **Any other answer** -- a server error, a validation list the screen never
 *    provokes -- has no sentence for a person: the "answered with an error" one.
 */
export function todoTaskFailure(problem: Problem, write: TodoTaskWrite): TodoTaskFailure {
  if (problem.status === 0) return { place: 'notice', sentence: NOT_MADE[write].unreachable }

  const isRefusal = problem.type.startsWith(refusalType(''))
  if (isRefusal && problem.detail !== undefined && problem.detail !== '') {
    const aboutTheText = TEXT_REFUSAL_CODES.some((code) => problem.type === refusalType(code))
    return { place: aboutTheText ? 'field' : 'notice', sentence: problem.detail }
  }

  return { place: 'notice', sentence: NOT_MADE[write].error }
}
