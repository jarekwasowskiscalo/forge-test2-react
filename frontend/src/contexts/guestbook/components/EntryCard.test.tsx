import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { GuestbookEntry } from '@/contexts/guestbook/lib/guestbookEntry'

import { EntryCard } from './EntryCard'

/**
 * One entry, read and corrected in the same place.
 *
 * Editing in place is the change this screen makes, and it brings a failure the
 * old shared form could not have: an editor seeded from the wrong entry. The
 * card is keyed on the entry's id for exactly that, and a missing key is
 * invisible until the second edit shows the first entry's text -- so opening two
 * editors in turn is one of the assertions below.
 *
 * The "edited" marker is derived from the two instants (`BR-02`), never read
 * from a flag, and both halves of that are asserted: an untouched entry must not
 * claim to have been corrected.
 */

function entry(overrides: Partial<GuestbookEntry> = {}): GuestbookEntry {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    author: 'Anna',
    message: 'Hello there',
    created_at: '2026-08-30T20:00:00Z',
    updated_at: '2026-08-30T20:00:00Z',
    ...overrides,
  }
}

function renderCard(props: Partial<Parameters<typeof EntryCard>[0]> = {}) {
  const handlers = {
    onEditStart: vi.fn(),
    onEditCancel: vi.fn(),
    onSave: vi.fn(),
    onDelete: vi.fn(),
  }
  const utils = render(
    <EntryCard entry={entry()} isEditing={false} {...handlers} {...props} />,
  )
  return { ...utils, ...handlers }
}

describe('reading an entry', () => {
  it('shows the signature and the message', () => {
    renderCard()

    expect(screen.getByText('Anna')).toBeInTheDocument()
    expect(screen.getByText('Hello there')).toBeInTheDocument()
  })

  it('keeps the exact instant in the markup while showing the age in words', () => {
    const { container } = renderCard()

    // The age is prose and rounds; the `datetime` attribute is the record. A
    // card that only rendered "2 days ago" would have lost when this was written.
    expect(container.querySelector('time')).toHaveAttribute(
      'dateTime',
      '2026-08-30T20:00:00Z',
    )
  })

  it('says "edited" only once the two instants have parted', () => {
    const { rerender } = renderCard()
    expect(screen.queryByText(/edited/)).not.toBeInTheDocument()

    rerender(
      <EntryCard
        entry={entry({ updated_at: '2026-08-30T21:00:00Z' })}
        isEditing={false}
        onEditStart={vi.fn()}
        onEditCancel={vi.fn()}
        onSave={vi.fn()}
        onDelete={vi.fn()}
      />,
    )
    expect(screen.getByText(/edited/)).toBeInTheDocument()
  })
})

describe('the two actions', () => {
  it('asks the page to start an edit rather than starting one itself', async () => {
    const { onEditStart } = renderCard()

    await userEvent.setup().click(screen.getByRole('button', { name: 'Edit' }))

    // The page owns which entry is open, because two cards open at once is a
    // state nothing on this screen can resolve.
    expect(onEditStart).toHaveBeenCalledOnce()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('hands a delete up to the page, which is where the confirmation lives', async () => {
    const { onDelete } = renderCard()

    await userEvent.setup().click(screen.getByRole('button', { name: 'Delete' }))

    expect(onDelete).toHaveBeenCalledOnce()
  })
})

describe('editing in place', () => {
  it('opens seeded with what this entry holds', () => {
    renderCard({ isEditing: true })

    expect(screen.getByRole('textbox', { name: 'Edit name' })).toHaveValue('Anna')
    expect(screen.getByRole('textbox', { name: 'Edit message' })).toHaveValue('Hello there')
  })

  it('re-seeds when a different entry is opened', () => {
    const { rerender } = renderCard({ isEditing: true })
    const other = entry({ id: '22222222-2222-4222-8222-222222222222', author: 'Brian' })

    rerender(
      <EntryCard
        entry={other}
        isEditing
        onEditStart={vi.fn()}
        onEditCancel={vi.fn()}
        onSave={vi.fn()}
        onDelete={vi.fn()}
      />,
    )

    // Without the key on the editor this still says "Anna", and nothing else
    // on the screen would say so.
    expect(screen.getByRole('textbox', { name: 'Edit name' })).toHaveValue('Brian')
  })

  it('sends the trimmed correction up', async () => {
    const user = userEvent.setup()
    const { onSave } = renderCard({ isEditing: true })

    await user.clear(screen.getByRole('textbox', { name: 'Edit message' }))
    await user.type(screen.getByRole('textbox', { name: 'Edit message' }), '  corrected  ')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(onSave).toHaveBeenCalledWith({ author: 'Anna', message: 'corrected' })
  })

  it('closes Save while a field is empty, and says why', async () => {
    const user = userEvent.setup()
    renderCard({ isEditing: true })

    await user.clear(screen.getByRole('textbox', { name: 'Edit message' }))

    // `BR-01` is about entries, not about how they arrived: an edit may not do
    // what a new entry is forbidden from doing.
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent(/Write something/)
  })

  it('leaves the correction alone on cancel', async () => {
    const { onEditCancel, onSave } = renderCard({ isEditing: true })

    await userEvent.setup().click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onEditCancel).toHaveBeenCalledOnce()
    expect(onSave).not.toHaveBeenCalled()
  })

  it('locks the editor while the save is in flight', () => {
    renderCard({ isEditing: true, isSaving: true })

    expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Edit name' })).toBeDisabled()
  })
})
