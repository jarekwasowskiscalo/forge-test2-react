"""The contract's bounds have one home each and one named copy, and the copies are checked.

`spec/design/data-model.md` says `AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH` live next
to the model and are imported from there, so a value reaching the database by any route
is bound by the same number; `PAGE_SIZE_MAX`, the largest page the list may ask for, lives
beside the schemas. The browser cannot import Python, so
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts` carries the same numbers as copies --
and the same document names them as the one exception, legal only because this file holds
the two sides equal. The page bound joined the list on 2026-09-08, when an audit found it
copied as a bare `100` in a hook, bound by nothing.

Why it has to be a test rather than a comment: the generated contract
(`frontend/src/api/schema.d.ts`) carries no `maxLength`, so nothing at build time ties
the TypeScript literal to the Pydantic one. Move the bound on one side and the screen
refuses an entry the API would accept, or accepts one the API refuses -- with a green
suite on both sides, because each side's tests read its own constant.

The values are read from source as text, not imported: importing the model would pull
SQLAlchemy into a fitness test, and the point is the *literal*, the thing a reader edits.
"""

import re
from typing import Final

from tests._repo import REPO_ROOT

GUESTBOOK: Final = REPO_ROOT / "app" / "contexts" / "guestbook"
BROWSER_COPY: Final = (
    REPO_ROOT / "frontend" / "src" / "contexts" / "guestbook" / "lib" / "guestbookEntry.ts"
)
#: Each bound and the Python file that is its home.
HOMES: Final = {
    "AUTHOR_MAX_LENGTH": GUESTBOOK / "models" / "guestbook_entry.py",
    "MESSAGE_MAX_LENGTH": GUESTBOOK / "models" / "guestbook_entry.py",
    "PAGE_SIZE_MAX": GUESTBOOK / "schemas" / "guestbook_entries.py",
}


def _literal(text: str, prefix: str, name: str) -> int:
    match = re.search(rf"^{prefix}{name}\s*=\s*(\d+)\s*$", text, flags=re.MULTILINE)
    assert match, f"{name} is not declared as a bare integer literal"
    return int(match.group(1))


def _python_side() -> dict[str, int]:
    return {
        name: _literal(home.read_text(encoding="utf-8"), "", name) for name, home in HOMES.items()
    }


def _browser_side(text: str) -> dict[str, int]:
    return {name: _literal(text, "export const ", name) for name in HOMES}


def test_the_browser_copies_of_the_bounds_equal_their_homes() -> None:
    python = _python_side()
    browser = _browser_side(BROWSER_COPY.read_text(encoding="utf-8"))
    assert browser == python, (
        f"the browser copies {browser} drifted from their homes {python}; "
        "spec/design/data-model.md allows the copies only while this holds"
    )


def test_the_detector_would_see_a_drift() -> None:
    """A detector arrives with proof that it fires."""
    drifted = BROWSER_COPY.read_text(encoding="utf-8").replace(
        "AUTHOR_MAX_LENGTH = 80", "AUTHOR_MAX_LENGTH = 81"
    )
    assert _browser_side(drifted) != _python_side()


def test_the_page_bound_has_no_other_copy_in_the_browser() -> None:
    """The literal that was found copied as a bare number: nothing under the context may
    write the page bound as `100` again -- it reads the named constant."""
    hooks = REPO_ROOT / "frontend" / "src" / "contexts" / "guestbook" / "hooks"
    for path in sorted(hooks.glob("*.ts")):
        if path.name.endswith(".test.ts"):
            continue
        assert not re.search(r"Math\.min\([^)]*\b100\b", path.read_text(encoding="utf-8")), (
            f"{path.name} clamps with a bare 100; use PAGE_SIZE_MAX from lib/guestbookEntry.ts"
        )
