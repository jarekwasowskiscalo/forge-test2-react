"""The sentences a failure is allowed to be.

Two reasons this module exists, and the second is the load-bearing one.

**It collapses the duplication.** The suite this replaces had about thirty
assertion bodies that differed only by a dict key and a noun -- five for the
import counters, four more for the same counters read back off the batch, four
for one entity's fields, five for another's. Each one restated the comparison and
the f-string. The business-language requirement constrains the Gherkin, not the
number of Python functions underneath it.

**pytest does not rewrite these asserts.** Assertion rewriting reaches modules
matching `python_files`, `conftest.py`, and whatever is passed to
`register_assert_rewrite`. `e2e/suite/steps/*.py` is none of those, so a bare
`assert actual == expected` there prints its message and nothing else -- no
introspected repr of both sides. That is exactly what keeps a page of real
records out of the JUnit `<failure>` element, and it is invisible unless it is
written down, so: **every assertion in a step module goes through this module.**

`should_be` does interpolate the one field value under assertion. That value is
already written in the `.feature` file and already in git; a whole response body
is not, and `Answer` cannot supply one.

No test framework in the harness -- these raise `AssertionError`, not
`pytest.fail`.
"""

from e2e.harness.client import Answer, Row


def should_answer(answer: Answer, expected: int, *, meaning: str) -> None:
    """Assert the status code, in the words of what it means to the business.

    `meaning` is the caller's sentence -- "the import to be refused because that
    day has already been imported" -- because a bare "expected 409, got 201"
    sends the reader to the HTTP spec rather than to the rule that was broken.
    """
    if answer.status != expected:
        raise AssertionError(f"expected {meaning}, got {answer}")


def should_be(actual: object, expected: object, *, subject: str) -> None:
    """Assert one value, naming what it was the value of."""
    if actual != expected:
        raise AssertionError(f"expected {subject} to be {expected!r}, got {actual!r}")


def found(row: Row | None, *, subject: str, answer: Answer) -> Row:
    """Unwrap a `row_where` miss into a sentence, or return the row.

    The answer is named but not quoted: which request came back, and what shape
    it had, is what tells a reader whether the row is missing or the page simply
    did not reach it.
    """
    if row is None:
        raise AssertionError(f"no {subject} in the response. The application answered {answer}")
    return row
