"""The one guard between a branch name and a `DROP DATABASE` statement.

A preview's database is named after the branch, and that name reaches
`CREATE DATABASE "<name>"` and `DROP DATABASE "<name>"` **interpolated**, because
PostgreSQL identifiers cannot be bound as parameters. There is no version of this
that is parameterised and safe; there is only a name that was checked and one that
was not.

The attacker model is not the interesting part -- whoever can push a branch can
also edit `app/lambda_handler.py`. What makes this worth its own file is that the
guard is the only thing standing between an ordinary typo and a statement that
means something else, and that the maintenance function it protects runs with the
master password against the cluster every preview shares.
"""

import re

import pytest

from app.lambda_handler import PREVIEW_DATABASE_PATTERN, _checked_preview_database


def test_a_name_made_from_a_slug_is_accepted() -> None:
    """What `scripts/preview.sh` actually produces: lowercase, underscores, a hash."""
    assert _checked_preview_database("preview_fix_toast_9a3f1c") == "preview_fix_toast_9a3f1c"


@pytest.mark.parametrize(
    "name",
    [
        pytest.param('preview_x"; DROP DATABASE app; --', id="closes-the-identifier"),
        pytest.param("preview_x; DROP DATABASE app", id="statement-separator"),
        pytest.param("preview_x\\", id="backslash"),
        pytest.param("preview_x\nDROP DATABASE app", id="newline"),
    ],
)
def test_a_name_that_could_end_the_identifier_is_refused(name: str) -> None:
    """The literal that motivates the pattern, kept as a test rather than as a comment."""
    with pytest.raises(ValueError):
        _checked_preview_database(name)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("app", id="the-maintenance-database"),
        pytest.param("postgres", id="the-cluster-default"),
        pytest.param("", id="empty"),
        pytest.param("preview_", id="prefix-alone"),
        pytest.param("Preview_x", id="uppercase"),
        pytest.param("preview_" + "x" * 41, id="over-length"),
    ],
)
def test_a_name_that_is_not_a_preview_is_refused(name: str) -> None:
    """The prefix lives inside the pattern, so no accepted name can be somebody else's.

    `app` is the database the maintenance function is itself connected to, and the
    one every preview is created from. A guard that checked only for quoting would
    let a caller drop it.
    """
    with pytest.raises(ValueError):
        _checked_preview_database(name)


def test_a_value_that_is_not_a_string_is_refused() -> None:
    """The name arrives inside a Lambda event payload, which is whatever was sent."""
    with pytest.raises(ValueError):
        _checked_preview_database(None)


def test_the_refusal_names_the_rule_it_applied() -> None:
    """So the fix is visible from the log line, without opening this file."""
    #: Escaped, because the pattern is being looked for as a literal inside the
    #: message rather than applied as a regex to it -- its own anchors would
    #: otherwise refuse to match anything but the whole string.
    with pytest.raises(ValueError, match=re.escape(PREVIEW_DATABASE_PATTERN.pattern)):
        _checked_preview_database("nope")
