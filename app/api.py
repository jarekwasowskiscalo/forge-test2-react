"""Aggregates every router into the single `api_router`.

`app.main` mounts this one router under the `/api` prefix, ahead of the
static-asset mount and the SPA catch-all. Keeping the aggregation here (and not
in `main.py`) means the prefix is applied in exactly one place, so a new resource
router cannot accidentally land outside `/api` and get swallowed by the
catch-all -- which returns `index.html` with status 200, so the symptom is not a
404 but the frontend failing on `JSON.parse("<!doctype ...")`.

This module is the **composition root** and the one place allowed to reach into a
context's router module. A context's own package (`app/contexts/<name>/`) exports
its domain and not its wiring: a neighbouring context has business with a
`GuestbookEntry` and none whatever with the function that binds it to a URL.
`tests/fitness/test_context_boundaries.py` holds both halves -- the boundary, and
this named exception to it.

One line per context, listed rather than discovered. Two people adding two
contexts append at different points of one short list and git resolves it, which
is the argument the process's `sdd-architecture.md` § 4 already makes for the
change registry's contiguous blocks; and an explicit list is checkable in both
directions, so a context that exists and was never registered fails as loudly as
a registration with nothing behind it.

There is no access check on this aggregate and no session anywhere in this
template: the guestbook is public by design. If your product needs
authentication, this is where the dependency hangs -- once, on the aggregate,
never per resource router, because a router added later would otherwise stay open
until somebody remembered.
"""

from fastapi import APIRouter

from app.contexts.guestbook.routers import guestbook_entries
from app.platform.routers import health

api_router = APIRouter()

# Platform first: liveness answers before any domain rule can be reached.
api_router.include_router(health.router)

# One line per bounded context, in the order they were added.
api_router.include_router(guestbook_entries.router)

__all__ = ["api_router"]
