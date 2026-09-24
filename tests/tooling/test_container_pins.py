"""The images a gate builds on are pinned, and the ones named twice agree.

Two rules, both about the same thing: a container image referred to by tag is not
a version, it is a name that points somewhere different next month.

**The Dockerfile's bases are pinned by digest.** CI's `image` job builds that file
and smoke-tests the result, which makes it a gate -- and Article XIII of the
constitution forbids unpinned tool versions in a gate. With a tag, a run that goes
red in October over a base rebuilt in September is a failure with no commit behind
it, which is the exact experience that teaches people to re-run a job rather than
read it.

**The Postgres image has two homes.** `docker-compose.yml` starts one for a
developer and for the end-to-end suite; `tests/_database.py` starts one through
testcontainers for the integration suite. This repository has twice written a test
because one fact had two homes -- the `uv` pin, the `actionlint` pin -- so a third
is warranted rather than novel. Two different Postgres versions across the two
suites is a class of failure that reproduces on exactly one of them.
"""

import re
from typing import Final

from tests._repo import REPO_ROOT

#: `FROM <image>[:tag][@sha256:...] [AS name]`, ignoring `FROM <earlier stage>`.
_FROM: Final = re.compile(r"^FROM\s+(\S+)", re.MULTILINE)

#: Any `postgres:...` reference, wherever it is written.
_POSTGRES: Final = re.compile(r"postgres:[\w.-]+")

#: Where a Postgres image is named. Both start a real server; nothing else does.
_POSTGRES_HOMES: Final = ("docker-compose.yml", "tests/_database.py")


def test_every_base_image_is_pinned_by_digest() -> None:
    """A tag names a moving target, and this file is what CI's `image` gate builds."""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    bases = _FROM.findall(dockerfile)
    assert bases, "the Dockerfile declares no FROM at all"

    unpinned = [base for base in bases if "@sha256:" not in base]
    assert not unpinned, (
        f"{unpinned} name a tag rather than an image. A tag is a different image "
        "next month, so the gate that builds this would be checking something else."
    )


def test_the_tag_is_kept_beside_the_digest() -> None:
    """A digest alone says nothing to a reader about what the image even is.

    `python:3.12-slim@sha256:...` is both: Docker resolves the digest and ignores
    the tag, and a person reading the file learns which base this is without
    fetching anything.
    """
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    for base in _FROM.findall(dockerfile):
        name, _, _ = base.partition("@")
        assert ":" in name, f"{base} pins a digest with no tag beside it to read"


def test_something_proposes_the_bump_the_digest_freezes() -> None:
    """The other half of pinning, and the half that is easy to forget.

    A digest never goes red on its own. Without a proposer, "pinned" quietly
    becomes "has not taken a security fix since the day it was written" -- which is
    a worse position than the moving tag it replaced, and an invisible one.
    """
    dependabot = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: docker" in dependabot, (
        "the base images are pinned by digest and nothing proposes updating them"
    )


def test_both_suites_start_the_same_postgres() -> None:
    """One engine, one version. The alternative reproduces on one suite and not the other."""
    found: dict[str, set[str]] = {}
    for relative in _POSTGRES_HOMES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        images = set(_POSTGRES.findall(text))
        assert images, f"{relative} no longer names a Postgres image where this test looks"
        found[relative] = images

    everything = set().union(*found.values())
    assert len(everything) == 1, (
        f"the suites start different databases: {found}. A failure that reproduces on "
        "one of them and not the other costs an afternoon before anybody looks here."
    )
