/**
 * `toProblem` is the only place four different backend error shapes become one.
 *
 * It is also where a whole class of refusal was silently dropped once: a route
 * answers 422 with an OBJECT (`{code, message, ...}`) when it refuses for a
 * reason of its own, and the normaliser recognised only the Pydantic LIST that
 * shares that status. Everything else fell through to a bare `Problem` with no
 * `detail`, so the screen rendered its "the service returned no details" fallback
 * -- while the service had in fact returned a finished sentence naming the fix.
 *
 * Table-driven over every shape the backend actually emits, because the bug was
 * not in any one branch: it was in the set of branches being incomplete.
 */

import { describe, expect, it } from 'vitest'

import { PROBLEM_BLANK, describeProblem, refusalType, toProblem } from './problem'

describe('toProblem', () => {
  it('reads an object detail — the 422 a rejected PATCH gets', () => {
    // app/contexts/guestbook/routers/guestbook_entries.py, the empty-body refusal.
    const problem = toProblem(422, {
      detail: {
        code: 'guestbook_entry_empty_patch',
        message: 'No field was given to change. The entry is unchanged.',
      },
    })

    expect(problem.status).toBe(422)
    expect(problem.detail).toBe('No field was given to change. The entry is unchanged.')
    expect(problem.type).toBe(refusalType('guestbook_entry_empty_patch'))
  })

  it('reads a plain-string detail', () => {
    const problem = toProblem(409, {
      detail: 'Nothing was saved.',
    })

    expect(problem.status).toBe(409)
    expect(problem.detail).toContain('Nothing was saved')
  })

  it('reads the Pydantic list, grouping every message under its field', () => {
    const problem = toProblem(422, {
      detail: [
        { loc: ['body', 'author'], msg: 'String should have at least 1 character' },
        { loc: ['body', 'author'], msg: 'Field required' },
      ],
    })

    expect(problem.errors).toEqual({
      author: ['String should have at least 1 character', 'Field required'],
    })
  })

  it('falls back to a blank problem for a shape it does not know', () => {
    const problem = toProblem(500, { unexpected: true })

    expect(problem.type).toBe(PROBLEM_BLANK)
    expect(problem.status).toBe(500)
  })

  it('names every refusal code this API can emit', () => {
    // Both codes `app/contexts/guestbook/routers/guestbook_entries.py` raises. A code the frontend
    // cannot turn into a stable `type` is a refusal no screen can branch on.
    for (const code of ['guestbook_entry_not_found', 'guestbook_entry_empty_patch']) {
      expect(refusalType(code)).toBe(`urn:app:refusal:${code}`)
    }
  })
})

describe('describeProblem', () => {
  it('describes a 404 as gone rather than broken, and refuses to offer a retry', () => {
    const copy = describeProblem(
      toProblem(404, {
        detail: {
          code: 'guestbook_entry_not_found',
          message: 'There is no such entry. Somebody else may have deleted it.',
        },
      }),
    )

    expect(copy.title).toBe('That is gone')
    expect(copy.detail).toContain('Somebody else may have deleted it')
    // The half that matters: re-asking for something deleted cannot succeed, so
    // the surface must not invite it.
    expect(copy.retryable).toBe(false)
  })

  it('lists the offending fields of a 422 so the form can point at them', () => {
    const problem = toProblem(422, {
      detail: [{ loc: ['body', 'author'], msg: 'Field required', type: 'missing' }],
    })

    expect(describeProblem(problem).fields).toEqual([['author', ['Field required']]])
  })

  it('offers a retry for anything that might succeed on a second attempt', () => {
    expect(describeProblem(toProblem(500, {})).retryable).toBe(true)
  })
})
