import { useState } from 'react'
import type { FormEvent } from 'react'

import { textLength } from '@/contexts/guestbook/lib/entryText'
import {
  ENTRY_PROBLEM_MESSAGES,
  MESSAGE_MAX_LENGTH,
  authorProblem,
  canSubmitEntry,
  messageProblem,
  normalizeEntryField,
} from '@/contexts/guestbook/lib/guestbookEntry'

/**
 * The card an entry is written in. Adding only -- an edit happens inside the
 * entry's own card (`EntryCard`), where the text being corrected already is.
 *
 * That split is the change from the previous screen, where one form served both
 * and the list scrolled away from it. Editing in place means the words a person
 * is fixing stay where they were reading them.
 *
 * **The fields carry no visible label**, matching the mock-up: two placeholders
 * in a card that is obviously a form. They carry `aria-label` instead, so the
 * name is there for anything that is not looking at the page -- a placeholder
 * alone is a label that disappears exactly when somebody starts typing.
 *
 * **A problem is shown only after the field has been left**, never on every
 * keystroke: telling somebody their name is too short while they are typing the
 * first letter is noise, and noise is what teaches people to ignore the red
 * text that matters.
 */
export interface EntryComposerProps {
  onSubmit: (values: { author: string; message: string }) => void
  /** True while the write is in flight: the card locks rather than vanishes. */
  isPending?: boolean
}

export function EntryComposer({ onSubmit, isPending = false }: EntryComposerProps) {
  const [author, setAuthor] = useState('')
  const [message, setMessage] = useState('')
  const [touchedAuthor, setTouchedAuthor] = useState(false)
  const [touchedMessage, setTouchedMessage] = useState(false)

  const authorIssue = touchedAuthor ? authorProblem(author) : undefined
  const messageIssue = touchedMessage ? messageProblem(message) : undefined
  const canSubmit = canSubmitEntry(author, message) && !isPending

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setTouchedAuthor(true)
    setTouchedMessage(true)
    if (!canSubmitEntry(author, message)) return
    // Trimmed here as well as on the server: what is sent should be what the
    // browser measured, or the two disagree about the length by the spaces.
    onSubmit({
      author: normalizeEntryField(author),
      message: normalizeEntryField(message),
    })
  }

  return (
    <section className="border-b border-hairline pt-7 pb-8">
      <form
        onSubmit={handleSubmit}
        noValidate
        className="flex flex-col gap-3.5 rounded-card border border-hairline bg-card p-4.5"
      >
        <div className="flex flex-col gap-1.5">
          <input
            name="author"
            aria-label="Your name"
            placeholder="Your name"
            value={author}
            disabled={isPending}
            onChange={(event) => setAuthor(event.target.value)}
            onBlur={() => setTouchedAuthor(true)}
            aria-invalid={authorIssue !== undefined}
            className="border-0 bg-transparent p-0 text-body font-medium tracking-[-0.01em] text-ink"
          />
          {authorIssue !== undefined && (
            <span role="alert" className="text-xs font-medium text-danger">
              {ENTRY_PROBLEM_MESSAGES[authorIssue]}
            </span>
          )}
        </div>

        <div className="h-px bg-hairline" aria-hidden="true" />

        <div className="flex flex-col gap-1.5">
          <textarea
            name="message"
            aria-label="Your message"
            placeholder="Write your message…"
            value={message}
            rows={3}
            disabled={isPending}
            onChange={(event) => setMessage(event.target.value)}
            onBlur={() => setTouchedMessage(true)}
            aria-invalid={messageIssue !== undefined}
            className="resize-y border-0 bg-transparent p-0 font-sans text-base leading-[1.55] text-ink"
          />
          {messageIssue !== undefined && (
            <span role="alert" className="text-xs font-medium text-danger">
              {ENTRY_PROBLEM_MESSAGES[messageIssue]}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Announced politely, not on every character: a live counter that
              interrupts is a counter that makes the field unusable with a
              screen reader on.

              Measured through the same two functions the validator beside it
              uses. It used to read `message.length` -- the UNTRIMMED value, in
              UTF-16 code units -- while `messageProblem` measured the trimmed one
              in code points, so the counter could read "1000 / 1000" over a
              message the validator called shorter, and "1000 / 1000" again over
              five hundred emoji. A counter that disagrees with the rule beside it
              is worse than no counter. */}
          <span className="nums text-xs text-faint" aria-live="polite">
            {textLength(normalizeEntryField(message))} / {MESSAGE_MAX_LENGTH}
          </span>
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded-control border-0 bg-accent px-5 py-2.5 text-sm font-medium text-inverse hover:brightness-112 disabled:cursor-not-allowed disabled:opacity-35"
          >
            {isPending ? 'Posting…' : 'Post entry'}
          </button>
        </div>
      </form>
    </section>
  )
}
