"""The corpus's FIXTURE half, for the black box.

A thin wrapper over `tests/_golden_set.py`: it adds **nothing** about where the
corpus is, and that is the whole point. There used to be a hand-copied twin of
the locator here, because this suite ran in a virtualenv it could not import
`tests/` from; the copies were guarded by an equality check on the directory they
resolved to, and by the time the twin was deleted they had diverged in return
type, in exception type, and in what the failure listed -- none of which that
check could see.

So this module is **the one place `e2e/` reaches into first-party code**, named
as the single exception in `tests/fitness/test_e2e_isolation.py`. It is safe
because `tests/_golden_set.py` imports nothing but `json`, `pathlib` and
`typing`: no application, no fixture, no database. A second crossing added here
would be a scenario that can reach the same objects the application does, and
such a scenario passes while the wire is broken.

What this file may grow: shapes the black box posts. It may never grow knowledge
of *where* the corpus is, or of what an entry means -- the first belongs to the
locator, the second to the step definitions.

**And it may never grow the seed half.** `golden-set/seed/` is what a deployed
environment was filled with at creation; a scenario reaching for it would be
asserting about another process's state, in a suite that truncates the world
before every scenario. `tests/fitness/test_golden_set.py` refuses it from the
other side too.
"""

import pathlib
from typing import Any, Final

from tests._golden_set import BOUNDARY, ORDINARY, REFUSED, case, described, entries_of

__all__ = [
    "BOUNDARY",
    "ORDINARY",
    "REFUSED",
    "bodies_of",
    "body_of",
    "case",
    "described",
    "entries_of",
]

#: The two keys the write endpoint takes. Named so a corpus entry carrying
#: bookkeeping of its own (`case`, `refusal`) cannot leak into a request body --
#: the API refuses unknown fields silently by ignoring them, so the leak would
#: not fail, it would just stop being the request the scenario meant to send.
_BODY_KEYS: Final[tuple[str, str]] = ("author", "message")


def body_of(entry: dict[str, Any]) -> dict[str, str]:
    """One corpus entry as the JSON body `POST /guestbook-entries` accepts."""
    return {key: entry[key] for key in _BODY_KEYS}


def bodies_of(path: pathlib.Path) -> list[dict[str, str]]:
    """Every entry of one corpus file, as request bodies, in file order."""
    return [body_of(entry) for entry in entries_of(path)]
