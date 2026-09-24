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

**The to-do list's two constants joined on 2026-09-24 (`CR-2609-823a`)**, each with its
one browser copy in the to-do list's own rule, `frontend/src/contexts/todo_list/lib/todoTask.ts`:
the bound of a task's text, and the seven line breaks a task may not carry inside it
(`BR-07`). The seven are a SET, not a number, and they are copied for the same reason the
bound is: the screen refuses a pasted line break before sending, so a copy that lost one
of the seven lets through a text the service refuses, and a copy that gained one refuses
a text the service would store. The shape each side is read in, for whoever writes them:

- **the bound**, a bare integer literal at the start of its line, as the guest book's
  are -- `TODO_TASK_TEXT_MAX_LENGTH = 200` beside `TodoTask` in
  `app/contexts/todo_list/models/todo_task.py`, and
  `export const TODO_TASK_TEXT_MAX_LENGTH = 200` in the browser copy;
- **the line breaks**, written as code-point NUMBERS the way the kernel writes its trim
  set (`app/platform/schemas/text.py`), one assignment at the start of its line. In
  Python, a parenthesized tuple, an annotation allowed::

      LINE_BREAKS: Final[tuple[int, ...]] = (
          0x000A,  # line feed
          ...
      )

  and in the browser copy a plain array literal, an annotation or `as const` allowed::

      export const LINE_BREAKS: readonly number[] = [
        0x000a, // line feed
        ...
      ]

  Every element is an integer literal -- hexadecimal (`0x...`) or decimal -- separated
  by commas, a trailing comma allowed; comments (`#`, `//`, `/* */`) are ignored, and
  anything else between the brackets -- a name, a string, a call -- is refused as not
  written as a number. The two are compared as sets of code points, order aside.

