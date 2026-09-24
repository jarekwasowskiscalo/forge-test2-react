"""Every check.sh gate runs in a named CI job, and every CI job is accounted for.

Article XII makes `./scripts/check.sh` the local half of "will CI pass" -- every
gate it runs, CI runs, and CI runs more -- and `spec/design/testing.md` promises
the two halves are declared. Until now that agreement was prose: a gate added to
`check.sh` but never wired into a workflow job -- or a job added to the workflow
that no local gate mirrors -- drifted silently, because nothing read both files in
one place.

This is that place. The map below is kept by hand and that is the design, not a
compromise: which job runs which gate is a *decision* (hygiene is split across
two jobs on purpose; the generated-contract check runs in two), and a decision
belongs in a reviewed table, not in an inference. What is checked mechanically is
the two boundaries of the table: every gate label in `check.sh` has an entry, and
every job in `ci.yml` is either a target of some entry or on the declared CI-only
list, which is itself confronted with the blind-spots section of `testing.md`.

Parsed with anchored regexes, no YAML parser -- PyYAML is not a dependency, and
`frontmatter.py` already states the argument: a third-party import in the package
that must keep working when the environment is broken, for a shape this closed,
is a bad trade. The cost of the regex is named in each assertion message: when
the workflow's shape changes, update the parser and the map here, in the same
commit.

Job ids allow digits (`e2e`) -- the first draft's `[a-z-]+` quietly dropped that
job from the census, which is exactly the silent-narrowing failure this file
exists to prevent.

This template's test, in this template's suite, importing nothing of the change
process: `check.sh`, `ci.yml` and `testing.md` are all this application's. The
process's own CI is proved by the process's own suite.
"""

import re
import subprocess
from typing import Final

import pytest

from tests._repo import REPO_ROOT

_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "ci.yml"
_CHECK: Final = REPO_ROOT / "scripts" / "check.sh"
_TESTING: Final = REPO_ROOT / "spec" / "design" / "testing.md"

#: A job id: two-space indent directly under `jobs:`, digits allowed.
_JOB: Final = re.compile(r"^  ([a-z0-9-]+):", re.MULTILINE)

#: The same anchor `test_sdd_gate_parity.py` reads `check.sh` with.
_GATE_LINE: Final = re.compile(r'^\s*gate\s+"(?P<label>[^"]+)"', re.MULTILINE)

#: The decision table: which CI job(s) run each check.sh gate. Hand-kept -- see
#: the module docstring for why -- and fenced on both sides by the tests below.
_RUN_IN: Final[dict[str, frozenset[str]]] = {
    "Repository hygiene": frozenset({"quality", "scripts"}),
    "Static checks": frozenset({"quality"}),
    "Infrastructure": frozenset({"infra"}),
    "Generated code is current": frozenset({"quality", "frontend"}),
    # The `frontend` job and not `specs`: this gate needs the dump, that job already
    # builds it, and a second build in a job that needs nothing else from the
    # application would pay for the import twice.
    "API contract is frozen": frozenset({"frontend"}),
    # A step of the `backend` job rather than a job of its own: it needs the same
    # locked environment and nothing more, and a job would pay for the setup twice.
    "Fitness tests": frozenset({"backend"}),
    "Backend tests": frozenset({"backend"}),
    "Frontend tests": frozenset({"frontend"}),
    "Frontend build": frozenset({"frontend"}),
    # Its own job since the advisory split: an advisory published against a
    # dependency nobody here touched used to turn every unrelated pull request red
    # from inside `frontend`. It now blocks only when the diff owns the manifests.
    "Dependency audit": frozenset({"audit"}),
    "Docker image": frozenset({"image"}),
    "End-to-end tests": frozenset({"e2e"}),
}

