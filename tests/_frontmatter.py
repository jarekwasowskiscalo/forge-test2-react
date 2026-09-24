"""The front matter of a specification document, read the one way this template reads it.

A copy of the change process's reader (the engine's `frontmatter.py`),
kept here on purpose: the fitness tests of this application read `spec/contexts/*.md`
declarations and must import nothing of the process -- the process works on this
template, the template does not depend on the process. Two small copies of one parser
are the price of that direction, and `test_context_declarations.py` holds both to the
same answer on every context document.
"""

import pathlib
import re
from typing import Final

FrontMatterValue = str | None | list[str]

_DELIMITER: Final = "---"
_KEY_LINE: Final = re.compile(r"^(?P<key>[a-z_][a-z0-9_]*):\s*(?P<value>.*)$")
_INLINE_LIST: Final = re.compile(r"^\[(?P<body>.*)\]$")


class FrontMatterError(ValueError):
    """A front-matter block this reader will not guess at."""


def _parse_scalar(raw: str) -> FrontMatterValue:
    value = raw.strip()
    if value in {"null", "~", ""}:
        return None
    inline_list = _INLINE_LIST.match(value)
    if inline_list is not None:
        body = inline_list.group("body").strip()
        if not body:
            return []
        return [item.strip().strip("\"'") for item in body.split(",")]
    return value.strip("\"'")


def parse(text: str, *, source: pathlib.Path | None = None) -> dict[str, FrontMatterValue]:
    """The front-matter block of `text`, or `{}` when it has none.

    `source` only ever appears in error messages; it is optional so the parser
    can be tested on a string without inventing a path for it.
    """
    where = f"{source}: " if source is not None else ""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _DELIMITER:
        return {}

    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == _DELIMITER)
    except StopIteration:
        raise FrontMatterError(f"{where}front matter opens with --- and never closes") from None

    parsed: dict[str, FrontMatterValue] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t-":
            raise FrontMatterError(
                f"{where}line {number}: nested or block YAML is not supported here. "
                "Front matter takes flat scalars and inline lists only -- see "
                ".specconf/templates/system/ADR.md."
            )
        match = _KEY_LINE.match(line)
        if match is None:
            raise FrontMatterError(f"{where}line {number}: not a 'key: value' pair -- {line!r}")
        key = match.group("key")
        if key in parsed:
            raise FrontMatterError(f"{where}line {number}: duplicate key {key!r}")
        parsed[key] = _parse_scalar(match.group("value"))
    return parsed


def read(path: pathlib.Path) -> dict[str, FrontMatterValue]:
    """The front-matter block of the file at `path`."""
    return parse(path.read_text(encoding="utf-8"), source=path)


def as_str(value: FrontMatterValue) -> str:
    """A scalar field, flattened for display. A list or a null renders empty."""
    return value if isinstance(value, str) else ""


def as_list(value: FrontMatterValue) -> list[str]:
    """A list field. A scalar counts as a one-element list; a null as none."""
    if isinstance(value, list):
        return value
    return [value] if isinstance(value, str) else []
