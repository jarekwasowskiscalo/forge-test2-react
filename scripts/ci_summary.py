"""Every CI job's result, written as a page a person can read.

## Why one module rather than a heredoc per job

Six of the thirteen jobs in `ci.yml` used to write a summary, each as an inline
Python or bash heredoc added at a different time. They disagreed about heading level
(`#`, `##`, `###`), about the dash (`--` against a real em dash) and about whether a
clean run states what it looked at. Five jobs wrote nothing at all, and `ci` -- the
one check the branch ruleset requires -- printed a raw `json.dumps` of its `needs`
into the log and left the page empty.

None of that is a bug in any one heredoc. It is what happens when a format is a
convention rather than a thing: there is nowhere to put the rule, and nothing to
test it against. So the rule lives in this docstring and the renderers live below
it, and `tests/tooling/test_ci_summary.py` asserts the rule over every block this
module can produce.

## The rule

**One writer per job.** Exactly one step appends to `$GITHUB_STEP_SUMMARY`, it is the
job's last step, and it carries `if: always()` -- because the run whose page matters
most is the one that just failed.

**The heading is `## ` followed by the job's `name:`, verbatim.** Never `#`, which is
the page's own level; never `###`, because nothing is nested under anything. The
order blocks land in is job-completion order and GitHub exposes no way to influence
it, so a block has to be findable by what it is called rather than by where it sits.
For the same reason no block ever refers to another by position.

**The second line is one sentence: the verdict in bold, then the scale in numbers.**
`**Passed.** 487 tests on a real Postgres -- 402 product, 85 framework, 0
unclassified.` A verdict on its own is a claim; a verdict with a scale beside it is
evidence, and a scale that falls to zero is a detector that stopped matching.

**A table only when more than one judged thing could disagree.** Five checks that
each pass or fail: a table. Five Terraform roots that pass or fail together: a
sentence naming them, because a per-root column would be reporting a distinction the
job cannot actually make.

**The last line says what a failure would mean, or what to do next** -- on a green
run too, and never "see the log".

**Typography.** The block is rendered Markdown: em dashes, `·` between counts,
backticks around every path, flag, job id and identifier. The ASCII `--` belongs in
YAML and shell comments and never reaches a page. `spec_summary.py` writes the other
half of the same page and is held to this by its own test; the one exception is a
gate finding's `remedy`, which comes from a module whose first surface is a terminal
and whose text can legitimately contain ` -- ` as a shell flag separator.

## Article XI

A block carries identifiers, counts, paths, and prose written in this file. Never a
test failure message, an assertion body, a log line or a golden-set value -- any of
which can name a real person. So the junit reader below takes **attributes and the
presence of child elements only**: never `.text`, never `message=`, never
`<system-out>`. `spec/design/testing.md` puts it plainly -- a junit may not be
committed and its contents may not be printed into a job summary.

The rule is asserted twice by the test module, once behaviourally (a report built to
carry a name, an address and an IBAN, and none of them reaching any block) and once
against this source, which must name no route to the text at all.

## Reporting never fails a build

Every reporting subcommand returns 0 on every path, including on a truncated or
absent report. A reporter that can turn a green run red is a reporter people delete,
and the heredocs this replaces would crash the step on a half-written junit.

Three genuine gates used to live inside those reporters, and they are good ones: a
missing frontend junit, a suite that collected zero tests, and an e2e report holding
no scenarios. A suite that ran and found nothing reads on a dashboard exactly like
one that passed. They are not lost -- they are the `census` subcommand, which writes
nothing and is the only branch here that can exit non-zero. It runs as its own named
step, so the red X in the step list says what failed rather than saying "summarise".

## Standard library only

`python3 scripts/ci_summary.py`, never `uv run`. The `scripts` job installs no
toolchain at all -- answering `--help` before any prerequisite is the property it
exists to prove -- `image`, `ci` and `ci-advisory` install nothing, and
`preview-teardown.yml` deliberately has neither uv nor Node so that a teardown still
works while the toolchain is broken. A test walks the imports rather than trusting
this paragraph.

Usage:
    python3 scripts/ci_summary.py suite --shape pytest --job "Backend tests" \\
        --junit .sdd/reports/backend.junit.xml --markdown "$GITHUB_STEP_SUMMARY"
    python3 scripts/ci_summary.py census --junit .sdd/reports/frontend.junit.xml \\
        --require-report --expect-nonempty --what tests

Exit code:
    0  always, except `census`, which is a gate and says so.
"""

import argparse
import json
import pathlib
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

#: How a backend test's `classname` maps to what the test is *about*. A decision
#: about this repository's layout, so it lives here rather than in workflow YAML
#: where no test would read it. `unclassified` is the safety net and is reported
#: even at zero: a classname matching neither prefix means the layout moved, and a
#: bucket quietly absorbing it would hide exactly that.
_BUCKETS: Final[tuple[tuple[str, str], ...]] = (("tests.", "product (`tests/`)"),)
_UNCLASSIFIED: Final = "unclassified"

#: The Terraform roots `infra-check.sh` walks. Mirrored from its `ROOTS=(...)` line
#: and compared against it by the test module.
_TERRAFORM_ROOTS: Final[tuple[str, ...]] = (
    "bootstrap",
    "preview/shared",
    "preview/branch",
    "envs/stage",
    "envs/prod",
)

#: What each job answers, for the aggregate block in `ci`. Keyed by job id and
#: compared against that job's `needs:` list by the test module, so a job added to
#: the workflow and forgotten here fails the build rather than appearing in the
#: table with no explanation beside it.
_JOB_PURPOSE: Final[dict[str, str]] = {
    "changes": "which heavy jobs this diff can possibly affect",
    "quality": "lint, format, strict types, and nothing generated tracked in git",
    "scripts": "the project's own interface: listed, answering `--help`, shellcheck, actionlint",
    "infra": "every Terraform root is canonical and still parses",
    "backend": "the regressions the suite pins, on a real Postgres",
    "audit": "advisories published against the dependency tree",
    "frontend": "the API contract in both directions, the unit suite and the build",
    "cross-platform": "that the suite runs on macOS as well as on Linux",
    "image": "the deployable artefact builds, runs unprivileged and serves",
    "e2e": "the black box: scenarios and the UI smoke against a live application",
    # Not this repository's job: it calls the change process's reusable workflow,
    # which runs the specification gates over this diff and writes its own summary.
    # The purpose is stated here anyway, because `ci` waits on it and a reader of the
    # required check should not have to open another repository to learn what it is.
    "specs": "the specification gates, run by the process that owns them",
    "ci-advisory": "the signals that report and never block",
    "changelog": "that a change made outside the process left a record of what it did",
}

