"""The guestbook context: what the rest of the application may know about it.

**This module is the context's public API, and the boundary is real rather than
advisory.** `tests/fitness/test_context_boundaries.py` refuses an import of
`app.contexts.guestbook.<anything>` from any other context -- only this package
may be imported, and only what is re-exported here can be reached. The rule is
sdd31's, and it exists because an agent feels no cultural friction: it can wire
itself into the deepest undocumented method of a neighbouring package in seconds,
pass every local test, and leave the architecture broken in a way no diff shows.

Importing this package imports the models below it, which is what registers
`guestbook_entries` on the shared `Base` before Alembic looks at the metadata.

The routers are deliberately **not** re-exported. `app/api.py` is the composition
root and reaches the router module directly; a context exports its domain, not
its wiring, and the two are different audiences.

The specification for everything here: `spec/contexts/guestbook.md`.
"""

from app.contexts.guestbook.models.guestbook_entry import (
    AUTHOR_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
    GuestbookEntry,
)

__all__ = [
    "AUTHOR_MAX_LENGTH",
    "MESSAGE_MAX_LENGTH",
    "GuestbookEntry",
]
