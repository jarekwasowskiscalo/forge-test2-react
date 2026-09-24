"""The CI reporter: the house style, the three report shapes, and Article XI.

`scripts/ci_summary.py` is the one writer of every job's summary block, and this is
what stops it becoming what it replaced. The old reporters were seven inline
heredocs, and there was nowhere to put a rule about them and nothing to test one
against -- so they disagreed about heading level, about the dash, and about whether
a clean run says what it looked at.

Here rather than beside the module: `pyproject.toml`'s `testpaths` names `tests`,
so a test file under `scripts/` is never collected;
`pythonpath` names `scripts`, so the import needs no bootstrap; and
`tests/tooling/conftest.py` marks everything here `no_db`, which is what puts it on
the macOS leg as well.

Fixtures are built into `tmp_path` rather than committed. A committed `.xml` would
add paths for the `backtick-paths` gate to judge, and it would hide the shape being
tested inside a file nobody opens while reading the assertion.
"""

import ast
import json
import pathlib
import re
import sys
from typing import Final

import ci_summary
import pytest

_REPO: Final = pathlib.Path(__file__).resolve().parent.parent.parent
_WORKFLOWS: Final = _REPO / ".github" / "workflows"

#: A junit whose every text-bearing corner holds something that must never reach a
#: page: a person's name in an assertion message, an address, an IBAN, and a
#: captured stdout. Real reports carry all four shapes.
_LOADED: Final = """<?xml version="1.0"?>
<testsuites><testsuite name="src/lib/x.test.ts" tests="2" failures="1" errors="0" time="1.5">
  <testcase classname="tests.unit.x" name="test_one" time="0.5">
    <failure message="expected 'Ada Lovelace' to equal 'Bob Smith'">
      assert entry.author == 'Ada Lovelace'
      E  ada@example.com
      E  GB29NWBK60161331926819
    </failure>
    <system-out>signed by ada@example.com</system-out>
  </testcase>
  <testcase classname="tests.integration.y" name="test_two" time="1.0"/>
</testsuite></testsuites>
"""

_SECRETS: Final[tuple[str, ...]] = (
    "Ada Lovelace",
    "Bob Smith",
    "ada@example.com",
    "GB29NWBK60161331926819",
    "assert entry.author",
    "signed by",
)


def _junit(tmp_path: pathlib.Path, body: str, name: str = "report.xml") -> pathlib.Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def _pytest_report(cases: str) -> str:
    return (
        f'<testsuites><testsuite name="pytest" tests="9" time="30">{cases}</testsuite></testsuites>'
    )


def _every_block(tmp_path: pathlib.Path) -> dict[str, str]:
    """One rendered block per renderer, so a rule can be asserted over all of them."""
    loaded = _junit(tmp_path, _LOADED)
    report = ci_summary.read_junit(loaded)
    assert report is not None
    steps = {"ruff": {"outcome": "success"}, "types": {"outcome": "failure"}}
    needs = {
        "changes": {"result": "success"},
        "backend": {"result": "failure"},
        "audit": {"result": "success", "outputs": {"advisory": "true"}},
        "ci-advisory": {"result": "success"},
    }
    blocks = {
        "pytest": ci_summary.render_suite("Backend tests", "pytest", report, "", ""),
        "vitest": ci_summary.render_suite("Frontend and API contract", "vitest", report, "", ""),
        "bdd": ci_summary.render_suite("End-to-end", "bdd", report, "", ""),
        "no-report": ci_summary.render_suite("Backend tests", "pytest", None, "", ""),
        "checks": ci_summary.render_checks("Lint, types, hygiene", "quality", steps, "failure"),
        "checks-infra": ci_summary.render_checks("Infrastructure", "infra", {}, "success"),
        "checks-skipped": ci_summary.render_checks("macos-latest", "cross-platform", {}, "skipped"),
        "route": ci_summary.render_route(
            "What changed", ["app/x.py"], ["image"], "abc123def456", "false", "false", ""
        ),
        "route-failsafe": ci_summary.render_route(
            "What changed", [], [], "", "", "", "the base is the null sha (a new branch)"
        ),
        "audit-clear": ci_summary.render_audit("Dependency audit", "0", "false"),
        "audit-blocked": ci_summary.render_audit("Dependency audit", "1", "true"),
        "audit-advisory": ci_summary.render_audit("Dependency audit", "1", "false"),
        "audit-incomplete": ci_summary.render_audit("Dependency audit", "4", "false"),
        "advisory": ci_summary.render_advisory("CI advisory", needs)[0],
        "verdict": ci_summary.render_verdict("CI passed", needs, [])[0],
        "deploy": ci_summary.render_deploy(
            "stage", "stage", "https://x", "abc123", "deploy", "success"
        ),
        "rollback": ci_summary.render_deploy(
            "stage", "stage", "https://x", "abc123", "rollback", "success"
        ),
        "release": ci_summary.render_release(
            "tag", "v1.4.0", "v1.3.2", "minor", "false", "success"
        ),
        "preview": ci_summary.render_preview("preview (b)", "b", "b-1", "https://x", "abc", "42"),
        "teardown": ci_summary.render_teardown("teardown", "b", "b-1", "delete", "success"),
    }
    return blocks


