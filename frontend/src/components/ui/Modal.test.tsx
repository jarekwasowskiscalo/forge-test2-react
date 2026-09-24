import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRef, useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { Modal } from './Modal'

/**
 * The four promises `aria-modal="true"` makes, held as tests.
 *
 * `DeleteEntryDialog.test.tsx` covers what the confirmation *says*; this covers
 * the mechanism underneath it, and it exists because the mechanism failed while
 * that file was green. Every assertion here is about `document.activeElement` or
 * about `inert`, and that is deliberate: the two assertions the component already
 * had -- `getByRole('dialog')` and `toBeDisabled()` -- are exactly the two that
 * passed while focus sat on a button *behind* the modal.
 *
 * jsdom is enough for all of it and that is the point. The environment never hid
 * these defects: `document.activeElement` is implemented, `Tab` through
 * `user-event` is implemented, and an attribute is an attribute. What hid them
 * was the shape of the questions being asked. (The *other* half of this screen's
 * accessibility -- whether a focus ring is actually painted -- genuinely cannot
 * be asked here, and lives in `e2e/ui/test_smoke.py`.)
 */

/** Where the application mounts. Named so the inert assertion can be literal. */
function rootContainer(): HTMLElement {
  const root = document.createElement('div')
  root.id = 'root'
  document.body.appendChild(root)
  return root
}

afterEach(() => {
  document.getElementById('root')?.remove()
})

/**
 * A page with one button on it that opens a dialog.
 *
 * The trigger is a real button that is really clicked, because the thing under
 * test is what the dialog does with *the element that had focus* -- handing it in
 * as a prop would test a different component. `vanishingTrigger` covers the case
 * the guestbook actually produces: a confirmed delete removes the card, and with
 * it the button that opened the dialog.
 */
function Harness({
  initialFocusDisabled = false,
  vanishingTrigger = false,
  onDismiss,
}: {
  initialFocusDisabled?: boolean
  vanishingTrigger?: boolean
  onDismiss?: () => void
} = {}) {
  const [open, setOpen] = useState(false)
  const [triggerGone, setTriggerGone] = useState(false)
  // Pointed at the way out, exactly as `DeleteEntryDialog` points it at Cancel.
  const cancelRef = useRef<HTMLButtonElement>(null)

  return (
    <div>
      <button type="button" onClick={() => setOpen(true)}>
        open
      </button>
      {!triggerGone && (
        <button type="button" onClick={() => setOpen(true)}>
          background
        </button>
      )}
      {open && (
        <Modal
          title="A decision"
          initialFocusRef={cancelRef}
          onDismiss={() => {
            if (vanishingTrigger) setTriggerGone(true)
            setOpen(false)
            onDismiss?.()
          }}
          footer={
            <>
              <button type="button" ref={cancelRef} disabled={initialFocusDisabled}>
                cancel
              </button>
              <button type="button" disabled={initialFocusDisabled}>
                confirm
              </button>
            </>
          }
        >
          <p>the consequence</p>
        </Modal>
      )}
    </div>
  )
}

async function openFrom(name: string) {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name }))
  return user
}

describe('where focus is when the dialog opens', () => {
  it('puts focus on the way out, which is what the caller asked for', async () => {
    render(<Harness />, { container: rootContainer() })
    await openFrom('open')

    const dialog = screen.getByRole('dialog')
    expect(dialog.contains(document.activeElement)).toBe(true)
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'cancel' }))
  })

  it('falls back to the container when the target it was given cannot take focus', async () => {
    // The defect this file was written for. `initialFocusRef ?? dialogRef` only
    // falls through on null: a *disabled* button is a live element, so `.focus()`
    // was called on it, silently ignored, and the container was never reached.
    render(<Harness initialFocusDisabled />, { container: rootContainer() })
    await openFrom('open')

    const dialog = screen.getByRole('dialog')
    expect(document.activeElement).toBe(dialog)
    expect(dialog.contains(document.activeElement)).toBe(true)
  })
})