#: Jobs that mirror no local gate, on purpose. `cross-platform` is the macOS leg
#: -- a Linux machine cannot be it, says testing.md's blind-spots table. `ci` is
#: the aggregate required check: it runs no gate, it reads the verdicts of every
#: other job.
#:
#: `changes` and `ci-advisory` joined them for the same reason and not by accident.
#: `changes` reads the diff to decide what the run can skip, which is a question that
#: does not exist on a workstation -- `check.sh` runs everything because a person
#: asking "will CI pass" is asking about all of it. `ci-advisory` is the second
#: verdict, the one no branch rule requires; it aggregates signals rather than
#: producing one, so there is no local gate for it to mirror either.
#: `specs` is here for a reason of its own: it runs the change process's gates, and
#: `check.sh` deliberately runs nothing of the process. There is no local gate to
#: wire it to, and inventing one would put the process back inside this repository.
#: `changelog` is CI-only for a reason of the same kind as `changes`: it reads the pull
#: request -- the diff against the base, the author, the labels -- and none of those three
#: exists on a workstation. `./scripts/changelog.sh check --base main` is the same gate
#: locally, but it is a question about a branch rather than a gate over the tree, so
#: `check.sh` does not run it and there is nothing for `_RUN_IN` to point at.
_CI_ONLY: Final[frozenset[str]] = frozenset(
    {"cross-platform", "ci", "changes", "ci-advisory", "specs", "changelog"}
)


def _jobs(text: str) -> set[str]:
    """The job ids under `jobs:`, and only under it.

    Sliced to the `jobs:` block first: the top-level keys above it (`on:`,
    `permissions:`, `concurrency:`) have two-space-indented children that the
    bare regex would happily read as jobs.
    """
    _, sep, below = text.partition("\njobs:\n")
    assert sep, f"{_WORKFLOW} has no top-level `jobs:` key -- update this parser with it"
    for line in below.splitlines():
        if re.match(r"^[A-Za-z]", line):
            below = below[: below.index(line)]
            break
    return set(_JOB.findall(below))


def test_the_header_comment_names_every_job_that_exists() -> None:
    """The workflow's own summary of itself, checked like any other claim.

    It said seven while ten existed, and stayed wrong long enough for an audit to
    copy the number instead of counting -- which is how a stale comment becomes a
    stale report. The three it omitted were `infra`, `specs` and `ci`.

    Deliberately one-directional on wording: this asserts the header NAMES each job,
    not that it describes it well. A test that graded prose would be a test nobody
    could satisfy.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    header, sep, _ = text.partition("\non:")
    assert sep, f"{_WORKFLOW} has no top-level `on:` key -- update this parser with it"
    missing = sorted(job for job in _jobs(text) if job not in header)
    assert not missing, (
        "the header comment in ci.yml does not name these jobs, so the file's summary "
        f"of itself is out of date: {missing}"
    )


def test_every_gate_has_a_map_entry_and_the_map_no_ghost() -> None:
    labels = set(_GATE_LINE.findall(_CHECK.read_text(encoding="utf-8")))
    assert labels == set(_RUN_IN), (
        "check.sh gates and the _RUN_IN map disagree. A new gate needs a decision "
        "about which CI job runs it; a removed gate leaves a ghost row. Update "
        f"_RUN_IN in this file. Only in check.sh: {sorted(labels - set(_RUN_IN))}; "
        f"only in the map: {sorted(set(_RUN_IN) - labels)}"
    )


def test_every_ci_job_runs_a_gate_or_is_a_declared_blind_spot() -> None:
    jobs = _jobs(_WORKFLOW.read_text(encoding="utf-8"))
    mapped = frozenset().union(*_RUN_IN.values())
    assert mapped <= jobs, (
        "the map names CI jobs that do not exist -- a renamed job must be renamed "
        f"here too: {sorted(mapped - jobs)}"
    )
    assert jobs - mapped == _CI_ONLY, (
        "a CI job neither runs a check.sh gate nor is on the declared CI-only "
        "list. Either wire the gate it mirrors into _RUN_IN, or -- if it truly "
        "cannot run locally -- add it to _CI_ONLY *and* to the blind-spots "
        f"section of spec/design/testing.md. Unaccounted: "
        f"{sorted((jobs - mapped) ^ _CI_ONLY)}"
    )


def test_a_new_job_lands_unmapped_until_somebody_places_it() -> None:
    """The known positive: the detector convicts a job nobody has placed."""
    fabricated = _WORKFLOW.read_text(encoding="utf-8") + (
        "\n  something-new:\n    runs-on: ubuntu-latest\n"
    )
    jobs = _jobs(fabricated)
    unmapped = jobs - frozenset().union(*_RUN_IN.values()) - _CI_ONLY
    assert unmapped == {"something-new"}


def test_the_ci_only_jobs_are_the_declared_blind_spots() -> None:
    """`cross-platform` is in testing.md's table; `ci` aggregates every other job."""
    section = _TESTING.read_text(encoding="utf-8")
    assert "macOS" in section, (
        "testing.md no longer names the macOS leg in its blind-spots section, but "
        "the cross-platform job still runs -- the declared list and the prose have "
        "split"
    )

    workflow = _WORKFLOW.read_text(encoding="utf-8")
    needs = re.search(r"^  ci:\n(?:.*\n)*?\s+needs:\s*\[([^\]]+)\]", workflow, re.MULTILINE)
    assert needs is not None, "the ci job lost its one-line needs list -- update this parser"
    aggregated = {item.strip() for item in needs.group(1).split(",")}
    assert aggregated == _jobs(workflow) - {"ci"}, (
        "the required check aggregates a different set than the jobs that exist; "
        "a job missing from `needs` can fail without failing `ci`. "
        f"Missing: {sorted((_jobs(workflow) - {'ci'}) - aggregated)}; "
        f"stale: {sorted(aggregated - (_jobs(workflow) - {'ci'}))}"
    )