# --------------------------------------------------------------------------- #
# The house style, asserted rather than described
# --------------------------------------------------------------------------- #


def test_every_block_follows_the_house_style(tmp_path: pathlib.Path) -> None:
    """One `##`, no `#`, no stray `###`, and a closing sentence rather than a table.

    The rule is in the module's docstring; without this test it would be a
    convention, which is exactly what the seven heredocs had.
    """
    for label, page in _every_block(tmp_path).items():
        lines = page.splitlines()
        headings = [line for line in lines if line.startswith("#")]
        assert headings, f"{label}: no heading at all"
        assert headings[0].startswith("## "), f"{label}: opens with {headings[0]!r}"
        assert sum(1 for line in headings if line.startswith("## ")) == 1, f"{label}: two headings"
        assert not [line for line in headings if re.match(r"^# [^#]", line)], f"{label}: an h1"
        body = [line for line in lines if line.strip()]
        assert not body[-1].startswith("|"), (
            f"{label}: the last line is a table row. Every block ends with a sentence saying "
            "what a failure would mean or what to do next."
        )
        assert page.endswith("\n"), f"{label}: no trailing newline"


def test_no_block_uses_the_ascii_double_dash(tmp_path: pathlib.Path) -> None:
    """`--` belongs in YAML and shell comments and never reaches a rendered page.

    The one line that cements the typography half of the rule. Before this module the
    same page carried `--` from five heredocs and a real em dash from a sixth.
    """
    for label, page in _every_block(tmp_path).items():
        offenders = [line for line in page.splitlines() if " -- " in line]
        assert not offenders, f"{label}: {offenders}"


def test_a_green_block_still_states_its_scale(tmp_path: pathlib.Path) -> None:
    """The `All clear.` regression, applied to every renderer.

    A verdict on its own is a claim. A block that carries no digit at all is one
    that could say the same thing over an empty tree.
    """
    for label, page in _every_block(tmp_path).items():
        if label in {"no-report", "route-failsafe"}:
            continue  # these state, correctly, that there was nothing to measure
        assert re.search(r"\d", page), f"{label}: names no number, so its verdict is a claim"


def test_every_block_names_its_job(tmp_path: pathlib.Path) -> None:
    """Block order on the summary page is job-completion order and cannot be
    influenced, so a block is findable only by what it is called."""
    for label, page in _every_block(tmp_path).items():
        assert page.splitlines()[0].startswith("## "), label


# --------------------------------------------------------------------------- #
# Article XI
# --------------------------------------------------------------------------- #


def test_no_block_can_carry_a_failure_message_or_a_captured_line(
    tmp_path: pathlib.Path,
) -> None:
    """Fed a report holding a name, an address, an IBAN and a captured line: none reach a page.

    Behavioural rather than textual, and deliberately: this module legitimately
    opens junit files, so "the source does not mention the report" is not available
    to it the way it is to `spec_summary.py`. What is available is feeding it the
    thing that must not escape and looking at what comes out.
    """
    pages = "\n".join(_every_block(tmp_path).values())
    for secret in _SECRETS:
        assert secret not in pages, f"{secret!r} reached a job summary (Article XI)"
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", pages), "an address reached a job summary"


