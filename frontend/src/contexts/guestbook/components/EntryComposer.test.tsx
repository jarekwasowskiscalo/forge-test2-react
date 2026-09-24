import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { MESSAGE_MAX_LENGTH } from '@/contexts/guestbook/lib/guestbookEntry'

import { EntryComposer } from './EntryComposer'

/**
 * The card an entry is written in.
 *
 * The rules it applies are unit-tested in `lib/guestbookEntry.ts`; what is
 * tested here is that the **card is wired to them** -- the seam between a
 * correct rule and a form that ignores it -- plus the three choices that are
 * decisions rather than presentation:
 *
 * - the button stays closed until both fields hold something (`BR-01`);
 * - a problem appears only after a field has been left, never per keystroke;
 * - what is sent is trimmed, so the browser and the server measure the same
 *   string.
 */

function renderComposer(props = {}) {
  const onSubmit = vi.fn()
  const utils = render(<EntryComposer onSubmit={onSubmit} {...props} />)
  return { ...utils, onSubmit }
}

const nameField = () => screen.getByRole('textbox', { name: 'Your name' })
const messageField = () => screen.getByRole('textbox', { name: 'Your message' })
const postButton = () => screen.getByRole('button', { name: 'Post entry' })

describe('what it takes to post', () => {
  it('keeps the button closed until both fields hold something [req:CR-2609-9b1e/R-2]', async () => {
    const user = userEvent.setup()
    renderComposer()

    expect(postButton()).toBeDisabled()

    await user.type(nameField(), 'Clara')
    // A signature alone is not an entry: the mock-up would have posted this,
    // and `BR-01` refuses it.
    expect(postButton()).toBeDisabled()

    await user.type(messageField(), 'Hello there')
    expect(postButton()).toBeEnabled()
  })

  it('sends the trimmed values, so the browser measured what the server stores [req:CR-2609-9b1e/R-1]', async () => {
    const user = userEvent.setup()
    const { onSubmit } = renderComposer()

    await user.type(nameField(), '  Clara  ')
    await user.type(messageField(), '  Hello there  ')
    await user.click(postButton())

    expect(onSubmit).toHaveBeenCalledWith({ author: 'Clara', message: 'Hello there' })
  })
})

describe('when it says something is wrong', () => {
  it('stays quiet while a field is still being typed into', async () => {
    const user = userEvent.setup()
    renderComposer()

    await user.click(nameField())

    // Telling somebody their name is too short at the first letter is noise,
    // and noise is what teaches people to ignore the red text that matters.
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('speaks once the field has been left empty', async () => {
    const user = userEvent.setup()
    renderComposer()

    await user.click(nameField())
    await user.tab()

    expect(await screen.findByRole('alert')).toHaveTextContent(/Add a name or a signature/)
    expect(nameField()).toHaveAttribute('aria-invalid', 'true')
  })
})

describe('the character counter', () => {
  it('counts what has been typed against the published ceiling', async () => {
    const user = userEvent.setup()
    renderComposer()

    expect(screen.getByText(`0 / ${MESSAGE_MAX_LENGTH}`)).toBeInTheDocument()

    await user.type(messageField(), 'abcde')

    // Read from the exported constant, never written as 1000: a test that spells
    // the number keeps proving the old rule after the rule moves.
    expect(screen.getByText(`5 / ${MESSAGE_MAX_LENGTH}`)).toBeInTheDocument()
  })
})

describe('while the write is in flight', () => {
  it('locks the card and says what is happening instead of vanishing', () => {
    renderComposer({ isPending: true })

    expect(screen.getByRole('button', { name: 'Posting…' })).toBeDisabled()
    expect(nameField()).toBeDisabled()
    expect(messageField()).toBeDisabled()
  })
})
