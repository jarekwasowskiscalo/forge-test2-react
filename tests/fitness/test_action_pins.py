"""Every action a workflow runs is pinned to a commit, and what may move is named.

A `uses:` on a tag is not a version. `actions/checkout@v7` is whatever that tag points
at this morning, and a tag is a mutable git ref its owner -- or whoever takes their
account -- can move onto other code. What then runs here, on this repository's runners
and with this repository's token, changed with no commit of ours to review. Article
XIII of the constitution refuses unpinned tool versions in a gate, and a workflow step
is the outermost gate there is.

This was the only repository of the three in this family that pinned nothing: 47 steps
across the five workflows, not one on a SHA. The engine states the same rule in
`ci_meta.check_pins`, but it judges the tree the PLUGIN ships from -- its `github_dir()`
walks up from the plugin's own root -- so it has never read a line of this repository.
That is why the rule is restated here, in this template's suite, importing nothing of
the process.

**What may move is listed, not left silent.** The process's two composite actions
resolve at `@main` deliberately, argued where they are used: the process is at 0.x, and
`CLAUDE.md` makes "live the moment they merge there" a property of those two rather
than an oversight. A branch moves more freely than a tag, so this is a real cost taken
on purpose -- and its expiry is written down beside it: pin them the day the process's
version starts meaning something. Naming them here is the whole difference between "we
decided this" and "nobody looked".

The list **clears itself**: a reference that stops needing the exemption fails the
assertion that every entry is still in use, so the exemption cannot outlive its reason.

Discovered rather than listed, the lesson `tests/tooling/test_uv_pin.py` records for
`UV_VERSION`: a workflow added tomorrow is covered without anybody remembering this
file. Discovery can silently find nothing, so the sweep refuses an empty tree.
"""

import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

#: A step's `uses:`, in both spellings a workflow writes it. The reference stops at
#: whitespace, so a trailing `# tag` comment is not part of it.
_USES: Final = re.compile(r"^\s*(?:- )?uses:\s*(?P<ref>\S+)")

#: The 40-character commit a pinned reference ends with -- the same shape the
#: engine's `ci_meta._PINNED` demands, so the two cannot disagree about the form.
_PINNED: Final = re.compile(r"@[0-9a-f]{40}$")

#: The tag kept beside the commit, for a reader. `# v7`, not a bare SHA.
_TAG_BESIDE: Final = re.compile(r"@[0-9a-f]{40}\s+#\s*\S+")

#: References that may move, each with the reason. See the module docstring: these
#: are the process's own composite actions, and the reason is recorded next to them
#: in `ci.yml` along with the condition that ends it.
_MAY_MOVE: Final[dict[str, str]] = {
    "Scalo-Sales-Engineering-Consulting/claude-marketplace/.github/actions/sdd-specs@main": (
        "the process is at 0.x and this template tracks its trunk; pin it the day the "
        "process's version starts meaning something (ci.yml, beside the step)"
    ),
    "Scalo-Sales-Engineering-Consulting/claude-marketplace/.github/actions/sdd-tests@main": (
        "the same decision as sdd-specs, and it has to be the same one: two halves of "
        "the process running from two different commits is not a verdict about either"
    ),
}


def _workflows() -> list[pathlib.Path]:
    paths = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    assert paths, "no workflows found; this test would then pass over nothing"
    return paths


def _steps(text: str) -> list[tuple[str, str]]:
    """Every `uses:` in one workflow, as (reference, the whole line).

    A reference starting `./` is this repository's own file at this repository's own
    commit -- there is nothing to pin and nothing that could move under it.
    """
    found: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _USES.match(line)
        if match is not None and not match.group("ref").startswith("./"):
            found.append((match.group("ref"), line))
    return found


def test_every_action_is_pinned_to_a_commit() -> None:
    """A tag is a name that points somewhere else next month."""
    moving: list[str] = []
    seen = 0
    for path in _workflows():
        for reference, _ in _steps(path.read_text(encoding="utf-8")):
            seen += 1
            if reference in _MAY_MOVE or _PINNED.search(reference):
                continue
            moving.append(f"{path.name}: {reference}")

    assert seen, "no third-party action was found at all, which cannot be true here"
    assert not moving, (
        f"these steps run whatever a tag points at today: {moving}. Pin the "
        "40-character commit and keep the tag in a `#` comment beside it, or name "
        "the reference in _MAY_MOVE with the reason it may."
    )


def test_a_pinned_commit_keeps_its_tag_beside_it() -> None:
    """A bare SHA tells a reader nothing about what the step even is.

    `actions/checkout@3d3c42e... # v7` is both: GitHub resolves the commit and
    ignores the comment, and a person learns which action and which version this is
    without fetching anything. Dependabot reads the comment too -- it is how the
    proposal arrives as "v7 -> v8" rather than as two opaque hashes.
    """
    bare: list[str] = []
    for path in _workflows():
        for reference, line in _steps(path.read_text(encoding="utf-8")):
            if _PINNED.search(reference) and not _TAG_BESIDE.search(line):
                bare.append(f"{path.name}: {line.strip()}")

    assert not bare, (
        f"these pins carry no tag to read: {bare}. Put the tag in a `#` comment after the commit."
    )


def test_every_reference_that_may_move_is_still_used() -> None:
    """The exemption cannot outlive the thing it exempts.

    An entry nothing uses is an exemption nobody re-argued, and it would silently
    cover the next reference that happened to be written the same way.
    """
    used = {
        reference
        for path in _workflows()
        for reference, _ in _steps(path.read_text(encoding="utf-8"))
    }
    stale = sorted(set(_MAY_MOVE) - used)
    assert not stale, (
        f"_MAY_MOVE names references no workflow uses any more: {stale}. Delete the "
        "entries -- an exemption kept past its subject exempts whatever comes next."
    )


def test_something_proposes_the_bump_the_pin_freezes() -> None:
    """The other half of pinning, and the half that is easy to forget.

    A commit never goes red on its own. Without a proposer, "pinned" quietly becomes
    "has not taken a security fix since the day it was written" -- a worse position
    than the moving tag it replaced, and an invisible one. The same argument
    `tests/tooling/test_container_pins.py` makes for the base images' digests.
    """
    dependabot = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: github-actions" in dependabot, (
        "the actions are pinned to commits and nothing proposes updating them"
    )


def test_the_detector_convicts_a_moving_tag() -> None:
    """A detector arrives with proof that it fires.

    Over the real workflow text, so the fabrication is one line and everything else
    the sweep reads is the tree it actually guards.
    """
    fabricated = _steps(
        (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        + "\n      - uses: some-org/some-action@v1\n"
    )
    assert ("some-org/some-action@v1", "      - uses: some-org/some-action@v1") in fabricated
    assert not _PINNED.search("some-org/some-action@v1")


def test_the_detector_convicts_a_pin_with_no_tag_to_read() -> None:
    """The known positive for the second rule, which the first would let through."""
    line = "      - uses: some-org/some-action@" + "0" * 40
    assert _PINNED.search(line.split("uses: ")[1]) is not None
    assert _TAG_BESIDE.search(line) is None