def test_the_reporter_has_no_route_to_a_report_s_text() -> None:
    """The static half: it must not be able to read the text, not merely refrain.

    A behavioural test proves today's renderers are clean. This one is what stops
    somebody adding a "why did it fail" column tomorrow -- the failure mode is banal
    and the consequence is a person's data on a page that outlives the runner.
    """
    tree = ast.parse((_REPO / "scripts" / "ci_summary.py").read_text(encoding="utf-8"))
    # Docstrings are excluded, and they have to be: the module's own docstring names
    # every one of these tokens in the paragraph explaining why it must not read them.
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.FunctionDef | ast.ClassDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr != "text", "reading an element's .text is a route to the message"
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            # The EXACT literal, not a substring: `element.get("message")` is a
            # route to the text, while a closing sentence that says the page never
            # carries a failure message is the rule being written down.
            assert node.value not in ("system-out", "system-err", "message"), (
                f"the literal {node.value!r} appears in executable code, which is a route to a "
                "report's text (Article XI)"
            )


# --------------------------------------------------------------------------- #
# The three report shapes
# --------------------------------------------------------------------------- #


def test_a_failed_case_with_no_failure_child_still_reads_as_a_pass(
    tmp_path: pathlib.Path,
) -> None:
    """The outcome is the presence of a child element, never a `status` attribute.

    A previous runner emitted `status=` and pytest's `xunit2` family does not, so a
    parser still reading it reported 0 of 21 on a green run, under a green check,
    which nobody investigates. Cemented here rather than left as a comment.
    """
    report = ci_summary.read_junit(
        _junit(
            tmp_path,
            _pytest_report(
                '<testcase classname="tests.a" name="test_x" status="failed" time="1"/>'
            ),
        )
    )
    assert report is not None
    assert report.failed == 0
    assert report.passed == 1


@pytest.mark.parametrize("shape", ["pytest", "vitest", "bdd"])
def test_a_green_suite_under_a_red_job_says_so_rather_than_passing(
    tmp_path: pathlib.Path, shape: str
) -> None:
    """These jobs do more than run tests, and the block belongs to the job.

    `backend` also resolves the Lambda package, `frontend` also checks two contracts
    and builds the bundle, `e2e` also builds the SPA. Reading the verdict off the
    report alone printed **Passed.** on a job that went red after its suite finished
    -- a page contradicting the check it is attached to, which is the same defect the
    `infra` block had and the `preview` block had.
    """
    report = ci_summary.read_junit(
        _junit(tmp_path, _pytest_report('<testcase classname="tests.a" name="t" time="1"/>'))
    )
    page = ci_summary.render_suite("Backend tests", shape, report, "", "", "failure")
    assert "**Failed.**" in page
    assert "the job still reports `failure`" in page
    green = ci_summary.render_suite("Backend tests", shape, report, "", "", "success")
    assert "**Passed.**" in green
    assert "still reports" not in green


def test_no_block_claims_success_in_prose_under_a_failed_verdict(
    tmp_path: pathlib.Path,
) -> None:
    """A verdict and the sentence under it cannot disagree.

    Found three times while reviewing this module, each in a block whose lead was a
    fixed string: `infra` asserted every root was canonical, `preview` announced an
    environment that was never raised, and the suite blocks called a red job passed.
    """
    failures = {
        "infra": ci_summary.render_checks("Infrastructure", "infra", {}, "failure"),
        "preview": ci_summary.render_preview("p", "b", "s", "", "abc", "none", "failure"),
        "deploy": ci_summary.render_deploy("stage", "stage", "", "abc", "deploy", "failure"),
        "teardown": ci_summary.render_teardown("t", "b", "s", "delete", "failure"),
        "release": ci_summary.render_release("tag", "", "v1", "minor", "false", "failure"),
    }
    for label, page in failures.items():
        assert "**Failed.**" in page or "**Refused.**" in page, f"{label}: verdict is not a failure"
        lead = page.split("\n\n")[1]
        for claim in ("is in canonical form", "is at http", "was destroyed", "**Up.**", "**Cut.**"):
            assert claim not in lead, f"{label}: the lead claims {claim!r} under a failure"