# --------------------------------------------------------------------------- #
# The routing census -- an allow-list rots in the dangerous direction
# --------------------------------------------------------------------------- #

#: A `verdict <output> '<regex>'` line in the `changes` job.
_VERDICT: Final = re.compile(r"^\s*verdict\s+(?P<name>\w+)\s+'(?P<pattern>[^']+)'", re.MULTILINE)

#: Top-level entries no routing filter names, each because the jobs those filters
#: gate genuinely cannot be affected by it -- and every one of them is still judged
#: by a job that is never routed at all (`quality`, `scripts`, `specs`, `backend`).
#:
#: This list is the point of the test. A filter set is an ALLOW-LIST, and an
#: allow-list fails in the dangerous direction: a directory nobody thought about
#: matches nothing, so every routed job skips it and the required check goes green
#: over a change nothing looked at. Adding a top-level directory therefore has to
#: be a decision recorded here rather than a silence.
_UNROUTED: Final[frozenset[str]] = frozenset(
    {
        ".claude",  # the pin on the SDD process plus this template's own skills
        ".github",  # `ci_self` covers it, and it empties `may_skip` outright
        ".specconf",  # the process's configuration and the stack profile; read by both suites
        "docs",  # non-normative prose; `specs` reads every link in it
        "retro",  # the self-audit loop; prose only
        "changelog",  # the record of changes made outside the process; prose only, and the changelog job is never routed
        "spec",  # the specification; `specs` and `backend` both read it
        "tests",  # `backend` is never routed, and it owns this tree
        "http",  # editor request files, run by a human
        # Root files. Each is judged by a job that is never routed, so no filter
        # needs to name it -- but the reason is written down rather than assumed,
        # which is the difference between an unrouted path and a forgotten one.
        ".gitattributes",  # `quality` renormalises the tree against it on every run
        ".gitignore",  # `quality` asserts nothing tracked matches it
        ".pre-commit-config.yaml",  # local hooks; no CI job runs them, by design
        ".python-version",  # the interpreter `backend` and `quality` already install
        "CLAUDE.md",  # prose; `specs` resolves every path and link in it
        "README.md",  # the same
    }
)


def _routing_patterns() -> dict[str, re.Pattern[str]]:
    verdicts = {
        match.group("name"): re.compile(match.group("pattern"))
        for match in _VERDICT.finditer(_WORKFLOW.read_text(encoding="utf-8"))
    }
    assert verdicts, (
        "no `verdict` lines found in the changes job -- either the routing was "
        "removed or this parser no longer matches it, and a census that finds "
        "nothing passes over everything"
    )
    return verdicts


