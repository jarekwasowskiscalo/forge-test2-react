"""Version arithmetic, and the refusal that keeps a wrong version from being published.

A loose tag parse is the thing a shell one-liner gets wrong in a way nobody notices
until a release is already out: `v1.2.3-rc1` read as `1.2.3` turns a pre-release
into a real one, and `v1.2` read as `1.2.0` silently invents a patch level. A
refusal is the only honest answer to a tag this does not understand.

This file used to have a second half, about an edit to `pyproject.toml` scoped to a
table rather than to a line. That edit is gone -- `release.sh` writes no version
anywhere, because the commit carrying it could never reach the trunk and left
`uv.lock` naming the version before it. The tag is the only record of a release now,
so there is no second copy and no edit to keep narrow.
"""

import pytest

#: Imported by its own name, as `tests/tooling/test_app_status.py` does: pytest's
#: `pythonpath` in pyproject.toml already puts `scripts/` on the path, and reaching
#: for `scripts.release_version` instead makes mypy see one file under two module
#: names and stop checking the tree.
from release_version import next_version


@pytest.mark.parametrize(
    ("bump", "last", "expected"),
    [
        ("patch", "v1.2.3", "v1.2.4"),
        ("minor", "v1.2.3", "v1.3.0"),
        ("major", "v1.2.3", "v2.0.0"),
        ("patch", "v0.0.0", "v0.0.1"),
        ("minor", "v0.9.9", "v0.10.0"),
        ("major", "v9.9.9", "v10.0.0"),
    ],
)
def test_the_arithmetic(bump: str, last: str, expected: str) -> None:
    """Including the two carries a string comparison would get wrong: 9 -> 10."""
    assert next_version(bump, last) == expected


@pytest.mark.parametrize(
    "last",
    ["v1.2", "1.2.3", "v1.2.3-rc1", "v1.2.3+build", "release-1.2.3", ""],
)
def test_a_tag_this_does_not_understand_is_refused(last: str) -> None:
    """Rather than coerced. A wrong version is published before anybody reads it."""
    with pytest.raises(ValueError):
        next_version("patch", last)
