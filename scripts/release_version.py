"""Semantic version arithmetic, and nothing else.

One verb. **`next`** computes the version after a bump, and the parse is strict on
purpose: `v1.2` or `v1.2.3-rc1` are refused rather than coerced, because a loose
parse turns a pre-release tag into a wrong major and nobody reads a version number
until it is already published.

There used to be a second verb, `write`, which put the computed version into
`pyproject.toml`'s `[project]` table. It is gone, and its absence is the fix rather
than a tidy-up: the commit that carried that edit staged `pyproject.toml` alone, so
`uv.lock` -- which holds the project's version as checked metadata -- was left
naming the version before it, and `uv sync --locked` failed on every commit a
release produced. A release now records its version in the tag and nowhere else,
so there is no second copy to keep in step.

Run through `scripts/release.sh`, which is the thing with the git safety checks.
"""

import argparse
import re
import sys

#: `vX.Y.Z` and nothing else. A tag that says anything more is a tag this does not
#: understand, and saying so is cheaper than guessing.
TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

#: What `next` reports when no release has ever happened, so the first one is
#: deterministic rather than dependent on which tags happen to be in the checkout.
FIRST = "v0.0.0"

BUMPS = ("patch", "minor", "major")


def next_version(bump: str, last: str) -> str:
    """The version after `bump` applied to `last`. Both with a leading `v`."""
    match = TAG.match(last)
    if match is None:
        raise ValueError(
            f"{last!r} is not a release tag. Expected vX.Y.Z -- a pre-release or a "
            "two-part version has to be resolved by a person, not guessed at here."
        )
    major, minor, patch = (int(part) for part in match.groups())

    if bump == "major":
        return f"v{major + 1}.0.0"
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    return f"v{major}.{minor}.{patch + 1}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="verb", required=True)

    following = sub.add_parser("next", help="print the version after a bump")
    following.add_argument("bump", choices=BUMPS)
    following.add_argument("--last", default=FIRST, help=f"the previous tag (default {FIRST})")

    arguments = parser.parse_args(argv)
    try:
        print(next_version(arguments.bump, arguments.last or FIRST))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
