import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

import { DeleteEntryDialog } from './DeleteEntryDialog'

/**
 * The last thing standing between a click and something irreversible.
 *
 * `BR-03` makes deletion permanent and the button that starts it sits a few pixels
 * away from "Edit", so this dialog is the whole warning. Three of its choices
 * are safety properties rather than presentation, and each is invisible from the
 * page test that merely opens it:
 *
 * - it **quotes** the entry, because rows differ only by their content and a
 *   confirmation that does not name what it will destroy cannot be answered;
 * - focus lands on the way out, not on the destructive action;
 * - it stops being dismissable once the request is in flight, because by then
 *   there is nothing left to cancel and hiding it would hide what is happening.
 */

function entry(overrides: Partial<GuestbookEntry> = {}): GuestbookEntry {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    author: 'Anna',
    message: 'The message we are about to delete',
    created_at: '2026-08-30T20:00:00Z',
    updated_at: '2026-08-30T20:00:00Z',
    ...overrides,
  }
}

function renderDialog(props = {}) {
  const onConfirm = vi.fn()
  const onCancel = vi.fn()
  const utils = render(
    <DeleteEntryDialog entry={entry()} onConfirm={onConfirm} onCancel={onCancel} {...props} />,
  )
  return { ...utils, onConfirm, onCancel }
}

describe('the dialog names what it will destroy', () => {
  it('quotes the signature and the message of that entry', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')

    expect(within(dialog).getByText('Anna')).toBeInTheDocument()
    expect(within(dialog).getByText('The message we are about to delete')).toBeInTheDocument()
  })

  it('states the consequence rather than only asking [req:CR-2609-9b1e/R-5]', () => {
    renderDialog()

    // "Are you sure?" about an unnamed thing is a question nobody can answer
    // wrongly and therefore one nobody reads.
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument()
  })
})

describe('where the keyboard lands', () => {
  it('opens with focus on the way out, not on the destructive action', async () => {
    renderDialog()

    // An Enter pressed out of habit must not delete anything.
    expect(await screen.findByRole('button', { name: 'Cancel' })).toHaveFocus()
  })

  it('lets Escape close it while there is still something to cancel', async () => {
    const { onCancel } = renderDialog()

    await userEvent.setup().keyboard('{Escape}')

    expect(onCancel).toHaveBeenCalledOnce()
  })
})

describe('once the request is in flight', () => {
  it('refuses Escape, because there is nothing left to cancel', async () => {
    const { onCancel } = renderDialog({ isPending: true })

    await userEvent.setup().keyboard('{Escape}')

    // Dismissing here would hide a request that is still happening, and the next
    // thing the person sees would be a list that changed for no reason they saw.
    expect(onCancel).not.toHaveBeenCalled()
  })

  it('locks both answers and says which one is running', () => {
    renderDialog({ isPending: true })

    expect(screen.getByRole('button', { name: 'Deleting…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
  })

  it('still holds the keyboard, although neither answer can take it', async () => {
    // The defect lived exactly between this block and `opens with focus on the
    // way out` above. That test asks about focus and this one used to ask only
    // `toBeDisabled()` -- so a state in which the dialog's own focus target is a
    // *disabled* button, and focus therefore stays on the Delete button behind
    // the modal, was covered by neither. The container is where it has to land:
    // there is nothing else in the dialog that can hold it.
    renderDialog({ isPending: true })

    const dialog = await screen.findByRole('dialog')

    expect(dialog.contains(document.activeElement)).toBe(true)
    expect(document.activeElement).toBe(dialog)
  })
})

describe('answering it', () => {
  it('calls back exactly once per answer', async () => {
    const { onConfirm, onCancel } = renderDialog()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Delete entry' }))
    expect(onConfirm).toHaveBeenCalledOnce()
    expect(onCancel).not.toHaveBeenCalled()
  })
})
