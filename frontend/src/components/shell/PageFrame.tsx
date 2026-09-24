import { Link, NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'

import { GUESTBOOK_ROUTE, TODO_LIST_ROUTE } from '@/routes'

/**
 * The whole frame this application has: one centred column on a cream page.
 *
 * **There is no top bar and no side panel.** The way between the screens is two
 * text links in the page header, beside the lockup -- not a bar of its own, and
 * not a switcher that looks like the guestbook's order pills, which would read as
 * a filter (`spec/design/ui/system-states.md` § One column). This is the one file
 * that learned about a second screen, and a third one adds a link here.
 *
 * The links **navigate inside the application** -- router links, not page loads --
 * and the link of the screen on show stays a link, marked as the current page
 * rather than removed. On the not-found page neither is current. The group is
 * named "Screens" for assistive technology.
 *
 * The lockup is a **placeholder and is meant to look like one** -- an accent
 * square with an initial beside the name. A template that shipped a plausible
 * mark would get shipped as somebody's product under a brand nobody chose.
 * `PRODUCT_NAME` and `PRODUCT_INITIAL` are the only two strings to replace. With
 * two screens it can name neither of them: "Guestbook" there named the product
 * after one of its screens and stood beside a navigation link of the same name.
 *
 * The lockup is a link rather than a heading, and it is a link on every screen
 * including the one it points at: it is the way back from the 404, and a way
 * back that only exists on the page you are lost on is a way back nobody finds.
 */

const PRODUCT_NAME = 'Product name'
const PRODUCT_INITIAL = 'P'

/** The screens the navigation leads to, in the order it shows them. */
const SCREENS = [
  { to: GUESTBOOK_ROUTE, label: 'Guestbook' },
  { to: TODO_LIST_ROUTE, label: 'To-do list' },
] as const

/**
 * The guestbook's footer sentence (`spec/design/ui/guestbook.md` § Copy).
 *
 * The footer is each screen's own (`spec/design/ui/system-states.md` § Regions),
 * and the frame carries this one only as the default of `footer`: the guestbook's
 * screen does not pass its sentence yet, and `CR-2609-823a` changed nothing in
 * `GuestbookPage.tsx` but three import paths. The day that screen passes its own
 * footer, this constant goes.
 */
const GUESTBOOK_FOOTER = 'Entries are public and editable by anyone with this link.'

export interface PageFrameProps {
  /** The big serif line. The screen's whole title, in the product's voice. */
  title: ReactNode
  /** One sentence under it: what this screen is for, and what it costs to use. */
  lede?: ReactNode
  /** Right of the lockup: a count, a state, a fact about the whole page. */
  meta?: ReactNode
  /**
   * One sentence at the foot of the column about who sees this -- the screen's
   * own. `null` for a page with none (the not-found page).
   */
  footer?: ReactNode
  children: ReactNode
}

export function PageFrame({
  title,
  lede,
  meta,
  footer = GUESTBOOK_FOOTER,
  children,
}: PageFrameProps) {
  return (
    <div className="min-h-screen bg-surface px-6 pb-24 text-ink">
      <div className="mx-auto max-w-reading">
        <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3 pt-7">
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <Link
              to={GUESTBOOK_ROUTE}
              className="flex items-center gap-2.5 text-ink no-underline hover:text-ink"
            >
              <span
                className="flex size-6.5 items-center justify-center rounded-chip bg-accent text-meta font-semibold text-inverse"
                aria-hidden="true"
              >
                {PRODUCT_INITIAL}
              </span>
              <span className="text-sm font-medium tracking-[-0.01em]">{PRODUCT_NAME}</span>
            </Link>
            <nav aria-label="Screens" className="flex gap-5 text-sm">
              {SCREENS.map((screen) => (
                <NavLink
                  key={screen.to}
                  to={screen.to}
                  className={({ isActive }) =>
                    isActive
                      ? 'font-medium text-ink underline decoration-2 underline-offset-6'
                      : 'text-muted no-underline hover:text-ink'
                  }
                >
                  {screen.label}
                </NavLink>
              ))}
            </nav>
          </div>
          {meta !== undefined && <span className="text-meta text-muted nums">{meta}</span>}
        </header>

        <div className="flex flex-col gap-2.5 border-b border-hairline pt-14 pb-10">
          <h1 className="m-0 font-serif text-[clamp(2.5rem,7vw,4.25rem)] leading-[1.02] font-normal tracking-[-0.02em]">
            {title}
          </h1>
          {lede !== undefined && (
            <p className="m-0 max-w-[44ch] text-base leading-[1.55] text-muted text-pretty">
              {lede}
            </p>
          )}
        </div>

        {children}

        {footer !== null && <footer className="pt-16 text-xs text-faint">{footer}</footer>}
      </div>
    </div>
  )
}
