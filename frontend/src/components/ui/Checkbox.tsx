import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'

import { cn } from '@/lib/cn'

/**
 * A checkbox in this system's language: a square with a 2px edge, filled with
 * the accent and ticked when checked.
 *
 * **It is a real `<input type="checkbox">`, drawn over rather than replaced.**
 * The input sits on top of the drawn box, the full size of it and invisible, so
 * a press, Space, a `<label>` pointing at it and the checked state assistive
 * technology reads are all the browser's own -- a `div` with `role="checkbox"`
 * would have to re-implement every one of them, and the one it forgot would be
 * the keyboard. Checked shows three ways at once in whatever renders it: the
 * fill, the tick and the state a reader announces, so colour is never the only
 * carrier (`spec/design/ui/todo-list.md` § A task's row).
 *
 * **The focus ring is drawn around the box, because the input itself is not
 * drawn** -- an outline on an invisible element is invisible too. It is the
 * screen's ring (`frontend/src/index.css`): the accent colour, 2px, offset 2px.
 *
 * The unticked edge is `--color-faint`, which clears the 3:1 a control's edge
 * needs against a white card; `--color-line` would not. A locked box is faded to
 * half, as a locked control is everywhere here -- the box, never the text beside
 * it, whose contrast is a promise of its own.
 *
 * Everything else an `<input>` takes passes through: `checked`, `onChange`,
 * `disabled`, `id`, the `aria-*` a caller names it with. No business logic, no
 * data (`spec/design/conventions.md` § Frontend).
 */
export type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { className, ...rest },
  ref,
) {
  return (
    <span className={cn('relative mt-0.5 flex size-5 shrink-0', className)}>
      <input
        ref={ref}
        type="checkbox"
        className="peer absolute inset-0 m-0 size-full cursor-pointer opacity-0 disabled:cursor-progress"
        {...rest}
      />
      <span
        aria-hidden="true"
        className={cn(
          'pointer-events-none flex size-5 items-center justify-center rounded-md border-2',
          'border-faint bg-card text-transparent',
          'peer-checked:border-accent peer-checked:bg-accent peer-checked:text-inverse',
          'peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent',
          'peer-disabled:opacity-50',
        )}
      >
        {/* The tick is always there and painted in the box's text colour, which
            is transparent until the input is checked -- so the drawing follows
            the input's own state, whoever holds it. */}
        <svg
          viewBox="0 0 16 16"
          className="size-3.5 fill-none stroke-current"
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3.5 8.5l3 3 6-7" />
        </svg>
      </span>
    </span>
  )
})
