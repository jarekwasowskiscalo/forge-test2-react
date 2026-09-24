"""How a list answer is read.

This module knows exactly one thing about the application, and it is a fact
about the wire rather than about the domain: a list answer is either a bare
array or `{"items": [...], "total": N}`. One collection endpoint is the one
that can report the whole-population count, so it does; the others still answer
an array. Unwrapping here rather than at each call site means a second endpoint
gaining an envelope is one edit.

It exists because the alternative was measured. `len(response.json())` over
`{"items": [...], "total": 19}` is **2**, and 2 is a plausible number of rows,
so `Then only 2 entries should be returned` could pass against a page of fifty.
One reader for both shapes is what makes that unrepresentable rather than
unlikely.

No test framework in the harness.
"""

from collections.abc import Mapping
from typing import Final

from e2e.harness.client import Answer, Row

#: The key a paged endpoint puts its rows under.
_ITEMS: Final[str] = "items"

#: The key beside it, carrying the size of the whole population rather than of
#: this page.
_TOTAL: Final[str] = "total"


def rows(answer: Answer) -> list[Row]:
    """The rows of a list answer, whichever shape the endpoint used.

    Raises rather than returning `[]` when the payload is neither: an answer
    that is not a list at all means the request was wrong, and a silent empty
    list turns that into "expected 19, got 0" -- a message about the data when
    the fault is in the question.
    """
    payload = answer.payload
    if isinstance(payload, Mapping) and _ITEMS in payload:
        payload = payload[_ITEMS]
    if not isinstance(payload, list):
        raise AssertionError(f"expected a list of rows, but {answer} answered")
    return [row for row in payload if isinstance(row, Mapping)]


def total_of(answer: Answer) -> int:
    """The whole-population count an enveloped list answer reports.

    Deliberately **not** falling back to `len(rows(answer))`. `total` is the one
    number on this envelope a page cannot imply -- which is the entire reason the
    envelope exists -- so answering the page length when the field is absent
    would make the assertion that checks `total` pass against an endpoint that
    had stopped sending it. An endpoint with no envelope is the wrong endpoint to
    ask, and says so.
    """
    payload = answer.payload
    if not isinstance(payload, Mapping) or _TOTAL not in payload:
        raise AssertionError(
            f"expected a list answer carrying a whole-population count, but {answer} "
            "answered. Only an enveloped endpoint reports one; a bare array cannot."
        )
    reported = payload[_TOTAL]
    #: `bool` is an `int` in Python, and `{"total": true}` is a wire defect rather
    #: than a count of one.
    if not isinstance(reported, int) or isinstance(reported, bool):
        raise AssertionError(f"the whole-population count is not a number: {reported!r}")
    return reported


def row_where(answer: Answer, **criteria: str) -> Row | None:
    """The first row whose every named field stringifies to the given value.

    Filtering by a stable field rather than reading index 0, because a list
    endpoint promises an order only as far as its `ORDER BY` is total -- and for
    five months neither list endpoint had a tiebreaker, so two rows
    sharing a date came back in either order.

    Returns `None` rather than raising, so each caller can phrase the miss in
    its own domain words; `assertions.found` turns it into a sentence.
    """
    for row in rows(answer):
        if all(str(row.get(field)) == value for field, value in criteria.items()):
            return row
    return None
