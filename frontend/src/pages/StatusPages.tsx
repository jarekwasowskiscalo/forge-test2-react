import { LinkButton } from '@/components/ui/Button'
import { PageFrame } from '@/components/shell/PageFrame'
import { GUESTBOOK_ROUTE } from '@/routes'

/**
 * Pages outside the normal flow. There is exactly one.
 *
 * It renders **inside** the frame rather than replacing it, so a mistyped
 * address keeps the lockup and the navigation to every screen -- neither marked as
 * the one on show. A full-page 404 would strand a person with nothing but the
 * browser's Back button.
 *
 * **Its sentence counts no screens.** It said "There is one screen in this
 * application: the guestbook." until the to-do list made that false, and a
 * sentence that counts the screens stops being true again with the next one
 * (`spec/design/ui/system-states.md` § Copy). It has no footer: the footer is a
 * screen's sentence about who sees what is on it, and nothing is on this one.
 */
export function NotFoundPage() {
  return (
    <PageFrame title="Nothing here" lede="There is nothing at this address." footer={null}>
      <div className="flex justify-center pt-10">
        <LinkButton to={GUESTBOOK_ROUTE}>Go to the guestbook</LinkButton>
      </div>
    </PageFrame>
  )
}