def test_the_backend_buckets_report_an_unclassified_classname(tmp_path: pathlib.Path) -> None:
    """A classname matching neither prefix means the layout moved.

    The bucket is reported even at zero, because a bucket that quietly absorbed it
    would hide exactly the thing it exists to show.
    """
    report = ci_summary.read_junit(
        _junit(
            tmp_path,
            _pytest_report(
                '<testcase classname="tests.a" name="t1" time="1"/>'
                '<testcase classname="somewhere.else" name="t3" time="1"/>'
            ),
        )
    )
    page = ci_summary.render_suite("Backend tests", "pytest", report, "", "")
    assert "| unclassified | 1 |" in page
    assert "product (`tests/`)" in page


def test_the_vitest_shape_sums_failures_and_errors(tmp_path: pathlib.Path) -> None:
    """A `<testsuite>` counts the two separately and a reader wants one number."""
    report = ci_summary.read_junit(
        _junit(
            tmp_path,
            '<testsuites><testsuite name="src/a.test.ts" tests="4" failures="1" errors="2" '
            'time="0.5"><testcase classname="a" name="t" time="0.5"/></testsuite></testsuites>',
        )
    )
    assert report is not None
    assert report.files[0].failures == 3


def test_the_bdd_shape_demangles_the_scenario_title(tmp_path: pathlib.Path) -> None:
    """pytest-bdd turns the sentence in the feature file into an identifier.

    This is as close to that sentence as the report can get back to, and it is the
    difference between a table a non-programmer reads and a list of function names.
    """
    report = ci_summary.read_junit(
        _junit(
            tmp_path,
            _pytest_report(
                '<testcase classname="e2e" name="test_a_visitor_signs_the_guestbook" time="2"/>'
            ),
        )
    )
    page = ci_summary.render_suite("End-to-end", "bdd", report, "", "")
    assert "| a visitor signs the guestbook | PASS |" in page


@pytest.mark.parametrize(
    ("what", "body"),
    [
        ("an empty report", "<testsuites></testsuites>"),
        ("a truncated document", '<testsuites><testsuite name="x" tests="2'),
        ("something that is not XML at all", "not xml"),
    ],
)
def test_a_degenerate_report_renders_a_block_rather_than_raising(
    tmp_path: pathlib.Path, what: str, body: str
) -> None:
    """The heredocs this replaces would crash the step on a half-written junit."""
    page = ci_summary.render_suite(
        "Backend tests", "pytest", ci_summary.read_junit(_junit(tmp_path, body)), "", ""
    )
    assert page.startswith("## Backend tests"), what


@pytest.mark.parametrize("result", ["failure", "cancelled"])
@pytest.mark.parametrize("job_id", [*sorted(ci_summary._CHECKS), "a-job-nobody-declared"])
def test_a_red_job_renders_whether_or_not_it_has_a_lead(job_id: str, result: str) -> None:
    """A job `_CHECKS_LEAD` says nothing about still gets its block.

    Live on 2026-09-16, run 35088488387: the `changelog` gate refused a pull request
    that carried no entry -- correctly -- and the step that reports the refusal died
    with `IndexError: string index out of range`. The guard was written
    `* bool(context)`, which multiplies the f-string *after* it is interpolated, so
    `context[0]` was indexed whether or not there was a `context` to index. A reader
    got a traceback where the verdict belongs, on the one path where the page matters
    most: the red one.

    Parametrised over every declared job rather than the two with no lead today,
    plus a job id `_CHECKS` does not carry at all -- that last one keeps the
    empty-lead branch exercised even if every declared job later gains a sentence,
    and it is what a renamed `id:` in the workflow would hand the reporter.
    """
    page = ci_summary.render_checks("Some job", job_id, {}, result)
    lead = next((line for line in page.splitlines() if line.startswith("**")), "")
    assert lead, f"{job_id}/{result}: the block carries no verdict line"
    assert lead.endswith("."), f"{job_id}/{result}: an unfinished sentence: {lead!r}"


