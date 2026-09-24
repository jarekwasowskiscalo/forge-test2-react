import { LinkButton } from '@/components/ui/Button'
import { PageFrame } from '@/components/shell/PageFrame'
import { GUESTBOOK_ROUTE } from '@/routes'

/**
 * Pages outside the normal flow. There is exactly one.
 *
 * It renders **inside** the frame rather than replacing it, so a mistyped
 * address keeps the lockup that gets a person back out. A full-page 404 would
 * strand them with nothing but the browser's Back button.
 */
export function NotFoundPage() {
  return (
    <PageFrame title="Nothing here" lede="There is one screen in this application: the guestbook.">
      <div className="flex justify-center pt-10">
        <LinkButton to={GUESTBOOK_ROUTE}>Go to the guestbook</LinkButton>
      </div>
    </PageFrame>
  )
}
