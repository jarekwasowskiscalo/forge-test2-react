/**
 * Every client-side route, as a constant.
 *
 * A route is the application's composition, not a context's internals: the
 * shell links to it, the 404 page offers it, `router.tsx` binds it, and the
 * screen inside the context navigates back to it. `GUESTBOOK_ROUTE` lived in
 * `components/shell/PageFrame.tsx` until the tree was cut by context, which
 * made a shared layout component the owner of a domain constant and gave every
 * one of those callers a reason to import the shell.
 *
 * Putting it here keeps the dependency pointing the right way. A context may
 * read the route it lives at; nothing shared has to reach into a context to
 * find one.
 *
 * The paths are English, like everything else here
 * (`spec/design/conventions.md` § Language).
 */
export const GUESTBOOK_ROUTE = '/guestbook'
