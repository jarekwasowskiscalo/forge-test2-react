import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it } from 'vitest'

import { PageFrame } from './PageFrame'

/**
 * The frame every screen renders itself inside, and the one seam that learned
 * about a second screen (`spec/design/ui/system-states.md` § One column).
 *
 * `R-5` clause 2: on the guestbook and on the to-do list alike, the way to the
 * other screen is on screen, and it takes no typed address. The way is two text
 * links beside the lockup, in a group assistive technology reads as "Screens";
 * the link of the screen on show stays a link and is marked as the current page
 * rather than removed (§ The navigation between the screens).
 *
 * The frame reads nothing, so it is rendered here with two stand-in screens at
 * the two addresses, and the links are followed rather than inspected: a link
 * that points at the right address and does not navigate is not a way anywhere.
 * The words are § Copy's, verbatim.
 */

/** The navigation group, named "Screens" -- a `<nav>` or any element in the `group` role. */
function screensGroup(): HTMLElement {
  return (
    screen.queryByRole('navigation', { name: 'Screens' }) ??
    screen.getByRole('group', { name: 'Screens' })
  )
}

function renderBothScreens(at: string) {
  render(
    <MemoryRouter initialEntries={[at]}>
      <Routes>
        <Route
          path="/guestbook"
          element={
            <PageFrame title="The guestbook, standing in">
              <p>The guestbook's content.</p>
            </PageFrame>
          }
        />
        <Route
          path="/todo-list"
          element={
            <PageFrame title="The to-do list, standing in">
              <p>The to-do list's content.</p>
            </PageFrame>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
  return userEvent.setup()
}

it('offers the way to the other screen on each screen [req:CR-2609-823a/R-5]', async () => {
  const user = renderBothScreens('/guestbook')
  expect(screen.getByRole('heading', { name: 'The guestbook, standing in' })).toBeInTheDocument()

  // On the guestbook: the way to the to-do list, and the guestbook marked as the
  // screen on show.
  let links = within(screensGroup())
  expect(links.getByRole('link', { name: 'To-do list' })).toHaveAttribute('href', '/todo-list')
  expect(links.getByRole('link', { name: 'To-do list' })).not.toHaveAttribute('aria-current')
  expect(links.getByRole('link', { name: 'Guestbook' })).toHaveAttribute('aria-current', 'page')

  await user.click(links.getByRole('link', { name: 'To-do list' }))

  // Followed, with no address typed: the to-do list, with the way back.
  expect(
    await screen.findByRole('heading', { name: 'The to-do list, standing in' }),
  ).toBeInTheDocument()
  links = within(screensGroup())
  expect(links.getByRole('link', { name: 'Guestbook' })).toHaveAttribute('href', '/guestbook')
  expect(links.getByRole('link', { name: 'Guestbook' })).not.toHaveAttribute('aria-current')
  expect(links.getByRole('link', { name: 'To-do list' })).toHaveAttribute('aria-current', 'page')

  await user.click(links.getByRole('link', { name: 'Guestbook' }))

  expect(
    await screen.findByRole('heading', { name: 'The guestbook, standing in' }),
  ).toBeInTheDocument()

  // The lockup names the product, not one of its screens -- "Guestbook" there
  // stood beside a navigation link of the same name -- and it still leads to the
  // guestbook, on every screen.
  expect(screen.getByRole('link', { name: 'Product name' })).toHaveAttribute('href', '/guestbook')
  expect(screen.getAllByRole('link', { name: 'Guestbook' })).toHaveLength(1)
})