def _top_level() -> set[str]:
    """What a fresh clone holds at its root, directories and files alike."""
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if tracked.returncode != 0:
        pytest.skip("no git checkout here -- there is no tree to take a census of")
    return {line.split("/", 1)[0] for line in tracked.stdout.splitlines() if line}


def test_every_top_level_path_is_routed_or_declared_unrouted() -> None:
    """A directory no filter names is a directory every routed job skips."""
    patterns = _routing_patterns()
    entries = _top_level()
    assert entries, "git ls-files returned nothing; this test would then pass over nothing"

    orphans = sorted(
        entry
        for entry in entries
        if entry not in _UNROUTED
        # A directory is probed as a path under it; a root file as itself.
        and not any(
            pattern.search(f"{entry}/probe") or pattern.search(entry)
            for pattern in patterns.values()
        )
    )
    assert not orphans, (
        f"these top-level paths match no routing filter and are not declared unrouted: "
        f"{orphans}. Every job the filters gate would skip a change to them, and the "
        "required check would go green over it. Either add the path to the filter that "
        "should see it, or add it to _UNROUTED with the reason it needs none."
    )


def test_the_unrouted_list_names_nothing_that_has_gone() -> None:
    """A stale entry here hides the next orphan behind a name nobody checks."""
    stale = sorted(_UNROUTED - _top_level())
    assert not stale, (
        f"_UNROUTED names paths this repository no longer has: {stale}. An exemption "
        "for something that does not exist is one nobody re-reads."
    )


# --------------------------------------------------------------------------- #
# The blind spots, at step level
#
# `_RUN_IN` above maps check.sh's gate LABELS to CI JOBS, which is the right
# granularity for "is every local gate run somewhere" and the wrong one for "is
# everything CI runs reproducible locally". It cannot see a STEP that exists in a
# job with no local counterpart -- which is how `CLAUDE.md` came to call `check.sh`
# "THE LOCAL DEFINITION of will CI pass" while three CI-only steps stood beside the
# one blind spot the prose admitted.
# --------------------------------------------------------------------------- #

#: CI-only steps, and the phrase in `testing.md` that owns each. The prose is the
#: declaration; this asserts the two halves still describe the same repository.
_CI_ONLY_STEPS: Final[dict[str, str]] = {
    "./scripts/package.sh --lambda": "package.sh --lambda",
    "--entrypoint id": "runtime assertions",
    "./scripts/test.sh --no-db -q": "cross-platform leg",
    # Declared late, and the omission was the point: this gate lived INSIDE a
    # reporting heredoc, so nothing named it and `testing.md`'s list of what only CI
    # can answer was quietly incomplete. Giving it a named step is what made it
    # visible enough to declare.
    "--require-report --expect-nonempty": "frontend suite census",
}


def test_the_ci_only_steps_still_exist_and_are_declared() -> None:
    """A blind spot that is fixed has to stop being listed as one, and the reverse.

    One-directional on wording, like the header test above: this asserts that each
    CI-only step is still in the workflow and that `testing.md` still names it. It
    does not grade the sentence -- a test that graded prose is one nobody satisfies.
    """
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    section = _TESTING.read_text(encoding="utf-8")

    gone = sorted(step for step in _CI_ONLY_STEPS if step not in workflow)
    assert not gone, (
        f"these steps are declared CI-only in testing.md and are no longer in the "
        f"workflow: {gone}. Either the step moved and this map is stale, or it was "
        "removed and testing.md is claiming a blind spot the repository no longer has."
    )

    undeclared = sorted(phrase for phrase in _CI_ONLY_STEPS.values() if phrase not in section)
    assert not undeclared, (
        f"testing.md's 'What only CI can answer' no longer names {undeclared}. The "
        "list is what makes the gap between check.sh and CI a decision rather than a "
        "surprise, and CLAUDE.md points a reader at it."
    )


# --------------------------------------------------------------------------- #
# The trigger
#
# The required status is a function of (SHA, pull-request metadata). These assert
# that every metadata move which can TAKE A GREEN AWAY still fires an event, which
# is the half a workflow forgets: applying a label was wired years before removing
# one was, because applying it was the half somebody needed.
# --------------------------------------------------------------------------- #