describe('Tab cannot leave the dialog', () => {
  it('wraps forwards from the last control to the first', async () => {
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('open')

    const dialog = screen.getByRole('dialog')
    screen.getByRole('button', { name: 'confirm' }).focus()
    await user.tab()

    expect(dialog.contains(document.activeElement)).toBe(true)
    // The scrolling body, which is the first stop in the cycle by design: a body
    // taller than the dialog cannot be read with the arrow keys otherwise.
    expect(document.activeElement).toBe(dialog.querySelector('[tabindex="0"]'))
  })

  it('wraps backwards from the first control to the last', async () => {
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('open')

    const dialog = screen.getByRole('dialog')
    ;(dialog.querySelector('[tabindex="0"]') as HTMLElement).focus()
    await user.tab({ shift: true })

    expect(dialog.contains(document.activeElement)).toBe(true)
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'confirm' }))
  })

  it('takes focus back when Tab is pressed with focus already in the background', async () => {
    // The assertion that does not pass while the trap is bound to the overlay
    // div: the dialog is a React *sibling* of the page, so a keydown from a button
    // behind it bubbles through that button's own ancestors and never reaches the
    // handler. Escape was bound to the document for precisely this reason.
    //
    // **Focus starts on the FIRST background button, and that detail is the
    // test.** The portal appends the dialog last in the document, so a Tab from
    // the last background control walks into the dialog of its own accord and
    // would be green with no trap at all. From the first one, the next stop in
    // document order is the second background button -- still behind the modal --
    // so only the trap can produce the expected result.
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('open')

    const dialog = screen.getByRole('dialog')
    screen.getByRole('button', { name: 'open' }).focus()
    expect(dialog.contains(document.activeElement)).toBe(false)

    await user.tab()

    expect(document.activeElement).not.toBe(screen.getByRole('button', { name: 'background' }))
    expect(dialog.contains(document.activeElement)).toBe(true)
  })

  it('takes focus back on Shift+Tab from the background too', async () => {
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('open')

    const dialog = screen.getByRole('dialog')
    screen.getByRole('button', { name: 'background' }).focus()

    await user.tab({ shift: true })

    expect(dialog.contains(document.activeElement)).toBe(true)
  })
})

describe('the page behind it', () => {
  it('is inert while the dialog is open and not afterwards', async () => {
    const root = rootContainer()
    render(<Harness />, { container: root })

    expect(root.hasAttribute('inert')).toBe(false)

    const user = await openFrom('open')
    expect(root.hasAttribute('inert')).toBe(true)

    await user.keyboard('{Escape}')
    expect(root.hasAttribute('inert')).toBe(false)
  })
})

describe('where focus goes when the dialog closes', () => {
  it('returns to the control that opened it', async () => {
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('background')

    await user.keyboard('{Escape}')

    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'background' }))
  })

  it('lands somewhere on the screen when the control that opened it is gone', async () => {
    // What a confirmed delete does: the card is removed, and with it the button
    // that opened the dialog. `trigger.focus()` on a detached node is a no-op, so
    // focus dropped to <body> -- and Tab from <body> restarts at the top of the
    // document, which is not where the person was.
    render(<Harness vanishingTrigger />, { container: rootContainer() })
    const user = await openFrom('background')

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('button', { name: 'background' })).toBeNull()
    expect(document.activeElement).not.toBe(document.body)
    expect(document.activeElement).not.toBeNull()
  })

  it('opens a second time down the same path', async () => {
    // `Modal`'s focus effect has an empty dependency list, so a second open is a
    // second mount rather than a re-run: it is a different path through the same
    // code and it has broken independently before.
    render(<Harness />, { container: rootContainer() })
    const user = await openFrom('open')
    await user.keyboard('{Escape}')

    await user.click(screen.getByRole('button', { name: 'open' }))

    const dialog = screen.getByRole('dialog')
    expect(dialog.contains(document.activeElement)).toBe(true)
  })
})

describe('dismissal', () => {
  it('reports Escape once, not once per listener', async () => {
    const onDismiss = vi.fn()
    render(<Harness onDismiss={onDismiss} />, { container: rootContainer() })
    const user = await openFrom('open')

    await user.keyboard('{Escape}')

    expect(onDismiss).toHaveBeenCalledOnce()
  })
})
