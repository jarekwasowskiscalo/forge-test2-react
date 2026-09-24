import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { expect, it } from 'vitest'

/**
 * The browser's half of the rule a task's text is judged by (`BR-06`, `BR-07`).
 *
 * This file and `tests/unit/test_todo_task_text_rules.py` read the SAME BYTES --
 * `golden-set/fixtures/todo-task-text.json` -- and assert the same verdicts and
 * the same lengths against them. Agreement is not a property either side has by
 * itself, so it can only be proved from one file both sides read; a second copy
 * of the cases here would be two lists nothing holds equal (`D-04`, one context
 * over). It is therefore the one module in the to-do list's browser folder
 * allowed to reach into the corpus, and `tests/fitness/test_golden_set.py` names
 * it and keeps refusing every other one.
 *
 * **Everything this proves is reached from inside the test.** The corpus file is
 * written by another author in the same wave and the rule by the implementation
 * wave after it, so a module-level read or import would fail the whole file at
 * load time and un-collect every case in it -- and a declared failure the runner
 * does not collect fails the gate (`spec/design/testing.md` § CR-2609-823a, "Red
 * first"). Inside the test, a missing file or module fails as that test.
 *
 * The rule the screen applies before sending is the service's rule, applied
 * first: normalize and trim with the shared text rule (`@/lib/text`), then empty,
 * then more than one line, then longer than the bound in code points
 * (`spec/design/ui/todo-list.md` § The add field). The screen accepts exactly the
 * texts the service accepts -- `R-2` clause 5 -- and a verdict that differs on one
 * case is a text the screen lets through and the service refuses, or the reverse.
 */

/** One case of the corpus: a text as typed, what the rule says about it, and how long it is. */
interface TaskTextCase {
  case: string
  description: string
  input: string
  verdict: 'accepted' | 'empty' | 'multiline' | 'too_long'
  /** Present exactly when the verdict is `accepted`: the length of the text as stored. */
  length?: number
}

const CORPUS = fileURLToPath(
  new URL('../../../../../golden-set/fixtures/todo-task-text.json', import.meta.url),
)

/**
 * The corpus, read at run time rather than imported, following
 * `contexts/guestbook/lib/entryText.test.ts`: the file sits outside `frontend/`,
 * and reading it needs no tsconfig change and cannot drift from the bytes Python
 * reads.
 */
function taskTextCases(): TaskTextCase[] {
  return (JSON.parse(readFileSync(CORPUS, 'utf8')) as { cases: TaskTextCase[] }).cases
}

it("gives each case of the task's corpus the verdict it states [req:CR-2609-823a/R-2]", async () => {
  const cases = taskTextCases()
  const { todoTaskTextVerdict } = await import('./todoTask')

  // Not vacuous: a corpus that lost a whole verdict would let a rule that never
  // says it pass here, and a suite of zero disagreements over zero cases reads
  // exactly like one that agreed.
  expect(new Set(cases.map((entry) => entry.verdict))).toEqual(
    new Set(['accepted', 'empty', 'multiline', 'too_long']),
  )

  const disagreements = cases
    .map((entry) => ({ entry, said: todoTaskTextVerdict(entry.input) }))
    .filter(({ entry, said }) => said !== entry.verdict)
    .map(({ entry, said }) => `${entry.case}: the corpus says ${entry.verdict}, the rule says ${said}`)

  expect(disagreements).toEqual([])
})

it('measures each accepted case in code points, as the server does [req:CR-2609-823a/R-2]', async () => {
  const cases = taskTextCases()
  const { TODO_TASK_TEXT_MAX_LENGTH } = await import('./todoTask')
  const { normalizeText, textLength } = await import('@/lib/text')

  const accepted = cases.filter((entry) => entry.verdict === 'accepted')
  expect(accepted.length).toBeGreaterThan(0)

  // The verdict alone would pass with the wrong unit: "accepted" is true of a
  // hundred and one emoji however they are counted, as long as the count fits.
  // The LENGTH is what names the unit -- the text as it will be stored, measured.
  const mismeasured = accepted
    .map((entry) => ({ entry, measured: textLength(normalizeText(entry.input)) }))
    .filter(({ entry, measured }) => measured !== entry.length)
    .map(({ entry, measured }) => `${entry.case}: the corpus says ${entry.length}, measured ${measured}`)
  expect(mismeasured).toEqual([])

  // Every accepted text fits the bound read from the constant, never written as 200.
  for (const entry of accepted) {
    expect(entry.length).toBeLessThanOrEqual(TODO_TASK_TEXT_MAX_LENGTH)
  }
  // And the bound is reached, not merely respected: a bound nobody showed standing
  // in the right place passes the same whether it is 200 or 2000.
  expect(accepted.find((entry) => entry.case === 'ascii_at_maximum')?.length).toBe(
    TODO_TASK_TEXT_MAX_LENGTH,
  )

  // The detector, proved to fire: counted in UTF-16 units, as `.length` counts,
  // the corpus disagrees -- 101 emoji are 202 units and one past the bound. A
  // corpus on which the wrong unit agreed would prove nothing about the unit.
  const disagreeInUtf16 = accepted
    .filter((entry) => normalizeText(entry.input).length !== entry.length)
    .map((entry) => entry.case)
  expect(disagreeInUtf16).toContain('emoji_under_the_bound_but_over_it_in_utf16')
})

it('refuses a text both too long and on two lines as one line [req:CR-2609-823a/R-2]', async () => {
  const cases = taskTextCases()
  const { TODO_TASK_TEXT_MAX_LENGTH, todoTaskTextVerdict } = await import('./todoTask')

  // Built from the constant: one letter past the bound once the break is gone.
  const before = 'a'.repeat(Math.floor(TODO_TASK_TEXT_MAX_LENGTH / 2))
  const after = 'a'.repeat(TODO_TASK_TEXT_MAX_LENGTH + 1 - before.length)
  expect(todoTaskTextVerdict(`${before}${after}`)).toBe('too_long')

  // Every line break the corpus shows between "Buy bread" and "and milk", which is
  // all seven of `A-1`: the corpus is the list, so this file keeps no second copy
  // of it. A text that breaks both rules gets the one-line reason, whichever break
  // it carries (`BR-07`), because its trouble is the break -- shortening it would
  // not make it a task.
  const lineBreaks = new Set(
    cases
      .filter(
        (entry) =>
          entry.verdict === 'multiline' &&
          entry.input.startsWith('Buy bread') &&
          entry.input.endsWith('and milk'),
      )
      .map((entry) => entry.input.slice('Buy bread'.length, -'and milk'.length)),
  )
  expect(lineBreaks.size).toBe(7)
  for (const lineBreak of lineBreaks) {
    expect(todoTaskTextVerdict(`${before}${lineBreak}${after}`)).toBe('multiline')
  }

  // And the corpus's own case of it, the one the server's test reads too.
  const both = cases.find((entry) => entry.case === 'too_long_and_on_two_lines_is_multiline')
  expect(both?.verdict).toBe('multiline')
  expect(todoTaskTextVerdict(both?.input ?? '')).toBe('multiline')
})
