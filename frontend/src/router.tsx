import { createBrowserRouter, Navigate } from 'react-router-dom'

import { GUESTBOOK_ROUTE } from '@/routes'
import { GuestbookPage } from '@/contexts/guestbook/pages/GuestbookPage'
import { NotFoundPage } from '@/pages/StatusPages'

/**
 * Client-side routes. The server returns the same empty shell for every one of
 * these paths (see app/main.py) -- nothing is server-rendered, and there is no
 * per-page HTML to keep in sync.
 *
 * **There is no layout route.** Each screen renders its own `PageFrame`,
 * because the frame is a page's own header and footer rather than a shell the
 * pages live inside -- and a layout route with one child is indirection with
 * nothing on the other side of it.
 *
 * **The route is English, like everything else here** (`spec/design/conventions.md`
 * § Language). It was Polish until 2026-09-02, on the argument that a route is text
 * a person reads and says out loud and this one was already written down, linked
 * and bookmarked. That argument was true and was outweighed: the seam it bought --
 * an English screen at a Polish address -- costs a reading every time, while
 * breaking the links costs once.
 *
 * `/` redirects rather than rendering the screen at two addresses. Two URLs for
 * one screen is two things to keep working, and the one nobody links to is the
 * one that quietly breaks.
 */
export const router = createBrowserRouter([
  { path: '/', element: <Navigate to={GUESTBOOK_ROUTE} replace /> },
  { path: GUESTBOOK_ROUTE, element: <GuestbookPage /> },
  { path: '*', element: <NotFoundPage /> },
])