#: What each check step in a check-list job looked at, keyed by job id and step id.
#: GitHub's `steps` context carries the outcome but not the `name:`, and "what this
#: check was for" is a decision rather than a fact about the run -- so the outcome
#: comes from the context and the prose comes from here, which is a reviewed table.
#: The step ids are compared against `ci.yml` by the test module.
_CHECKS: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    "quality": (
        ("ruff", "`ruff check`", "every Python file in the tree"),
        ("format", "`ruff format --check`", "every Python file in the tree"),
        (
            "types",
            "`mypy`, strict",
            "`app`, `scripts`, `e2e` and part of `tests`",
        ),
        (
            "tracked",
            "no generated artefact is tracked",
            "the whole index against `.gitignore`, plus four paths by name",
        ),
        ("eol", "line endings match `.gitattributes`", "every tracked file, renormalised"),
    ),
    "scripts": (
        ("flags", "`start.sh` still accepts every mode flag", "5 flags, matched whole-word"),
        ("execbit", "shell scripts are executable", "every script, at the mode **git** records"),
        ("listed", "every script is listed in help", "every public script against `help.sh`"),
        (
            "help",
            "every script answers `--help` with no toolchain",
            "every public script, exit status only",
        ),
        ("images", "the pinned linter images pull", "2 images, up to 3 attempts each"),
        ("shellcheck", "`shellcheck`", "every script, pinned v0.9.0, following `source`"),
        ("actionlint", "`actionlint`", "every workflow, pinned 1.7.7"),
    ),
    "image": (
        ("build", "build", "the `Dockerfile` against the whole context, with the GHA cache"),
        ("contents", "runs unprivileged, and the SPA is inside", "`id -un` and `index.html`"),
        ("health", "serves `/api/health`", "30 one-second attempts, with no database"),
    ),
    "cross-platform": (
        ("nodb", "the no-database subset, through the script", "`./scripts/test.sh --no-db`"),
        ("fitness", "the fitness suite, through the script", "`./scripts/test.sh fitness`"),
        ("postgres", "a Postgres this runner can actually run", "Homebrew `postgresql@16`"),
        ("integration", "integration tests on a real Postgres", "one migrated database per test"),
        ("bash", "shell scripts parse under the system bash", "every script, `bash -n`, bash 3.2"),
        ("migrate", "the database scripts work against a supplied Postgres", "`./scripts/db.sh`"),
    ),
    "infra": (("check", "format and validate every root", "`./scripts/infra-check.sh`"),),
    "changelog": (
        (
            "entry",
            "a change made outside the process left a record of what it did",
            "the diff against the pull request's base, or a named exemption",
        ),
    ),
    # `frontend` proves four things beside its suite, so its table rides inside the
    # suite block rather than arriving from a second writer.
    "frontend": (
        (
            "types",
            "the committed API types are current",
            "`frontend/src/api/schema.d.ts` against a fresh dump",
        ),
        (
            "contract",
            "the application honours the hand-written contract",
            "`contracts/openapi/` against the dump",
        ),
        ("eslint", "lint, at zero warnings", "every file under `frontend/src/`"),
        ("vitest", "unit tests", "the vitest projects"),
        ("build", "type-check and build", "`tsc --noEmit`, then the production bundle"),
    ),
}


# --------------------------------------------------------------------------- #
# The shape of a block
# --------------------------------------------------------------------------- #


def block(job: str, verdict: str, lead: str, *parts: str) -> str:
    """One job's block: heading, a verdict-and-scale sentence, then whatever else.

    `parts` are paragraphs, already formatted. The closing sentence is just the last
    of them -- the rule says every block has one, and the test module checks that the
    last non-blank line is prose rather than a table row.
    """
    body = "\n\n".join(part.strip("\n") for part in (f"**{verdict}** {lead}", *parts) if part)
    return f"## {job}\n\n{body}\n"


def table(headers: tuple[str, ...], rows: Sequence[tuple[str, ...]], align: str = "") -> str:
    """A Markdown table, or the empty string when there is nothing to put in it."""
    if not rows:
        return ""
    marks = [
        f"{'--:' if align[index : index + 1] == 'r' else '---'}" for index in range(len(headers))
    ]
    lines = [f"| {' | '.join(headers)} |", f"|{'|'.join(marks)}|"]
    lines += [f"| {' | '.join(cells)} |" for cells in rows]
    return "\n".join(lines)


