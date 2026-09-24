"""Sentences this repository has withdrawn, and may not quietly get back.

A false claim about the system is not fixed by the commit that deletes it. It is
fixed by the commit that deletes it *and* stops the next author writing it again --
because these sentences were all reasonable when somebody wrote them, and every one
of them outlived the thing it described by weeks.

The three that cost the most, and what each one actually did:

  * "removing a label cannot make a green run wrong" stood in `ci.yml` as the reason
    `unlabeled` was left off the trigger. It is true of a RESTRICTIVE label and two
    of this repository's three are permissive -- `spec-exempt` is the only road from
    `check_change.py` exit 1 to exit 0 -- so taking one away turned green into red
    and fired no event at all.
  * "If this passes, CI passes" made `check.sh` an equivalence. It is a containment:
    `spec/design/testing.md` names seven things CI answers that it cannot.
  * the free-plan paragraph explained why `CI passed` could not be required. The
    organisation was on Team throughout; the obstacle was a fork network, and it was
    detached on 2026-09-10. The paragraph was still there, still cited, in September.

**Phrases, not meanings.** This cannot tell whether a document has gone stale; it
can tell that an exact sentence somebody decided against is back. That is a narrow
promise and a cheap one, and narrowness is what keeps it from crying wolf.

**What is deliberately not scanned.** `changelog/` and `spec/changes/` are records of
what was believed on a date and are never edited afterwards (`changelog/README.md`);
`spec/rationale/` holds dated audits for the same reason. A withdrawal is an event in
this repository's history, so the history is allowed to contain it -- it is the LIVE
tree that may not.
"""

import pathlib
import subprocess
from typing import Final

import pytest

from tests._repo import REPO_ROOT

#: Trees that record what was believed on a date, and are not edited after the fact.
_HISTORICAL: Final[tuple[str, ...]] = ("changelog/", "spec/changes/", "spec/rationale/")

#: This module quotes every phrase it refuses, so it cannot scan itself.
_SELF: Final[str] = "tests/fitness/test_withdrawn_claims.py"

#: Files worth reading as prose. Everything else in the tree is a lockfile, a
#: fixture or a binary, and a phrase found in one would be a coincidence.
_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".py", ".sh", ".md", ".yml", ".yaml", ".toml", ".json", ".ts", ".tsx", ".cfg", ".txt"}
)

#: The sentence, and what it was replaced by. The second half is the assertion
#: message: a test that says only "forbidden string found" sends somebody to
#: `git log` to find out what they were supposed to write instead.
_WITHDRAWN: Final[tuple[tuple[str, str], ...]] = (
    (
        "removing a label cannot make a green run wrong",
        "two of the three labels this repository reads are permissive, so taking one away "
        "turns green into red; the third asks for a job rather than waiving one, and moving "
        "it changes the verdict just as much. `unlabeled` is on ci.yml's trigger for exactly "
        "that reason, and `.github/labels.md` is the register of all three.",
    ),
    (
        "If this passes, CI passes",
        "check.sh is a containment, not an equivalence: say that it runs every gate of this "
        "application and point at spec/design/testing.md, 'What only CI can answer'.",
    ),
    (
        "on the free plan",
        "the organisation is on Team and was throughout. The obstacle to a ruleset was a fork "
        "network, detached on 2026-09-10; ruleset `main` id 22747644 has required `CI passed` "
        "since. State a reading with a date, never a permanent impossibility.",
    ),
    (
        "a verdict nothing can require",
        "`CI passed` is a required check on this repository. See ci.yml's `on:` comment for "
        "the dated fact and the history behind it.",
    ),
    (
        "flow.yml",
        "that file belongs to the change process, and the script contract forbids this "
        "template's scripts, tests and CI from naming any file of the process. Say 'CI of its "
        "own', and for this repository's specification gates say the `specs` job.",
    ),
)


def _tracked_prose() -> list[pathlib.Path]:
    """Every tracked file worth reading, minus the historical trees and this one."""
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    names = [name for name in out.split("\0") if name]
    return [
        REPO_ROOT / name
        for name in names
        if pathlib.PurePosixPath(name).suffix in _SUFFIXES
        and name != _SELF
        and not name.startswith(_HISTORICAL)
    ]


def _naming(phrase: str) -> list[str]:
    """The tracked files carrying `phrase`, relative, for an actionable message."""
    found = []
    for path in _tracked_prose():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):  # a file that is not prose after all
            continue
        if phrase in text:
            found.append(str(path.relative_to(REPO_ROOT)))
    return sorted(found)


def test_the_scanner_reads_the_tree_it_thinks_it_is_reading() -> None:
    """Proved on a known positive first, like every scanner in this directory.

    A `git ls-files` that stops matching, a suffix set that stops covering the file
    the phrase lives in, an exclusion that grows to cover everything -- each one
    turns this module into a test that passes for ever while checking nothing.
    """
    files = _tracked_prose()
    assert len(files) > 100, (
        f"the scanner found {len(files)} files to read, which is too few for this repository "
        "-- the `git ls-files` call or the suffix set has stopped matching"
    )
    assert _naming("#!/usr/bin/env bash"), (
        "the scanner cannot find a shebang anywhere in scripts/, so it is not reading what it "
        "believes it is reading"
    )
    assert not _naming("this string appears in no file of this repository"), (
        "the scanner reports a hit for a phrase that is nowhere in the tree"
    )


@pytest.mark.parametrize(("phrase", "instead"), _WITHDRAWN, ids=lambda value: value[:40])
def test_a_withdrawn_claim_does_not_come_back(phrase: str, instead: str) -> None:
    """One parametrisation per sentence, so a failure names the sentence.

    The historical trees are excluded rather than exempted: a changelog entry
    describing the day a claim was withdrawn has to be able to quote it.
    """
    carrying = _naming(phrase)
    assert not carrying, (
        f'"{phrase}" is a claim this repository withdrew, and it is back in {carrying}. '
        f"What to write instead: {instead}"
    )
