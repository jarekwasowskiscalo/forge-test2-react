import { createBrowserRouter, Navigate } from 'react-router-dom'

import { GUESTBOOK_ROUTE, TODO_LIST_ROUTE } from '@/routes'
import { GuestbookPage } from '@/contexts/guestbook/pages/GuestbookPage'
import { TodoListPage } from '@/contexts/todo_list/pages/TodoListPage'
import { NotFoundPage } from '@/pages/StatusPages'

/**
 * Client-side routes, and the composition root: the one module that binds a path
 * to a context's screen (`spec/design/conventions.md` § Frontend,
 * `tests/fitness/test_context_boundaries.py`). Two screens, one per context -- the
 * guestbook and the to-do list -- and each context takes one line here.
 *
 * The server returns the same empty shell for every one of these paths (see
 * app/main.py) -- nothing is server-rendered, and there is no per-page HTML to
 * keep in sync.
 *
 * **There is no layout route.** Each screen renders its own `PageFrame`,
 * because the frame is a page's own header and footer rather than a shell the
 * pages live inside -- and a layout route is indirection the pages do not need:
 * the frame reads nothing, so there is nothing for a shared parent to hold.
 *
 * **The routes are English, like everything else here** (`spec/design/conventions.md`
 * § Language). The guestbook's was Polish until 2026-09-02, on the argument that a
 * route is text a person reads and says out loud and this one was already written
 * down, linked and bookmarked. That argument was true and was outweighed: the seam it
 * bought -- an English screen at a Polish address -- costs a reading every time,
 * while breaking the links costs once.
 *
 * `/` redirects to the guestbook rather than rendering a screen at two addresses
 * (`spec/design/ui/system-states.md` § Interactions; `CR-2609-823a`, `Q-5`). Two
 * URLs for one screen is two things to keep working, and the one nobody links to
 * is the one that quietly breaks.
 */
export const router = createBrowserRouter([
  { path: '/', element: <Navigate to={GUESTBOOK_ROUTE} replace /> },
  { path: GUESTBOOK_ROUTE, element: <GuestbookPage /> },
  { path: TODO_LIST_ROUTE, element: <TodoListPage /> },
  { path: '*', element: <NotFoundPage /> },
])
