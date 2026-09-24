import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, it } from 'vitest'

import { NotFoundPage } from './StatusPages'

/**
 * The page a wrong address gets.
 *
 * It said "There is one screen in this application: the guestbook." The to-do
 * list made that false, and `R-5` clause 4 forbids any screen to say it. The
 * replacement counts no screens at all, because a sentence that counts them stops
 * being true again with the next one (`spec/design/ui/system-states.md` § Copy:
 * "The 404 sentence counts no screens").
 *
 * The page still renders inside the frame, with the way back to the guestbook.
 */

it('does not say the application has one screen [req:CR-2609-823a/R-5]', () => {
  const { container } = render(
    <MemoryRouter initialEntries={['/no-such-page']}>
      <NotFoundPage />
    </MemoryRouter>,
  )

  // Nowhere on the page, in any wording that counts one screen.
  expect(container.textContent ?? '').not.toMatch(/one screen/i)
  expect(container.textContent ?? '').not.toMatch(/only screen/i)

  // What it says instead, word for word, and the way back.
  expect(screen.getByRole('heading', { name: 'Nothing here' })).toBeInTheDocument()
  expect(screen.getByText('There is nothing at this address.')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Go to the guestbook' })).toHaveAttribute(
    'href',
    '/guestbook',
  )
})