# --------------------------------------------------------------------------- #
# Only the gate may fail a build
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "argv",
    [
        ["suite", "--shape", "pytest", "--job", "x", "--junit", "MISSING"],
        ["suite", "--shape", "vitest", "--job", "x", "--junit", "DIR"],
        ["suite", "--shape", "bdd", "--job", "x", "--junit", "TRUNCATED"],
        ["checks", "--job", "x", "--job-id", "quality", "--steps", "not json"],
        ["route", "--job", "x", "--files-from", "MISSING"],
        ["advisory", "--job", "x", "--needs", "not json"],
        ["verdict", "--job", "x", "--needs", "not json"],
        ["embed", "--from", "MISSING", "--details", "x"],
        ["audit", "--job", "x", "--rc", "nonsense"],
        ["deploy", "--job", "x", "--environment", "stage"],
        ["release", "--job", "x"],
        ["preview", "--job", "x"],
        ["teardown", "--job", "x"],
    ],
)
def test_a_reporting_subcommand_returns_zero_on_every_path(
    tmp_path: pathlib.Path, argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """A reporter that can turn a green run red is a reporter people delete."""
    truncated = _junit(tmp_path, '<testsuites><testsuite name="x" tests="2', "bad.xml")
    resolved = [
        str(tmp_path / "nothing.xml")
        if part == "MISSING"
        else str(tmp_path)
        if part == "DIR"
        else str(truncated)
        if part == "TRUNCATED"
        else part
        for part in argv
    ]
    assert ci_summary.main(resolved) == 0
    capsys.readouterr()


@pytest.mark.parametrize(
    ("what", "body", "require", "expect", "code"),
    [
        ("a populated report", '<testcase classname="a" name="t"/>', True, True, 0),
        ("an empty report", "", True, True, 1),
        ("an empty report, e2e's flags", "", False, True, 1),
        ("no report, frontend's flags", None, True, True, 1),
        ("no report, e2e's flags", None, False, True, 0),
    ],
)
def test_the_census_is_the_only_thing_here_that_decides(
    tmp_path: pathlib.Path,
    what: str,
    body: str | None,
    require: bool,
    expect: bool,
    code: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The three gates that used to hide inside reporters, in one place.

    The asymmetry is deliberate and predates this module: for `e2e`, "no report at
    all" is exit 0, because on an early failure the job is red already and a second
    error is noise. `frontend` has nothing else refusing an uncollected suite, so
    for it a missing report is a failure too.
    """
    path = tmp_path / "gone.xml" if body is None else _junit(tmp_path, _pytest_report(body))
    assert (
        ci_summary.census(path, require_report=require, expect_nonempty=expect, what="tests")
        == code
    ), what
    capsys.readouterr()


def test_only_the_census_can_return_non_zero() -> None:
    """The source half of the rule above: one `return 1`, and it is in the gate."""
    source = (_REPO / "scripts" / "ci_summary.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    returning = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        for inner in ast.walk(node)
        if isinstance(inner, ast.Return)
        and isinstance(inner.value, ast.Constant)
        and inner.value.value == 1
    }
    assert returning == {"census"}, (
        f"only `census` may return a failing code; these also do: {sorted(returning - {'census'})}"
    )


# --------------------------------------------------------------------------- #
# The module's constants against the world
# --------------------------------------------------------------------------- #


def test_the_module_imports_the_standard_library_only() -> None:
    """What keeps it runnable on the bare `scripts` runner and inside a teardown.

    Those jobs install no toolchain by design, so `uv run` is not available to them
    and a single third-party import would be discovered at the worst moment.
    """
    source = (_REPO / "scripts" / "ci_summary.py").read_text(encoding="utf-8")
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    assert roots <= set(sys.stdlib_module_names), sorted(roots - set(sys.stdlib_module_names))


def test_the_terraform_roots_match_the_script_that_walks_them() -> None:
    """The page names the five roots; `infra-check.sh` is what actually checks them."""
    script = (_REPO / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    match = re.search(r"^ROOTS=\((.*?)\)", script, re.MULTILINE)
    assert match, "infra-check.sh no longer declares ROOTS=(...) -- update this parser"
    assert tuple(match.group(1).split()) == ci_summary._TERRAFORM_ROOTS


def test_the_job_purposes_cover_exactly_what_the_required_check_waits_on() -> None:
    """A job added to `ci`'s `needs:` and forgotten here would appear in the
    aggregate table with an em dash where its purpose belongs."""
    text = (_WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    # Four jobs declare `needs:`; the required check's is the one naming every other
    # job, so it is the longest. Picking the first match found `audit`'s.
    lists = re.findall(r"^\s+needs: \[(.+?)\]$", text, re.MULTILINE)
    assert lists, "ci.yml no longer declares a bracketed needs: list -- update this parser"
    longest = max(lists, key=len)
    assert {name.strip() for name in longest.split(",")} == set(ci_summary._JOB_PURPOSE)


def test_every_declared_check_step_exists_in_the_workflow() -> None:
    """The prose table is keyed by step id, so a renamed `id:` would silently drop a
    row from a page that still claims to list every check."""
    text = (_WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    declared = set(re.findall(r"^\s+id: ([a-z][a-z0-9-]*)$", text, re.MULTILINE))
    for job_id, checks in ci_summary._CHECKS.items():
        missing = sorted(step for step, _what, _looked in checks if step not in declared)
        assert not missing, f"{job_id}: these step ids are in no ci.yml step: {missing}"


# --------------------------------------------------------------------------- #
# Every job reports
# --------------------------------------------------------------------------- #


def _application_workflows() -> list[pathlib.Path]:
    """Every workflow in this repository, because every one of them is the application's.

    This used to subtract the change process's own workflow by name. Nothing was ever
    subtracted -- that file lives in the process's repository, not this one -- and a
    template naming a file of the process is the coupling the script contract forbids
    outright. A filter that removes nothing is also a filter nothing can be seen to
    break, so it went rather than being corrected.
    """
    return sorted(_WORKFLOWS.glob("*.yml"))


def test_every_job_in_every_workflow_writes_a_summary() -> None:
    """The assertion that makes "every job explains itself" mechanical.

    Parsed with anchored regexes rather than PyYAML, for the reason
    `test_sdd_ci_parity.py` gives: it is not a dependency of this project, and a
    parser that needs one is a parser that cannot run where the workflows do.

    A new job with no summary fails the build, exactly as a new job missing from
    `ci`'s `needs:` does today.
    """
    for workflow in _application_workflows():
        text = workflow.read_text(encoding="utf-8")
        _, sep, below = text.partition("\njobs:\n")
        assert sep, f"{workflow.name} has no top-level `jobs:` key"
        blocks = re.split(r"^  ([a-z][a-z0-9-]*):$", below, flags=re.MULTILINE)[1:]
        for name, body in zip(blocks[::2], blocks[1::2], strict=True):
            # A job that IS a call to a reusable workflow has no steps of its own, so
            # it cannot run the reporter; the workflow it calls writes the summary.
            if re.search(r"^    uses:\s", body, re.MULTILINE):
                continue
            # And a job whose work is the change process's own action: the gates write
            # their table straight to $GITHUB_STEP_SUMMARY, from the one implementation
            # that knows what a gate is. A second summary here would restate it.
            if "claude-marketplace/.github/actions/" in body:
                continue
            assert "ci_summary.py" in body, (
                f"{workflow.name}: job `{name}` writes no summary. Every job says what it "
                "looked at, at what scale, and what its verdict means."
            )


def test_every_summary_step_runs_even_when_the_job_failed() -> None:
    """`if: always()`, because the run whose page matters most is the one that just
    failed. Without it a red job is exactly the one that explains nothing."""
    for workflow in _application_workflows():
        text = workflow.read_text(encoding="utf-8")
        for block in re.findall(r"\n      - name: [^\n]*\n(?:(?!\n      - ).)*", text, re.DOTALL):
            if "ci_summary.py" in block and "census" not in block:
                assert "if: always()" in block, (
                    f"{workflow.name}: a summary step without `if: always()`:\n{block[:200]}"
                )


def test_no_workflow_reintroduces_an_inline_summary_heredoc() -> None:
    """One writer per job means one implementation, and the heredocs are why."""
    for workflow in sorted(_WORKFLOWS.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        assert "GITHUB_STEP_SUMMARY" not in text.replace('markdown "$GITHUB_STEP_SUMMARY"', ""), (
            f"{workflow.name} writes to the summary page outside `ci_summary.py`"
        )


# --------------------------------------------------------------------------- #
# The required check's three rules, unchanged by the move
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("what", "results", "may_skip", "ok"),
    [
        ("everything green", {"changes": "success", "backend": "success"}, [], True),
        ("the router failed", {"changes": "failure", "backend": "skipped"}, [], False),
        ("the router was cancelled", {"changes": "cancelled", "backend": "skipped"}, [], False),
        ("the router itself skipped", {"changes": "skipped", "backend": "skipped"}, [], False),
        ("a cleared skip", {"changes": "success", "image": "skipped"}, ["image"], True),
        ("an uncleared skip", {"changes": "success", "image": "skipped"}, [], False),
        (
            "cross-platform skipped with an empty may_skip",
            {"changes": "success", "cross-platform": "skipped"},
            [],
            True,
        ),
        (
            "the advisory check alone is red",
            {"changes": "success", "ci-advisory": "failure"},
            [],
            True,
        ),
        ("a job failed", {"changes": "success", "backend": "failure"}, [], False),
        ("a job was cancelled", {"changes": "success", "backend": "cancelled"}, [], False),
    ],
)
def test_the_aggregate_verdict_keeps_its_three_rules(
    what: str, results: dict[str, str], may_skip: list[str], ok: bool
) -> None:
    """The most load-bearing logic in the repository, moved from a heredoc into a
    module. These cases were written against the heredoc's behaviour first.

    `changes` must have **succeeded**, not merely not failed; `ci-advisory` may
    fail; everything else must have succeeded or be `skipped` for a reason published
    in advance.
    """
    needs = {name: {"result": result} for name, result in results.items()}
    _page, verdict, refusals = ci_summary.render_verdict("CI passed", needs, may_skip)
    assert verdict is ok, f"{what}: {refusals}"
    assert bool(refusals) is not ok, what


def test_a_dead_router_says_the_skips_prove_nothing() -> None:
    """A skip only means anything when the router ran, and the page has to say so:
    a page listing eleven `skipped` rows under a red check invites the reading that
    ten of them were fine."""
    needs = {"changes": {"result": "failure"}, "image": {"result": "skipped"}}
    page, verdict, _refusals = ci_summary.render_verdict("CI passed", needs, [])
    assert verdict is False
    assert "proves nothing" in page
    assert "may be read as a pass" in page


def test_the_advisory_flag_survives_the_json_round_trip() -> None:
    """The flag reaches this module through `toJSON(needs)`, one level deeper than
    the job's own `outputs` context."""
    needs = json.loads('{"audit": {"result": "success", "outputs": {"advisory": "true"}}}')
    page, raised = ci_summary.render_advisory("CI advisory", needs)
    assert raised is True
    assert "**raised**" in page


# --------------------------------------------------------------------------- #
# embed
# --------------------------------------------------------------------------- #


def test_embedding_demotes_headings_so_the_page_keeps_one_level(
    tmp_path: pathlib.Path,
) -> None:
    """`traceability.py` opens with an h1, which landed in the middle of a page
    whose own sections are h2. The `specs` job is the one job with two writers, and
    this keeps the second one from ever adding a heading of its own."""
    source = tmp_path / "matrix.md"
    source.write_text("# Requirement coverage\n\ntext\n\n## Detail\n", encoding="utf-8")
    page = ci_summary.render_embed(source, 2, "Requirement coverage, by change")
    assert page.startswith("<details><summary>Requirement coverage, by change</summary>")
    assert "### Requirement coverage" in page
    assert "#### Detail" in page
    assert not re.search(r"^## ", page, re.MULTILINE)
