"""The to-do list context: what the rest of the application may know about it.

**This module is the context's public API, and the boundary is real rather than
advisory.** `tests/fitness/test_context_boundaries.py` refuses an import of
`app.contexts.todo_list.<anything>` from any other context -- only this package may
be imported, and only what is re-exported here can be reached.

It re-exports the model and the two constants beside it: the bound of a task's text
and the seven line breaks a task may not hold inside it. Nothing else crosses. The
one rule this context shares with the guestbook -- how a text is normalized, trimmed
and measured -- is not the guestbook's to export and not this context's either: it is
the shared kernel in `app/platform/schemas/text.py`, which both import
(`spec/contexts/todo_list.md` § Neighbours).

Importing this package imports the model below it, which is what registers
`todo_tasks` on the shared `Base` before Alembic looks at the metadata.

The routers are deliberately **not** re-exported. `app/api.py` is the composition
root and reaches the router module directly; a context exports its domain, not its
wiring.

The specification for everything here: `spec/contexts/todo_list.md`.
"""

from app.contexts.todo_list.models.todo_task import (
    LINE_BREAKS,
    TODO_TASK_TEXT_MAX_LENGTH,
    TodoTask,
)

__all__ = [
    "LINE_BREAKS",
    "TODO_TASK_TEXT_MAX_LENGTH",
    "TodoTask",
]