Neither half of the to-do list exists until the implementation wave writes it, so both of
its cases are red until both files do; a missing file fails the case that reads it, with
its path, rather than the module.
"""

import pathlib
import re
from typing import Final

import pytest

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


# --------------------------------------------------------------------------- #
# The to-do list's bound and line breaks (`CR-2609-823a`)
# --------------------------------------------------------------------------- #

#: The home of both to-do constants: beside `TodoTask` (`spec/design/data-model.md`
#: § `todo_tasks`).
TODO_HOME: Final = REPO_ROOT / "app" / "contexts" / "todo_list" / "models" / "todo_task.py"
#: Their one browser copy: the to-do list's own rule, beside its verdict.
TODO_BROWSER_COPY: Final = (
    REPO_ROOT / "frontend" / "src" / "contexts" / "todo_list" / "lib" / "todoTask.ts"
)

#: `LINE_BREAKS = (...)` at the start of a line in Python, an annotation allowed.
_PYTHON_LINE_BREAKS: Final = re.compile(
    r"^LINE_BREAKS\b[^=\n]*=\s*\((?P<body>[^)]*)\)", flags=re.MULTILINE
)
#: `export const LINE_BREAKS = [...]` at the start of a line, an annotation allowed.
_BROWSER_LINE_BREAKS: Final = re.compile(
    r"^export const LINE_BREAKS\b[^=\n]*=\s*\[(?P<body>[^\]]*)\]", flags=re.MULTILINE
)
#: One element of the set: an integer literal, hexadecimal or decimal.
_CODE_POINT: Final = re.compile(r"0[xX][0-9a-fA-F]+|\d+")


def _source(path: pathlib.Path) -> str:
    """One of the two files, or a failure naming it -- never a bare FileNotFoundError."""
    assert path.is_file(), (
        f"{path.relative_to(REPO_ROOT).as_posix()} does not exist -- the constant and its "
        "copy are compared only once both are written"
    )
    return path.read_text(encoding="utf-8")


def _code_points(text: str, declaration: re.Pattern[str], comment: str) -> list[int]:
    """The code points one side's `LINE_BREAKS` literal lists, in the shape the docstring gives.

    Comments are removed first, so a `# line feed (LF)` or a `// U+2028` beside an element
    is neither an element nor the end of the list.
    """
    without_blocks = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    uncommented = re.sub(re.escape(comment) + r"[^\n]*", "", without_blocks)
    match = declaration.search(uncommented)
    assert match, "LINE_BREAKS is not declared as one literal list at the start of its line"
    elements = [element.strip() for element in match.group("body").split(",")]
    code_points: list[int] = []
    for element in (element for element in elements if element):
        assert _CODE_POINT.fullmatch(element), (
            f"LINE_BREAKS lists {element!r}, which is not written as a number"
        )
        code_points.append(int(element, 16) if element[:2].lower() == "0x" else int(element))
    return code_points


def test_the_task_bound_equals_its_browser_copy() -> None:
    """`TODO_TASK_TEXT_MAX_LENGTH` beside `TodoTask`, and its copy in the to-do list's rule.

    Its own case rather than a fourth row of `HOMES`: the guest book's three share one
    browser file, and the to-do list's copy lives in its own context's folder, which the
    guest book's may not import. Never compared with `QUERY_MAX_LENGTH`, which is also
    200 -- two rules sharing a number, and moving one moves nothing on the other side.
    """
    python = _literal(_source(TODO_HOME), "", "TODO_TASK_TEXT_MAX_LENGTH")
    browser = _literal(_source(TODO_BROWSER_COPY), "export const ", "TODO_TASK_TEXT_MAX_LENGTH")

    assert browser == python, (
        f"the browser copy of TODO_TASK_TEXT_MAX_LENGTH is {browser} and its home says "
        f"{python}; spec/design/data-model.md allows the copy only while this holds"
    )


def test_the_line_breaks_equal_their_browser_copy() -> None:
    """`LINE_BREAKS` beside `TodoTask`, and its copy in the to-do list's rule, as one set.

    Non-empty on both sides first: two literals that both failed to list anything would
    otherwise be equal, and this would pass on the very state it exists to refuse.
    """
    python = _code_points(_source(TODO_HOME), _PYTHON_LINE_BREAKS, "#")
    browser = _code_points(_source(TODO_BROWSER_COPY), _BROWSER_LINE_BREAKS, "//")

    assert python and browser, "a LINE_BREAKS literal lists no code point"
    assert sorted(browser) == sorted(python), (
        f"the browser copy of LINE_BREAKS lists {[f'U+{c:04X}' for c in sorted(browser)]} "
        f"and its home {[f'U+{c:04X}' for c in sorted(python)]}; the screen and the "
        "service must refuse the same line breaks"
    )


def test_the_line_break_reader_would_see_a_drift() -> None:
    """A detector arrives with proof that it fires -- on the shapes the docstring gives.

    Written here rather than read from the two files, so it holds before they exist: the
    reader finds the seven through comments that carry numbers and brackets of their own,
    sees a copy that lost one, and refuses an element that is not written as a number.
    """
    python = (
        "LINE_BREAKS: Final[tuple[int, ...]] = (  # the seven (A-1)\n"
        "    0x000A,  # line feed (LF), U+000A\n"
        "    0x000B,\n    0x000C,\n    0x000D,\n    0x0085,\n    0x2028,\n    0x2029,\n)\n"
    )
    browser = (
        "/** The seven (A-1) -- U+2028 [LS] among them. */\n"
        "export const LINE_BREAKS: readonly number[] = [\n"
        "  0x000a, // line feed [LF]\n  0x000b, 0x000c, 0x000d, 0x0085, 0x2028, 0x2029,\n"
        "] as const\n"
    )
    seven = [0x000A, 0x000B, 0x000C, 0x000D, 0x0085, 0x2028, 0x2029]

    assert _code_points(python, _PYTHON_LINE_BREAKS, "#") == seven
    assert _code_points(browser, _BROWSER_LINE_BREAKS, "//") == seven
    drifted = browser.replace("0x0085, ", "")
    assert sorted(_code_points(drifted, _BROWSER_LINE_BREAKS, "//")) != seven
    with pytest.raises(AssertionError, match="not written as a number"):
        _code_points(python.replace("0x2029", "PARAGRAPH_SEPARATOR"), _PYTHON_LINE_BREAKS, "#")