def details(title: str, body: str) -> str:
    """A fold, for the part of a block a reader only wants sometimes."""
    if not body.strip():
        return ""
    return f"<details><summary>{title}</summary>\n\n{body}\n\n</details>"


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{int(seconds // 60)}m {int(seconds % 60):02d}s"


# --------------------------------------------------------------------------- #
# Reading a JUnit report -- attributes and child elements, never text
# --------------------------------------------------------------------------- #


class Case(NamedTuple):
    """One test case, reduced to what may appear on a public page."""

    classname: str
    name: str
    time: float
    #: `pass`, `fail` or `skip`, decided by the PRESENCE of a child element.
    #:
    #: Never by a `status` attribute. A previous runner emitted one and pytest's
    #: `xunit2` family does not, so a parser still reading it reported 0/21 on a
    #: green run, under a green check, which nobody investigates.
    outcome: str


class SuiteFile(NamedTuple):
    """One `<testsuite>`, which for vitest is one file."""

    name: str
    tests: int
    failures: int
    time: float


class Report(NamedTuple):
    cases: list[Case]
    files: list[SuiteFile]

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def failed(self) -> int:
        return sum(1 for case in self.cases if case.outcome == "fail")

    @property
    def skipped(self) -> int:
        return sum(1 for case in self.cases if case.outcome == "skip")

    @property
    def passed(self) -> int:
        return self.total - self.failed - self.skipped

    @property
    def seconds(self) -> float:
        return sum(suite.time for suite in self.files) or sum(case.time for case in self.cases)


def read_junit(path: pathlib.Path) -> Report | None:
    """The report, or `None` when there is nothing readable at that path.

    `None` covers absent, unparseable and truncated alike, and the callers treat all
    three the same way: say so on the page, return 0, and let the step that actually
    failed carry the red. Distinguishing them would be reporting on the reporter.
    """
    if not path.is_file():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None

    cases: list[Case] = []
    for element in root.iter("testcase"):
        if element.find("failure") is not None or element.find("error") is not None:
            outcome = "fail"
        elif element.find("skipped") is not None:
            outcome = "skip"
        else:
            outcome = "pass"
        cases.append(
            Case(
                element.get("classname", ""),
                element.get("name", ""),
                _float(element.get("time")),
                outcome,
            )
        )

    files = [
        SuiteFile(
            element.get("name", "?"),
            _int(element.get("tests")),
            _int(element.get("failures")) + _int(element.get("errors")),
            _float(element.get("time")),
        )
        for element in root.iter("testsuite")
    ]
    return Report(cases, files)


def _int(value: str | None) -> int:
    try:
        return int(value or 0)
    except ValueError:
        return 0


def _float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


# --------------------------------------------------------------------------- #
# Coverage -- a section of a job, never a job of its own
# --------------------------------------------------------------------------- #


def cobertura_section(path: pathlib.Path, subject: str) -> str:
    """Backend coverage: the headline, then the twelve thinnest modules in a fold."""
    if not path.is_file():
        return ""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return ""
    covered, valid = _int(root.get("lines-covered")), _int(root.get("lines-valid"))
    if not valid:
        return ""
    rate = _float(root.get("line-rate")) * 100

    rows: list[tuple[float, str, int, int]] = []
    for cls in root.iter("class"):
        lines = cls.find("lines")
        if lines is None:
            continue
        total = len(lines)
        hit = sum(1 for line in lines if _int(line.get("hits")) > 0)
        if total:
            rows.append((hit / total, cls.get("filename", "?"), total, hit))
    rows.sort()

    headline = f"Coverage: **{rate:.0f}%** of `{subject}` — {covered} of {valid} lines."
    fold = details(
        "The twelve least-covered modules",
        table(
            ("Module", "Lines", "Covered"),
            [(f"`{name}`", str(total), str(hit)) for _, name, total, hit in rows[:12]],
            align="lrr",
        )
        + f"\n\nLowest twelve of {len(rows)}. Measured, never gated: there is no threshold, and "
        "a number that falls is a suite that stopped reaching somewhere.",
    )
    return f"{headline}\n\n{fold}" if fold else headline


def vitest_coverage_section(path: pathlib.Path, subject: str) -> str:
    """Frontend coverage, from vitest's own summary rather than from a second parser."""
    if not path.is_file():
        return ""
    try:
        lines = json.loads(path.read_text(encoding="utf-8"))["total"]["lines"]
    except (ValueError, KeyError, OSError):
        return ""
    return (
        f"Coverage: **{lines['pct']}%** of lines under `{subject}` — "
        f"{lines['covered']} of {lines['total']}. Measured, never gated."
    )


# --------------------------------------------------------------------------- #
# suite -- the three report shapes
# --------------------------------------------------------------------------- #

_NO_REPORT: Final = (
    "**No report.** The suite did not get as far as writing one, so there is no scale to "
    "state. Something before it refused, and the step that went red above is the one to read."
)


def render_suite(
    job: str,
    shape: str,
    report: Report | None,
    coverage: str,
    extra: str,
    result: str = "success",
) -> str:
    if report is None:
        return f"## {job}\n\n{_NO_REPORT}\n"
    tail = _elsewhere(report, result)
    if shape == "pytest":
        return _pytest_block(job, report, coverage, extra, result, tail)
    if shape == "vitest":
        return _vitest_block(job, report, coverage, extra, result, tail)
    return _bdd_block(job, report, extra, result, tail)


def _verdict(report: Report, result: str) -> str:
    """The job's verdict, not the suite's -- these jobs do more than run tests.

    `backend` also resolves the Lambda package, `frontend` also checks two contracts
    and builds the bundle, `e2e` also builds the SPA. Reading the verdict off the
    report alone printed **Passed.** on a job that went red after its suite finished,
    which is a page contradicting the check it belongs to.
    """
    if report.failed or result not in ("success", ""):
        return "Failed."
    return "Passed."


def _elsewhere(report: Report, result: str) -> str:
    """The sentence for a job that failed somewhere other than its suite."""
    if report.failed or result in ("success", ""):
        return ""
    return (
        f"**Every test passed and the job still reports `{result}`,** so what refused is one of "
        "the steps beside the suite. The step list above is where it is; this block covers the "
        "suite only."
    )


def _pytest_block(
    job: str, report: Report, coverage: str, extra: str, result: str, tail: str
) -> str:
    counts: dict[str, list[int]] = {label: [0, 0, 0] for _, label in _BUCKETS}
    counts[_UNCLASSIFIED] = [0, 0, 0]
    for case in report.cases:
        label = next(
            (label for prefix, label in _BUCKETS if case.classname.startswith(prefix)),
            _UNCLASSIFIED,
        )
        counts[label][0] += 1
        counts[label][1] += int(case.outcome == "fail")
        counts[label][2] += int(case.outcome == "skip")

    scale = " · ".join(f"{count[0]} {label}" for label, count in counts.items())
    lead = (
        f"{_plural(report.total, 'test')} on a real Postgres in {_duration(report.seconds)} — "
        f"{scale}. {report.failed} failed, {report.skipped} skipped."
    )
    rows = [(label, str(count[0]), str(count[1]), str(count[2])) for label, count in counts.items()]
    rows.append(
        (
            "**total**",
            f"**{report.total}**",
            f"**{report.failed}**",
            f"**{report.skipped}**",
        )
    )
    note = (
        "A non-zero `unclassified` is the finding, not the count: a classname matching neither "
        "prefix means the layout moved, and a bucket that quietly absorbed it would hide "
        "exactly that."
    )
    closing = (
        "The junit stays on this runner. An assertion message can quote a record's field value, "
        "so this page carries counts and never a failing test's name or message (Article XI). "
        "Reproduce with `./scripts/test.sh backend`."
    )
    return block(
        job,
        _verdict(report, result),
        lead,
        table(("Bucket", "Tests", "Failed", "Skipped"), rows, align="lrrr"),
        note,
        coverage,
        extra,
        tail,
        closing,
    )


def _vitest_block(
    job: str, report: Report, coverage: str, extra: str, result: str, tail: str
) -> str:
    lead = (
        f"{_plural(report.total, 'test')} across {_plural(len(report.files), 'file')} in "
        f"{_duration(report.seconds)}. {report.failed} failed, {report.skipped} skipped."
    )
    fold = details(
        "Per file",
        table(
            ("File", "Tests", "Failed", "Time"),
            [
                (f"`{suite.name}`", str(suite.tests), str(suite.failures), f"{suite.time:.2f}s")
                for suite in report.files[:25]
            ],
            align="lrrr",
        )
        + (
            f"\n\nThe first 25 of {len(report.files)}."
            if len(report.files) > 25
            else f"\n\n{_plural(len(report.files), 'file')} of {len(report.files)}."
        ),
    )
    closing = (
        "A suite that ran and found nothing reads on a dashboard exactly like one that passed, "
        "so an empty report is refused by the `collected` step rather than reported here. "
        "Reproduce with `./scripts/test.sh frontend`."
    )
    return block(job, _verdict(report, result), lead, extra, fold, coverage, tail, closing)


def _bdd_block(job: str, report: Report, extra: str, result: str, tail: str) -> str:
    lead = (
        f"{report.passed} of {report.total} in {_duration(report.seconds)} — Gherkin scenarios "
        "and the Playwright UI smoke, against a real application on a real Postgres, driven by "
        "`./scripts/test.sh e2e`, the same command a developer runs."
    )
    marks = {"pass": "PASS", "fail": "**FAIL**", "skip": "SKIP"}
    rows = [
        # pytest-bdd mangles the scenario title into a Python identifier; this is as
        # close to the sentence in the .feature file as the report can get back to.
        (
            case.name.removeprefix("test_").replace("_", " "),
            marks[case.outcome],
            f"{case.time:.2f}s",
        )
        for case in report.cases[:40]
    ]
    more = f"\n\nThe first 40 of {report.total}." if report.total > 40 else ""
    note = (
        "Each row's outcome is the presence of a child element in the report, never a `status` "
        "attribute: the previous runner emitted one, and a parser still reading it reported "
        "0 of 21 on a green run, under a green check, which nobody investigates."
    )
    closing = (
        "Failure screenshots land in `.sdd/ui-artifacts/` on this runner and are deliberately "
        "not uploaded: a pixel-perfect picture of a populated screen is personal data. "
        "Reproduce with `./scripts/test.sh ui` and read them on your own machine."
    )
    return block(
        job,
        _verdict(report, result),
        lead,
        table(("Scenario", "Status", "Time"), rows) + more,
        note,
        extra,
        tail,
        closing,
    )


# --------------------------------------------------------------------------- #
# checks -- a job whose result is a set of independent assertions
# --------------------------------------------------------------------------- #

#: The sentence under each check-list table. What a failure there would mean, in
#: the words of the thing that would have failed.
_CHECKS_CLOSING: Final[dict[str, str]] = {
    "quality": (
        "`./scripts/lint.sh` and `./scripts/hygiene.sh` run the same checks on a workstation. "
        "This page names which check refused and never what it printed: the reporter reads step "
        "outcomes, never step logs."
    ),
    "scripts": (
        "The scripts are the interface to this project, for people and for agents, so a script "
        "that is missing, undocumented or broken on one OS is the same class of defect as a "
        "broken endpoint. This job installs no toolchain on purpose — `--help` has to be "
        "answerable *before* any prerequisite check, and `start.sh --help` once ran `uv sync` "
        'first and died with "uv: command not found", on exactly the machine most likely to be '
        "asking what the script does."
    ),
    "image": (
        "Building is not proof it runs, which is why the last three checks exist — and "
        '`/api/health` deliberately touches no service or persistence layer, so "the process '
        'answers" and "the database is reachable" stay separate questions. If this job ever '
        "needs a database to pass, that property has been lost. It exists because the image "
        "could not build for five days and nothing noticed, because nothing built it."
    ),
    "cross-platform": (
        "Everything here runs **through the scripts**, not through pytest: this leg used to call "
        "`uv run pytest` directly, so the escape hatch's own interface had never been executed "
        "on the one machine it exists for. It runs on the trunk, weekly, on request, and on a "
        "pull request carrying the `cross-platform` label — not on every pull request, because a "
        "macOS runner bills at 10x. The stated cost: a bash-3.2 regression surfaces after the "
        "merge, and somebody has to watch trunk runs."
    ),
    "infra": (
        "No credentials and no state: `validate` runs with no backend, so this answers a "
        "question about a commit rather than about an account, and it runs on a pull request "
        "from a fork exactly as it runs on the trunk. Deliberately not `terraform plan`, which "
        "reads live state and would need deploy credentials on every pull request. Fix "
        "formatting with `./scripts/infra.sh stage fmt`."
    ),
}


def render_checks(job: str, job_id: str, steps: Mapping[str, object], result: str) -> str:
    """A table of independent checks, with each verdict taken from GitHub's own record.

    A step that never started is *absent* from the `steps` context rather than
    reported as skipped, so it renders as `not reached` instead of crashing the
    reporter or -- worse -- being silently dropped from the table.
    """
    declared = _CHECKS.get(job_id, ())
    rows = _check_rows(job_id, steps)
    passed = 0
    for step_id, _what, _looked in declared:
        entry = steps.get(step_id)
        if isinstance(entry, dict) and entry.get("outcome") == "success":
            passed += 1

    if job_id == "infra":
        # One check over five roots that pass or fail together: a per-root column
        # would report a distinction this job cannot actually make.
        roots = ", ".join(f"`{root}`" for root in _TERRAFORM_ROOTS)
        count = len(_TERRAFORM_ROOTS)
        lead = (
            f"Every `.tf` file is in canonical form, and all {count} roots parse and "
            f"type-check — {roots}."
            if result == "success"
            else f"One of {count} Terraform roots is not canonical or no longer parses — "
            f"{roots}. `terraform validate` names the file and the line."
        )
        return block(job, _checks_verdict(result), lead, _CHECKS_CLOSING["infra"])

    if result == "skipped":
        return block(job, "Not run.", _not_run(job_id), _CHECKS_CLOSING.get(job_id, ""))

    context = _CHECKS_LEAD.get(job_id, "")
    if result == "success":
        lead = f"{_plural(len(declared), 'check')}" + (f", {context}." if context else ".")
    else:
        # Counted from the context, not from the table: the table always carries
        # every declared check, so its row count says nothing about how far the job
        # got. A step that never started is absent from `steps` entirely.
        reached = sum(1 for step_id, _what, _looked in declared if step_id in steps)
        lead = (
            f"{passed} of {_plural(len(declared), 'check')} passed"
            + (f", {len(declared) - reached} never reached" if reached < len(declared) else "")
            + (f". {context[0].upper() + context[1:]}." if context else ".")
        )
    return block(
        job,
        _checks_verdict(result),
        lead,
        rows,
        _CHECKS_CLOSING.get(job_id, ""),
    )


def _check_rows(job_id: str, steps: Mapping[str, object]) -> str:
    """The check table for one job, from GitHub's own record of each step.

    A step that never started is *absent* from the `steps` context rather than
    reported as skipped, so it renders as `not reached` instead of crashing the
    reporter or -- worse -- being silently dropped from the table.
    """
    rows: list[tuple[str, ...]] = []
    for step_id, what, looked_at in _CHECKS.get(job_id, ()):
        entry = steps.get(step_id)
        outcome = str(entry.get("outcome", "")) if isinstance(entry, dict) else ""
        rows.append(
            (
                what,
                looked_at,
                {
                    "success": "pass",
                    "failure": "**fail**",
                    "cancelled": "cancelled",
                    "skipped": "skipped",
                }.get(outcome, "not reached"),
            )
        )
    return table(("Check", "What it looked at", "Verdict"), rows)


def _checks_verdict(result: str) -> str:
    return {"success": "Passed.", "skipped": "Not run.", "cancelled": "Cancelled."}.get(
        result, "Failed."
    )


#: What distinguishes each check-list job, for the line beside its count. The count
#: alone restates the verdict ("5 checks, and 5 have passed"); what a reader does not
#: already know is what this job is and why it is worth its runner.
_CHECKS_LEAD: Final[dict[str, str]] = {
    "quality": "no Node, no Docker and no database, which is why this is the first thing to "
    "go red and the cheapest to re-run",
    "scripts": "on a runner with no uv, no Node and no Python project installed",
    "image": "the image builds, and then answers for itself",
    "cross-platform": "on macOS, against a Homebrew Postgres and the system bash 3.2",
}

_NOT_RUN: Final[dict[str, str]] = {
    "cross-platform": (
        "This pull request carries no `cross-platform` label, so the macOS leg was not asked "
        "for. A macOS runner bills at 10x, and the question this leg answers — does bash 3.2 "
        "still parse these scripts, does the suite still run off a Homebrew Postgres — is not "
        "one an ordinary pull request raises. Label the pull request `cross-platform` to ask "
        "for it; `labeled` is in this workflow's event types precisely so that the label fires "
        "a run rather than waiting for the next push. Otherwise it is answered on the trunk "
        "after the merge, weekly, and on request."
    ),
}


def _not_run(job_id: str) -> str:
    return _NOT_RUN.get(job_id, "This job was not asked for on this run.")


# --------------------------------------------------------------------------- #
# route -- what changed, and what could be skipped
# --------------------------------------------------------------------------- #

_ROUTED: Final[tuple[str, ...]] = ("backend", "frontend", "infra", "image", "e2e")


def render_route(
    job: str,
    files: list[str],
    may_skip: list[str],
    base: str,
    deps: str,
    ci_self: str,
    reason: str,
) -> str:
    if reason:
        return block(
            job,
            "Fail-safe.",
            f"{reason}, so no diff could be resolved and nothing is cleared to skip. Every job "
            "runs, exactly as it did before this job existed.",
            "A fail-safe run is this job refusing to guess rather than a fault. If it is the "
            "*usual* outcome on pull requests, the checkout's `fetch-depth` or the event's base "
            "is what to look at.",
        )

    skippable = ", ".join(f"`{name}`" for name in may_skip) if may_skip else "nothing"
    lead = (
        f"{_plural(len(files), 'file')} in the diff against `{base[:12]}`. Could be skipped once "
        f"routing is wired: {skippable} — and nothing is skipped today."
    )
    rows = [
        (
            f"`{name}`",
            "never filtered"
            if name == "backend"
            else ("no match" if name in may_skip else "matched"),
            "no" if name in may_skip else "yes",
        )
        for name in _ROUTED
    ]
    flags = f"`deps` {deps or 'false'} · `ci_self` {ci_self or 'false'}"
    fold = details(
        f"The {len(files)} changed files",
        " · ".join(f"`{path}`" for path in files[:50])
        + (f"\n\n…and {len(files) - 50} more." if len(files) > 50 else ""),
    )
    closing = (
        "Every job still runs. The verdict is published and read against what actually changed "
        "before any `if:` consumes it, because once a job can be skipped a skip is a green "
        "required check — and a job that skips without appearing above is a gate that stopped "
        "without saying so. `CI passed` is what refuses that."
    )
    return block(
        job,
        "Routed.",
        lead,
        table(("Job", "Filter", "Would run"), rows),
        flags,
        fold,
        closing,
    )


# --------------------------------------------------------------------------- #
# advisory and verdict -- the two aggregate blocks
# --------------------------------------------------------------------------- #


def render_advisory(job: str, needs: Mapping[str, Mapping[str, object]]) -> tuple[str, bool]:
    audit = needs.get("audit", {})
    outputs = audit.get("outputs")
    raised = str(outputs.get("advisory", "")) == "true" if isinstance(outputs, dict) else False
    result = str(audit.get("result", "unknown"))
    rows = [
        (
            "Dependency audit",
            "**raised**" if raised else "clear",
            f"the `Dependency audit` job (`{result}`)",
        )
    ]
    # Counted rather than spelled, so the scale moves when a second signal is added.
    # A block whose scale cannot change is one that would read the same over an empty
    # list of signals.
    lead = (
        f"{sum(1 for row in rows if '**' in row[1])} of {_plural(len(rows), 'signal')} raised, "
        "so this check is red — and it still blocks nothing."
        if raised
        else f"{_plural(len(rows), 'signal')}, and none is raised."
    )
    closing = (
        "`Dependency audit` found an advisory against a dependency this change did not touch, "
        "or could not audit at all. Neither is a reason to stop this pull request; both are "
        "reasons somebody should look this week. Its own block on this page says which."
        if raised
        else "This check is required by no branch rule and blocks no merge. It exists so that "
        '"correctness" and "taste" are two colours in the checks list rather than one line '
        "in a log: a red `CI advisory` beside a green `CI passed` is legible from the pull "
        "request page without opening anything."
    )
    return (
        block(
            job,
            "Raised." if raised else "Clear.",
            lead,
            table(("Signal", "State", "Decided by"), rows),
            closing,
        ),
        raised,
    )


#: Verdicts that report and never block. One list, here.
_ADVISORY: Final[frozenset[str]] = frozenset({"ci-advisory"})
#: The router. Not merely "did not fail" -- it must have SUCCEEDED.
_ROUTER: Final = "changes"
#: Routed by trigger and label rather than by the diff, so `changes` cannot clear
#: it in advance.
_TRIGGER_ROUTED: Final[frozenset[str]] = frozenset({"cross-platform"})


def render_verdict(
    job: str, needs: Mapping[str, Mapping[str, object]], may_skip: Sequence[str]
) -> tuple[str, bool, list[str]]:
    """The aggregate block, whether the run may merge, and one line per refusal."""
    results = {name: str(data.get("result", "")) for name, data in needs.items()}
    cleared = set(may_skip) | _TRIGGER_ROUTED | _ADVISORY
    refusals: list[str] = []

    router_dead = results.get(_ROUTER) != "success"
    if router_dead:
        refusals.append(
            f"`{_ROUTER}` reports `{results.get(_ROUTER)}`. Every job it gates then reports "
            "`skipped`, and a skip only means anything when the router ran."
        )
    for name, result in sorted(results.items()):
        if name == _ROUTER or name in _ADVISORY or result == "success":
            continue
        if result == "skipped":
            if name not in cleared:
                refusals.append(
                    f"`{name}` reports `skipped` and `changes` never cleared it — so either its "
                    "`if:` is wrong, or a job it `needs:` did not succeed and took it down with "
                    "it. That is the routing being wrong, which is more expensive than a test "
                    "failure."
                )
            continue
        refusals.append(
            f"`{name}` reports `{result}`. Its own block on this page says what it checked and "
            "at what scale."
        )

    if router_dead:
        return (
            block(
                job,
                "Red.",
                f"`{_ROUTER}` reports `{results.get(_ROUTER)}`, so this run proves nothing.",
                "Every job `changes` gates then reports `skipped`, and a skip only means "
                "anything when the router ran. None of those skips may be read as a pass. Fix "
                "`changes` and re-run; nothing else here is diagnosable until it succeeds.",
            ),
            False,
            refusals,
        )

    succeeded = sum(1 for result in results.values() if result == "success")
    skipped = sorted(name for name, result in results.items() if result == "skipped")
    lead = (
        f"All {len(results)} jobs accounted for: {succeeded} succeeded"
        + (f" and {len(skipped)} was skipped" if len(skipped) == 1 else "")
        + (f" and {len(skipped)} were skipped" if len(skipped) > 1 else "")
        + (" for a reason published in advance" if skipped else "")
        + ". This is the check the branch ruleset requires; nothing else on this page is."
        if not refusals
        else f"{len(results)} jobs accounted for: {succeeded} succeeded, "
        f"{sum(1 for r in results.values() if r not in ('success', 'skipped'))} did not, and "
        f"{len(skipped)} were skipped."
    )
    rows = [
        (
            f"`{name}`",
            result if result == "success" else f"**{result}**",
            _JOB_PURPOSE.get(name, "—"),
        )
        for name, result in sorted(results.items())
    ]
    refusal_list = (
        "### What refuses this run\n\n" + "\n".join(f"- {line}" for line in refusals)
        if refusals
        else ""
    )
    note = (
        f"`changes` cleared {', '.join(f'`{n}`' for n in may_skip) if may_skip else 'nothing'} to "
        "skip on this run; `cross-platform` is routed by trigger and label rather than by the "
        "diff, so `changes` cannot clear it in advance."
    )
    closing = (
        "This job runs no gate of its own. It reads every other job's verdict and applies three "
        "rules: `changes` must have **succeeded**, not merely not failed, because every job it "
        'gates would otherwise report `skipped` and a bare "skipped is fine" would read that '
        "as green; `ci-advisory` may fail; everything else must have succeeded, or be `skipped` "
        "for a reason `changes` published in advance. A job that skipped without appearing on "
        "that list has a wrong `if:` — a gate that quietly stopped, which is the one failure "
        "this design exists to be able to see."
    )
    return (
        block(
            job,
            "Red." if refusals else "Green.",
            lead,
            table(("Job", "Result", "What it answers"), rows),
            refusal_list,
            note,
            closing,
        ),
        not refusals,
        refusals,
    )


# --------------------------------------------------------------------------- #
# audit -- three exit codes, and the diff decides between two of them
# --------------------------------------------------------------------------- #


def render_audit(job: str, rc: str, deps: str) -> str:
    """Four verdicts, because `audit.sh` has a three-valued exit and the diff splits one.

    Flattening exit 4 into "pass" is precisely what that three-valued exit exists to
    prevent: an ecosystem nobody audited is a named gap, not a clean result.

    The sentences name the ecosystems rather than "the dependencies", because the page
    is where the over-claim was visible: a reader saw a green "Dependency audit" and had
    no way to learn that only one of the two lockfiles had ever been resolved.
    """
    if rc == "4":
        return block(
            job,
            "Incomplete.",
            "A tool this runner needs is missing, so at least one of the two lockfiles — "
            "`frontend/package-lock.json` (npm) and `uv.lock` (uv) — was not audited. Which one "
            "is named in the step log. A named gap, not a pass.",
            "`audit.sh` exits 4 rather than 0 precisely so this sentence can exist, and this "
            "job refuses `continue-on-error` because it would flatten that exit into a green.",
        )
    if rc == "0":
        return block(
            job,
            "Clear.",
            "2 lockfiles resolved — `npm audit` over `frontend/package-lock.json`, nothing at "
            "high or critical severity, and `uv audit` over `uv.lock`, no known vulnerability. "
            "The other 3 ecosystems carry no advisory query here and the step log says so for "
            "each: the base images, the Terraform providers and the actions are pinned, and "
            "something proposes the bump each pin freezes.",
            "From the lockfile only: no install, no network write, nothing modified — so two "
            "machines cannot answer this differently.",
            "The severity follows the diff rather than the calendar: a change that touches the "
            "dependency manifests owns the tree it resolved and this gate blocks, while a change "
            "that does not gets a red `CI advisory`, which no branch rule requires. This change "
            + ("touches" if deps == "true" else "does not touch")
            + " the manifests. Moderate advisories are printed in full in the step log even on a "
            "green run, because an advisory nobody sees is one nobody decides about.",
        )
    if deps == "true":
        return block(
            job,
            "Blocked.",
            "An ecosystem reports at least 1 advisory that fails its section — high-or-worse for "
            "`frontend/package-lock.json`, any severity for `uv.lock`, since `uv audit` has no "
            "threshold to set — and this change touches the dependency manifests, so it owns the "
            "tree it resolved and this gate blocks. The step log names which.",
            "Fix without a major bump with `npm audit fix` in `frontend/`, or "
            "`uv lock --upgrade-package <name>` for a wheel. If the advisory is "
            "genuinely unreachable here, say so in a dated row in `spec/changes/EXEMPTIONS.md` "
            "rather than lowering the severity threshold; `npm audit fix --force` is a major "
            "version bump applied by a machine at 3am.",
        )
    return block(
        job,
        "Advisory.",
        "An ecosystem reports at least 1 advisory that fails its section, against a dependency "
        "this change did not touch. Reported, not blocking. The step log names which of the 2 "
        "lockfiles.",
        "`CI advisory` carries it, and no branch rule requires that check. This job used to live "
        "inside `frontend`, where it turned every unrelated pull request red — which is how a "
        "gate earns a `--no-verify`.",
    )


# --------------------------------------------------------------------------- #
# The deployment workflows
# --------------------------------------------------------------------------- #


def _facts(rows: list[tuple[str, str]]) -> str:
    """Key/value lines, as a list rather than a table.

    Markdown has no headerless table, so a two-column table of facts renders an
    empty grey band above every deployment block. A definition list carries the same
    pairs and reads as prose, which is what these are.
    """
    return "\n".join(f"- **{key}** — {value}" for key, value in rows if value)


def render_deploy(job: str, environment: str, url: str, ref: str, mode: str, result: str) -> str:
    facts = _facts(
        [
            ("Environment", f"`{environment}`"),
            ("Commit", f"`{ref[:12]}`" if ref else ""),
            ("Mode", mode),
            ("URL", url),
        ]
    )
    if result != "success":
        return block(
            job,
            "Failed.",
            f"`./scripts/deploy.sh {environment} --yes` did not finish, and the environment may "
            "be partly moved: the script migrates before it publishes, so the schema can be "
            "ahead of the code.",
            facts,
            "That is the safe direction and the reason for the order — old code tolerates a new "
            "schema. Read `deploy.log` in this run's artefacts before re-running. A re-run is "
            "safe; a rollback is only meaningful once a version was actually published.",
        )
    if mode == "rollback":
        return block(
            job,
            "Rolled back.",
            f"The `{environment}` alias now serves the version published before the last one"
            + (f", at {url}" if url else "")
            + ". Nothing was rebuilt and nothing was deleted — the previous version was still "
            "there, which is what makes this take seconds.",
            facts,
            "The schema was **not** reverted, deliberately: a migration run backwards on a live "
            "database is far more dangerous than the one it would undo. If this rollback is not "
            "enough, the schema is what to look at next.",
        )
    return block(
        job,
        "Deployed.",
        f"`{environment}` is at {url or 'the address its Terraform output names'}"
        + (f", from `{ref[:12]}`" if ref else "")
        + ".",
        facts,
        "One script did all of it — the same one a person runs by hand: build, apply, "
        "**migrate**, publish, invalidate, smoke. That order is the only one with no window in "
        "which the code and the schema disagree, and it is what makes a rollback safe.",
        "The way back is one pointer rather than a redeploy: dispatch this workflow with "
        "**mode: rollback** and the alias serves the last version that actually served and "
        "passed its smoke, read from the release manifest — seconds, "
        "which is the only reason it is usable during an incident. It reverts neither the "
        "schema nor the SPA. The deploy log is kept for 7 days; the Terraform state and plan "
        "are not, because a state file carries the database's master password (Article XI).",
    )


def render_release(job: str, version: str, previous: str, bump: str, dry: str, result: str) -> str:
    facts = _facts(
        [
            ("Bump", f"{bump} (chosen)" if bump else ""),
            ("Previous", f"`{previous}`" if previous else ""),
            ("New", f"`{version}`" if version else ""),
            ("Dry run", "yes" if dry == "true" else "no"),
        ]
    )
    if result != "success":
        return block(
            job,
            "Refused.",
            "No tag was cut. A release is cut from the default branch, and the likeliest reason "
            "to land here is a dispatch from somewhere else.",
            facts,
            "`release.sh` refuses this too; it is asserted in the workflow as well because the "
            "message is better and the refusal is instant — a dispatch from the wrong branch is "
            "the likeliest way to try to release something unreviewed.",
        )
    if dry == "true":
        return block(
            job,
            "Dry run.",
            f"The next version would be `{version}` — a {bump} bump from `{previous}`. Nothing "
            "was tagged, nothing was published, and no deployment follows.",
            facts,
            "Run it again without the dry-run flag to cut the tag for real.",
        )
    return block(
        job,
        "Cut.",
        f"`{version}` — a {bump} bump from `{previous}`, tagged on the default branch, with "
        "release notes published.",
        facts,
        "The bump is chosen, never read out of a commit message: every deployment here is asked "
        "for, and a workflow that inferred significance from the first word of a message would "
        "be deciding rather than being asked.",
        "**Production is deployed by the job that calls `deploy.yml`, not by this tag.** A tag "
        "pushed with the workflow's own token triggers no `push:` workflow, so a release that "
        "created a tag and stopped would leave production on the previous version with every "
        "step green.",
    )


def render_preview(
    job: str, branch: str, slug: str, url: str, ref: str, commented: str, result: str = "success"
) -> str:
    facts = _facts(
        [
            ("Branch", f"`{branch}`"),
            ("Slug", f"`{slug}`"),
            ("Commit", f"`{ref[:12]}`" if ref else ""),
            ("URL", url),
            (
                "Pull request",
                f"#{commented}, comment edited in place"
                if commented and commented != "none"
                else "none open for this branch",
            ),
        ]
    )
    if result != "success":
        return block(
            job,
            "Failed.",
            f"The preview `{slug}` for `{branch}` was not raised"
            + (f", and the last URL it had was {url}" if url else " and has no URL")
            + ".",
            facts,
            "Terraform may have applied part of the stack before it stopped, so a retry is the "
            "first thing to try and `./scripts/preview.sh down` is the second. Read the log in "
            "this run's artefacts before either: a half-applied preview still costs money.",
        )

    tail = (
        ""
        if commented and commented != "none"
        else " No pull request is open for this branch, so the URL above is the only place it is "
        "written down."
    )
    return block(
        job,
        "Up.",
        f"Preview `{slug}` is at {url}, raised from `{branch}`.{tail}",
        facts,
        "It has its own database on the shared preview cluster. **The URL is public and "
        "unauthenticated** — treat it as a demo rather than as a staging environment, and put "
        "nothing in it you would not publish.",
        "Every branch shares one GitHub Environment named `preview`; the per-branch identity is "
        "the slug, which is both a state key and a resource-name prefix. It goes away when the "
        "pull request closes or the branch is deleted. The log is kept for 7 days; the Terraform "
        "state is not, because it carries the cluster's master password (Article XI).",
    )


def render_teardown(job: str, branch: str, slug: str, trigger: str, result: str) -> str:
    facts = _facts(
        [
            ("Branch", f"`{branch}`"),
            ("Slug", f"`{slug}`"),
            ("Trigger", f"`{trigger}`"),
            ("Terraform state key", f"`preview/{slug}`" if slug else ""),
        ]
    )
    if result != "success":
        return block(
            job,
            "Failed.",
            f"The preview `{slug}` for `{branch}` was not destroyed.",
            facts,
            "**A stack is still up and still costing money.** `./scripts/preview.sh down "
            f"{branch}` is the same command, and it needs neither uv nor Node — deliberately, "
            "so that a teardown still works while the toolchain is broken.",
        )
    return block(
        job,
        "Down.",
        f"The preview `{slug}` for `{branch}` was destroyed, triggered by `{trigger}`.",
        facts,
        "This ran **without the branch**. The chain is branch name → deterministic slug → "
        "Terraform state key → destroy from state, and the Terraform code came from the default "
        "branch, which is the whole reason the slug is derived rather than stored.",
        "A merge with auto-delete fires `pull_request: closed` and then `delete`, so you will "
        "often see two of these and both are correct: the second destroys an already-empty "
        "state and drops a database that is already gone. They serialise on the concurrency "
        "group rather than racing.",
    )


# --------------------------------------------------------------------------- #
# embed -- somebody else's Markdown, folded in without a second heading
# --------------------------------------------------------------------------- #


def render_embed(path: pathlib.Path, demote: int, title: str) -> str:
    """Fold an existing document into the page, its headings pushed down.

    The named exception for a page with two writers: the first writer owns the
    `##` heading, and this appends a `<details>` continuation, never a heading of its
    own. Written for the specification gates' page (a job that has since moved to the
    process's own CI, with its own reporter), and kept for the next
    page that folds a generated document in: without the demotion a document opening
    with an h1 lands as an h1 in the middle of a page whose own sections are h2.
    """
    if not path.is_file():
        return ""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip("#")
        level = len(line) - len(stripped)
        lines.append("#" * (level + demote) + stripped if level else line)
    return details(title, "\n".join(lines).strip("\n")) + "\n"


# --------------------------------------------------------------------------- #
# census -- the only branch here that decides anything
# --------------------------------------------------------------------------- #


def census(path: pathlib.Path, *, require_report: bool, expect_nonempty: bool, what: str) -> int:
    """Refuse a suite that proved nothing. Writes no page; the reporter already did.

    A suite that ran and found nothing reads on a dashboard exactly like one that
    passed, which is the whole argument. The asymmetry between the two callers is
    deliberate and predates this module: for `e2e`, "no report at all" is exit 0,
    because on an early failure the job is red already and a second error is noise.
    """
    report = read_junit(path)
    if report is None:
        if require_report:
            print(f"::error::no report at {path} -- the {what} suite never wrote one")
            return 1
        return 0
    if expect_nonempty and report.total == 0:
        print(
            f"::error::the report at {path} contains no {what} at all. A suite that ran and "
            "found nothing reads on a dashboard exactly like one that passed."
        )
        return 1
    return 0


# --------------------------------------------------------------------------- #
# The command line
# --------------------------------------------------------------------------- #


def _emit(page: str, markdown: str | None) -> None:
    """stdout always, so the step log shows exactly what the page got."""
    print(page)
    if markdown:
        with open(markdown, "a", encoding="utf-8") as handle:
            handle.write(page if page.endswith("\n") else page + "\n")


def _output(github_output: str | None, **values: str) -> None:
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _json(raw: str) -> dict[str, dict[str, object]]:
    """A GitHub context, or an empty one. Never raises: this is a reporter."""
    try:
        parsed = json.loads(raw or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _split(raw: str) -> list[str]:
    return [part for part in (raw or "").replace(",", " ").split() if part]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ and __doc__.splitlines()[0])
    parser.add_argument("--markdown", default=None, help="a file to append the block to")
    sub = parser.add_subparsers(dest="command", required=True)

    def with_job(name: str, **kwargs: str) -> argparse.ArgumentParser:
        made = sub.add_parser(name, **kwargs)  # type: ignore[arg-type]
        made.add_argument("--job", required=True, help="the job's `name:`, verbatim")
        made.add_argument("--result", default="success", help="${{ job.status }}")
        made.add_argument("--markdown", default=None)
        return made

    suite = with_job("suite", help="a test suite's block")
    suite.add_argument("--shape", choices=("pytest", "vitest", "bdd"), required=True)
    suite.add_argument("--junit", required=True)
    suite.add_argument("--cobertura", default="")
    suite.add_argument("--vitest-json", default="")
    suite.add_argument("--subject", default="app/", help="what the coverage figure is about")
    suite.add_argument("--extra", default="", help="one more paragraph, from the caller")
    # A job that proves more than its suite renders that table inside the suite
    # block: one writer per job is the rule, so a second step is not an option.
    suite.add_argument("--job-id", default="", help="render this job's check table too")
    suite.add_argument("--steps", default="{}", help="${{ toJSON(steps) }}")

    gate = sub.add_parser("census", help="refuse a suite that proved nothing")
    gate.add_argument("--junit", required=True)
    gate.add_argument("--require-report", action="store_true")
    gate.add_argument("--expect-nonempty", action="store_true")
    gate.add_argument("--what", default="tests")

    checks = with_job("checks", help="a job whose result is a set of independent checks")
    checks.add_argument("--job-id", required=True, help="the job's key in the workflow")
    checks.add_argument("--steps", default="{}", help="${{ toJSON(steps) }}")

    route = with_job("route", help="the routing verdict")
    route.add_argument("--files-from", default="")
    route.add_argument("--may-skip", default="")
    route.add_argument("--base", default="")
    route.add_argument("--deps", default="")
    route.add_argument("--ci-self", default="")
    route.add_argument("--reason", default="", help="why the fail-safe path was taken")

    audit = with_job("audit", help="the dependency audit's block")
    audit.add_argument("--rc", default="0", help="audit.sh's exit code: 0, 1 or 4")
    audit.add_argument("--deps", default="", help="whether the diff touches the manifests")

    advisory = with_job("advisory", help="the advisory signals")
    advisory.add_argument("--needs", default="{}", help="${{ toJSON(needs) }}")
    advisory.add_argument("--github-output", default="")

    verdict = with_job("verdict", help="the aggregate verdict")
    verdict.add_argument("--needs", default="{}", help="${{ toJSON(needs) }}")
    verdict.add_argument("--may-skip", default="")
    verdict.add_argument("--github-output", default="")

    embed = sub.add_parser("embed", help="fold an existing document into the page")
    embed.add_argument("--from", dest="source", required=True)
    embed.add_argument("--demote", type=int, default=2)
    embed.add_argument("--details", dest="title", required=True)
    embed.add_argument("--markdown", default=None)

    deploy = with_job("deploy", help="a deployment's block")
    deploy.add_argument("--environment", required=True)
    deploy.add_argument("--url", default="")
    deploy.add_argument("--ref", default="")
    deploy.add_argument("--mode", default="deploy")

    release = with_job("release", help="a release tag's block")
    release.add_argument("--version", default="")
    release.add_argument("--previous", default="")
    release.add_argument("--bump", default="")
    release.add_argument("--dry-run", dest="dry", default="false")

    preview = with_job("preview", help="a preview environment's block")
    preview.add_argument("--branch", default="")
    preview.add_argument("--slug", default="")
    preview.add_argument("--url", default="")
    preview.add_argument("--ref", default="")
    preview.add_argument("--commented", default="none")

    teardown = with_job("teardown", help="a preview teardown's block")
    teardown.add_argument("--branch", default="")
    teardown.add_argument("--slug", default="")
    teardown.add_argument("--trigger", default="")

    args = parser.parse_args(argv)
    markdown = getattr(args, "markdown", None) or None

    if args.command == "census":
        return census(
            pathlib.Path(args.junit),
            require_report=args.require_report,
            expect_nonempty=args.expect_nonempty,
            what=args.what,
        )

    if args.command == "suite":
        coverage = ""
        if args.cobertura:
            coverage = cobertura_section(pathlib.Path(args.cobertura), args.subject)
        elif args.vitest_json:
            coverage = vitest_coverage_section(pathlib.Path(args.vitest_json), args.subject)
        extra = args.extra
        if args.job_id:
            rows = _check_rows(args.job_id, _json(args.steps))
            extra = "\n\n".join(part for part in (rows, extra) if part)
        page = render_suite(
            args.job, args.shape, read_junit(pathlib.Path(args.junit)), coverage, extra, args.result
        )
    elif args.command == "checks":
        page = render_checks(args.job, args.job_id, _json(args.steps), args.result)
    elif args.command == "route":
        files: list[str] = []
        if args.files_from and pathlib.Path(args.files_from).is_file():
            files = pathlib.Path(args.files_from).read_text(encoding="utf-8").split()
        page = render_route(
            args.job,
            files,
            _split(args.may_skip),
            args.base,
            args.deps,
            args.ci_self,
            args.reason,
        )
    elif args.command == "audit":
        page = render_audit(args.job, args.rc, args.deps)
    elif args.command == "advisory":
        page, raised = render_advisory(args.job, _json(args.needs))
        _output(args.github_output or None, raised="true" if raised else "false")
    elif args.command == "verdict":
        page, ok, refusals = render_verdict(args.job, _json(args.needs), _split(args.may_skip))
        for line in refusals:
            print(f"::error::{line}")
        _output(args.github_output or None, ok="true" if ok else "false")
    elif args.command == "embed":
        page = render_embed(pathlib.Path(args.source), args.demote, args.title)
    elif args.command == "deploy":
        page = render_deploy(args.job, args.environment, args.url, args.ref, args.mode, args.result)
    elif args.command == "release":
        page = render_release(
            args.job, args.version, args.previous, args.bump, args.dry, args.result
        )
    elif args.command == "preview":
        page = render_preview(
            args.job, args.branch, args.slug, args.url, args.ref, args.commented, args.result
        )
    else:
        page = render_teardown(args.job, args.branch, args.slug, args.trigger, args.result)

    _emit(page, markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
