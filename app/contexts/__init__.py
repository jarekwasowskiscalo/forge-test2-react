"""Every bounded context, one package each, and the aggregate that finds them.

A context is a directory here and nothing else is. What that buys is the thing a
layer-first tree cannot give: a **path that holds one context and nothing else**,
so `.github/CODEOWNERS` can hand a context to a person or a team without handing
them a quarter of every other context as well.

**Importing this package imports every context**, which is how `Base.metadata`
comes to know every table before Alembic autogenerates against it
(`alembic/env.py`). The list below is explicit and one line per context, rather
than a directory walk, for the reason the change registry is written
in contiguous per-change blocks (the process's `sdd-architecture.md` § 4): two people adding two contexts append at different
points of one short list, and git's ordinary text merge resolves it. Discovery
would remove the merge and take something with it -- with an explicit list,
`tests/fitness/test_context_boundaries.py` can check BOTH directions, and a
context that exists but was never registered is exactly as loud as a registration
with no context behind it.
"""

from app.contexts import guestbook, todo_list

__all__ = ["guestbook", "todo_list"]