#: The `pull_request` types, as a flow sequence on one line.
_PR_TYPES: Final = re.compile(r"^  pull_request:\n    types: \[([^\]]+)\]", re.MULTILINE)

#: Every type that must fire, and the permissive metadata each one moves. A label
#: this repository reads can only ADD permission -- `spec-exempt` is the one road
#: from `check_change.py` exit 1 to exit 0, `no-changelog` a path to `ok` in
#: `changelog.sh` -- so removing one turns green into red, and a green that was
#: never recomputed is a green somebody merges on.
_REQUIRED_PR_TYPES: Final[dict[str, str]] = {
    "opened": "the pull request exists",
    "synchronize": "a new commit",
    "reopened": "the pull request exists again",
    "labeled": "a permissive label applied: red may become green",
    "unlabeled": "a permissive label taken away: green may become red",
    "ready_for_review": "the draft flag cleared, which un-skips two asserts in check_change.py",
    "converted_to_draft": "the draft flag set, which skips them again",
}


def _pull_request_types() -> list[str]:
    text = _WORKFLOW.read_text(encoding="utf-8")
    match = _PR_TYPES.search(text)
    assert match, (
        f"{_WORKFLOW} has no single-line `pull_request:` / `types: [...]` pair -- the shape "
        "changed, so update this parser in the same commit"
    )
    return [part.strip() for part in match.group(1).split(",")]


def test_every_metadata_move_that_can_take_a_green_away_fires_an_event() -> None:
    """Naming `types:` REPLACES the default set, so an omission is silent.

    `unlabeled` and `ready_for_review` were both missing, and the file said the
    first was deliberate, on the grounds that taking a label away could not
    invalidate a green run. That reasoning holds for RESTRICTIVE labels and both of
    this repository's are permissive, so it was exactly backwards. `check_change.py` meanwhile claimed
    its two draft-skipped asserts "start deciding the moment you take it out of
    draft" -- a sentence that could not be true while `ready_for_review` fired
    nothing at all.
    """
    declared = _pull_request_types()
    missing = sorted(name for name in _REQUIRED_PR_TYPES if name not in declared)
    assert not missing, (
        f"ci.yml's `pull_request` types omit {missing}. Each one moves metadata a required "
        f"check reads: {', '.join(f'{n} ({_REQUIRED_PR_TYPES[n]})' for n in missing)}."
    )


def test_converted_to_draft_never_travels_without_ready_for_review() -> None:
    """The pair, and why one half alone is worse than neither.

    `check_change.py` skips its `stage` and `status` asserts while a pull request
    is a draft. So `converted_to_draft` on its own is a laundering path: a red
    `specs` recomputes to green the moment somebody converts, and the aggregate
    that green belongs to is the one the branch ruleset requires. Paired with
    `ready_for_review` it is closed -- GitHub refuses to merge a draft, and leaving
    the draft recomputes strictly.
    """
    declared = _pull_request_types()
    if "converted_to_draft" in declared:
        assert "ready_for_review" in declared, (
            "ci.yml fires on `converted_to_draft` without `ready_for_review`, which is the one "
            "combination that is worse than neither: converting to draft turns a red `specs` "
            "green, and nothing recomputes it when the pull request leaves the draft again."
        )


