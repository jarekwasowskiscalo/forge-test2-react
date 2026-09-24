import { useCallback, useEffect, useId, useLayoutEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import type { ReactNode, RefObject } from 'react'

import { cn } from '@/lib/cn'

/**
 * A modal dialog: portal, backdrop, focus trap, inert background, focus restore.
 *
 * Written from scratch rather than pulled in: a dependency-free dialog is
 * ~80 lines of focus handling, and every headless-dialog package would arrive
 * with its own focus-trap and portal opinions to argue with.
 *
 * Everything here is mechanism. It knows nothing about what is being
 * confirmed -- that lives in the caller (`DeleteEntryDialog`), which is what
 * lets the focus behaviour below be reviewed as one thing instead of read past
 * on the way to what it is confirming.
 *
 * **Not `<dialog>` (decision of 2026-09-16, `cr: historical`).** `showModal()`
 * would give the backdrop, the inertness, the entering focus and the Escape
 * handling for free. Three things argue against it, and none of them is the
 * reason this comment used to give -- "this app's `position: absolute`
 * overlays", of which there is not one in the tree:
 *
 * 1. `showModal()` puts the element in the browser's **top layer**, which paints
 *    over every z-index there is. `Toast.tsx` renders its host as an ordinary
 *    `fixed z-50` node that is always mounted, and a failed delete is announced
 *    exactly there -- so `::backdrop` would cover the one region that has
 *    something to say while this dialog is open.
 * 2. `spec/design/ui/guestbook.md` § The delete dialog requires a dialog that is
 *    **not dismissable** while the request is in flight. A `<dialog>` closes on
 *    Escape natively, so keeping that promise means intercepting `cancel` --
 *    which is the same amount of code as owning the key.
 * 3. Both `aria-live` regions are deliberately mounted at all times
 *    (`Toast.tsx`), and moving the dialog to the top layer changes what a reader
 *    observes about a region it is already watching.
 *
 * The parts `<dialog>` would have given are implemented below, and the reason
 * is recorded here rather than left to be rediscovered: an argument written
 * down wrongly is worse than one not written down, because the next reader
 * checks it, finds it false, and throws out the decision with it.
 */

/** Everything Tab should be able to reach inside the dialog. */
const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'

/**
 * The element chain from a node up to `<body>`, closest first.
 *
 * Recorded while the trigger is still in the document, because it is needed
 * after the trigger has left it: a confirmed delete removes the card, and with
 * it the button that opened this dialog.
 */
function lineageOf(element: Element): HTMLElement[] {
  const chain: HTMLElement[] = []
  let node = element.parentElement
  while (node !== null && node !== document.body) {
    chain.push(node)
    node = node.parentElement
  }
  return chain
}

/**
 * Focus `element`, and say whether it actually took it.
 *
 * The whole point. `element.focus()` on a *disabled* button is silently ignored,
 * and so is one on a hidden, `display: none` or detached node -- so asking the
 * document afterwards is the only way to distinguish "focused" from "asked". A
 * null check cannot: a disabled button is a perfectly live `HTMLButtonElement`.
 */
function focusTook(element: HTMLElement | null | undefined): boolean {
  if (element === null || element === undefined) return false
  element.focus()
  return document.activeElement === element
}

export interface ModalProps {
  /** Small caps line above the title -- process and rule ids. */
  eyebrow?: ReactNode
  title: ReactNode
  /** The scrolling body. */
  children: ReactNode
  /** The footer strip: explanation on the left, actions on the right. */
  footer: ReactNode
  /**
   * Called on Escape and on a backdrop press.
   *
   * Omit it to make the dialog undismissable -- which is what a caller does
   * once its action is in flight and there is nothing left to cancel.
   */
  onDismiss?: () => void
  /**
   * Focused when the dialog opens. Falls back to the dialog container.
   *
   * A confirmation exists to be answered, so a caller points this at the
   * decision rather than at the first focusable. The fallback matters: a
   * disabled confirm button cannot take focus, and without a container to
   * catch it focus would stay on the trigger *behind* the modal -- where Tab
   * then walks into the page the dialog is covering.
   *
   * It is a fallback the implementation reaches, and that sentence is load
   * bearing: this comment described the behaviour correctly for a while before
   * `focusTook` existed, and the code underneath it chose the disabled button
   * every time.
   */
  initialFocusRef?: RefObject<HTMLElement | null>
  className?: string
}

export function Modal({
  eyebrow,
  title,
  children,
  footer,
  onDismiss,
  initialFocusRef,
  className,
}: ModalProps) {
  const headingId = useId()
  const bodyId = useId()
  const dialogRef = useRef<HTMLDivElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)

  const dismiss = useCallback(() => onDismiss?.(), [onDismiss])

  useLayoutEffect(() => {
    // **One effect, and the order inside it is the design.** Marking the
    // background `inert` blurs whatever is focused inside it, so reading the
    // trigger has to happen first; restoring focus to the trigger needs the
    // background to be live again, so the cleanup has to undo them in the
    // opposite order. Two effects could not promise either, because React
    // orders effects by position and cleanups by the same -- not in the pairs
    // this needs.
    //
    // A layout effect rather than a passive one for a second reason as well:
    // `GuestbookPage` clears this dialog and pushes an error toast in the same
    // commit when a delete fails, and the toast's `aria-live` host lives inside
    // `#root`. A cleanup that ran after paint would insert the announcement
    // into a subtree that was still inert, and nobody would hear it.

    // 1. The element that opened the dialog, so focus can be handed back. Read
    //    from the document rather than taken as a prop: the trigger is whatever
    //    had focus, which for a form is the submit button when clicked and the
    //    last field when submitted with Enter.
    const trigger = document.activeElement
    // Its ancestry, recorded while it is still in the document -- by the time
    // focus is handed back it may not be. See step 4.
    const lineage =
      trigger === null || trigger === document.body ? [] : lineageOf(trigger)

    // 2. `aria-modal` is a claim; this is what makes it true. Without it the
    //    page behind stays reachable by mouse, by Tab and by a screen reader's
    //    own navigation -- and a reader told the background is inert while focus
    //    is physically in it gets two incompatible models of one page, which is
    //    worse than never having claimed it.
    //
    //    Everything under <body> except this dialog's own portal node, rather
    //    than a hard-coded `#root`: in the application those are the same
    //    element, and saying it this way keeps the rule true under a test
    //    renderer, a second root, or anything else mounted beside it. Nodes that
    //    were already inert are left out of the list, so the cleanup restores
    //    the page it found rather than the page it assumed.
    const overlay = overlayRef.current
    const backgrounded = Array.from(document.body.children).filter(
      (node): node is HTMLElement =>
        node instanceof HTMLElement && node !== overlay && !node.hasAttribute('inert'),
    )
    for (const node of backgrounded) node.setAttribute('inert', '')

    // 3. Asked, then verified. A disabled confirm button is a live element, so
    //    `??` never falls through to the container -- it picked the button, the
    //    browser ignored the call, and focus stayed on the trigger *behind* the
    //    modal. Checking where the focus landed covers the whole class of
    //    refusals rather than the one case reported: disabled, hidden,
    //    `display: none`, or a node that has already left the document.
    if (!focusTook(initialFocusRef?.current)) dialogRef.current?.focus()

    return () => {
      for (const node of backgrounded) node.removeAttribute('inert')

      // 4. The trigger first, then up its own ancestry. A confirmed delete
      //    removes the card the Delete button sat in, so `trigger.focus()` is a
      //    call on a detached node: it does nothing, focus drops to <body>, and
      //    the next Tab restarts at the top of the document instead of where the
      //    person was. The nearest ancestor still on screen is the list they
      //    were reading, which is the honest answer to "where did that go".
      const home = [trigger, ...lineage].find(
        (node): node is HTMLElement =>
          node instanceof HTMLElement && node !== document.body && node.isConnected,
      )
      if (home === undefined) return
      if (!home.hasAttribute('tabindex')) {
        // A container is not focusable on its own. Marked -1 so it can take
        // focus programmatically without joining the Tab order, and unmarked
        // again the moment focus leaves it: a dialog should not leave attributes
        // behind on a page it only borrowed.
        home.setAttribute('tabindex', '-1')
        home.addEventListener('blur', () => home.removeAttribute('tabindex'), { once: true })
      }
      home.focus()
    }
    // Deliberately once, on mount: re-running would steal focus from whatever
    // the operator moved to inside the dialog.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    // On the document, not on the dialog: clicking a non-focusable part of the
    // dialog moves focus to <body> in some browsers, and Escape has to keep
    // working after that.
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') dismiss()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [dismiss])

  useEffect(() => {
    /**
     * Keep Tab inside the dialog.
     *
     * `aria-modal` tells assistive technology the rest of the page is inert, and
     * the effect above makes that true for a reader and a mouse -- but a sighted
     * keyboard user still needs the cycle closed, and `inert` is not universally
     * honoured by every environment this runs in (jsdom implements the attribute
     * and none of its behaviour).
     *
     * **On the document, exactly as Escape is, and for the same reason.** This
     * handler used to sit on the overlay's `onKeyDown`. React events propagate up
     * the React tree, and the dialog is rendered as a *sibling* of the page
     * content (`GuestbookPage`), so a keydown from a control behind the modal
     * bubbled through that control's own ancestors and never reached the overlay
     * at all: the handler simply did not run, and the branch below that recovers
     * focus from outside the container was dead code for as long as it existed.
     */
    function handleTab(event: KeyboardEvent) {
      if (event.key !== 'Tab') return
      const container = dialogRef.current
      if (container === null) return

      const nodes = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE))
      const first = nodes[0]
      const last = nodes.at(-1)
      if (first === undefined || last === undefined) return

      const active = document.activeElement
      const outside = !container.contains(active)
      if (event.shiftKey && (active === first || outside)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (active === last || outside)) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleTab)
    return () => document.removeEventListener('keydown', handleTab)
  }, [])

  return createPortal(
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-6"
      // mousedown, not click: a click that starts inside the dialog and ends on
      // the backdrop (a drag while selecting text) must not dismiss it.
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) dismiss()
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={headingId}
        aria-describedby={bodyId}
        // Focusable container so a click on its chrome keeps focus in the
        // subtree instead of dropping it on <body>.
        tabIndex={-1}
        className={cn(
          'flex max-h-[86vh] w-full max-w-xl flex-col overflow-hidden',
          'rounded-modal border border-hairline bg-card shadow-2xl',
          'animate-rise',
          className,
        )}
      >
        <header className="shrink-0 border-b border-hairline px-5 py-3.5">
          {eyebrow !== undefined && <p className="m-0 text-xs font-bold tracking-wider text-faint uppercase">{eyebrow}</p>}
          <h2 id={headingId} className="m-0 mt-1 text-lg font-bold">
            {title}
          </h2>
        </header>

        {/* tabIndex on a scroll container, not decoration: the body can be
            taller than the dialog, and a container that cannot take focus
            cannot be scrolled with the arrow keys. Without it a keyboard-only
            agent would be asked to confirm consequences they cannot reach.
            It is also the first stop in the Tab cycle, before the buttons. */}
        <div id={bodyId} tabIndex={0} className="min-h-0 flex-1 overflow-y-auto px-5 py-3.5">
          {children}
        </div>

        <footer className="flex shrink-0 items-center gap-2.5 border-t border-hairline bg-card px-5 py-3">
          {footer}
        </footer>
      </div>
    </div>,
    document.body,
  )
}