def test_no_job_routes_itself_off_a_metadata_run() -> None:
    """The saving that would have cost the gate.

    A metadata run's aggregate REPLACES the previous one for this SHA. Skipping the
    heavy jobs on such a run -- which the reporter would have to be taught to clear,
    or it goes red -- means a pull request with a red `backend` needs only a label
    added or removed to publish a green `CI passed` assembled from `specs` and
    `changelog` alone. The whole workflow runs in two to three minutes; that is the
    price of not having to reason about which green a merge button is reading.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    routed = sorted(set(re.findall(r"github\.event\.action", text)))
    assert not routed, (
        "a job in ci.yml now branches on `github.event.action`. A metadata run is a FULL run "
        "by decision -- see the `pull_request:` comment in ci.yml. If this is being changed "
        "deliberately, the aggregate must be unable to publish a green built from a subset of "
        "the jobs, and this test and that comment move in the same commit."
    )


# --------------------------------------------------------------------------- #
# The blind-spot list is closed
#
# `_CI_ONLY_STEPS` above pins four STEPS. The section in `testing.md` is the
# declaration a reader is pointed at, and `CLAUDE.md` quotes its LENGTH -- which
# is how it came to say "all five" while the section listed seven. A count in
# prose is a fact like any other.
# --------------------------------------------------------------------------- #

_CLAUDE_MD: Final = REPO_ROOT / "CLAUDE.md"

#: Every bullet of `testing.md` § What only CI can answer, and the `ci.yml` job
#: that answers it. Hand-kept, like `_RUN_IN`, and fenced the same way: the count
#: must match the section, and every job named must exist.
_CI_ONLY_ANSWERS: Final[dict[str, str]] = {
    "The cross-platform leg.": "cross-platform",
    "The specification gates.": "specs",
    "`./scripts/package.sh --lambda`.": "backend",
    "The image's runtime assertions.": "image",
    "The routing verdict.": "changes",
    "The record of a change made outside the process.": "changelog",
    "The frontend suite census.": "frontend",
}

#: The counts this repository can write out in prose. Deliberately short: a map
#: that ran to twenty would mean the blind-spot list had stopped being readable.
_NUMBER_WORD: Final[dict[int, str]] = {5: "five", 6: "six", 7: "seven", 8: "eight"}


def _ci_only_section() -> str:
    text = _TESTING.read_text(encoding="utf-8")
    _, sep, below = text.partition("## What only CI can answer\n")
    assert sep, f"{_TESTING} no longer has a `## What only CI can answer` heading"
    end = below.find("\n## ")
    return below if end == -1 else below[:end]


def test_the_blind_spot_list_names_a_job_that_exists_for_every_entry() -> None:
    """A declared gap is only a decision while both halves are true.

    The section is what `check.sh` and `CLAUDE.md` send a reader to, so an entry
    naming a job that no longer exists reads as a gap the repository still has.
    """
    section = _ci_only_section()
    jobs = _jobs(_WORKFLOW.read_text(encoding="utf-8"))

    missing = sorted(title for title in _CI_ONLY_ANSWERS if title not in section)
    assert not missing, (
        f"testing.md's 'What only CI can answer' no longer names {missing}. Either the gap "
        "closed and this map is stale, or the section was edited and the map was not."
    )

    unknown = sorted({job for job in _CI_ONLY_ANSWERS.values() if job not in jobs})
    assert not unknown, (
        f"these jobs answer a declared CI-only entry and are not in ci.yml: {unknown}. A "
        "blind spot attributed to a job that does not exist is a blind spot nobody owns."
    )

    bullets = len(re.findall(r"^- \*\*", section, re.MULTILINE))
    assert bullets == len(_CI_ONLY_ANSWERS), (
        f"the section lists {bullets} entries and this map holds {len(_CI_ONLY_ANSWERS)}. The "
        "map is the reviewed half: add the entry here in the same commit that adds the bullet."
    )


def test_the_prose_that_quotes_the_list_quotes_its_length_correctly() -> None:
    """`CLAUDE.md` said "names all five" while the section listed seven.

    That is the whole failure mode of a summary: it is written once, against a list
    that then grows, and a reader trusts the number instead of counting. The number
    is derived here so it cannot be written down wrong twice.
    """
    word = _NUMBER_WORD.get(len(_CI_ONLY_ANSWERS))
    assert word, (
        f"{len(_CI_ONLY_ANSWERS)} CI-only entries and no word for it -- extend _NUMBER_WORD, or "
        "ask whether a list this long is still a list a reader uses."
    )
    claude = _CLAUDE_MD.read_text(encoding="utf-8")
    assert f"names all\n{word}" in claude or f"names all {word}" in claude, (
        f"CLAUDE.md does not say the section names all {word} entries. It is the one place a "
        "reader is told how long the list is, and a stale count there is how the gap stops "
        "being a decision and becomes a surprise."
    )
