"""audit.sh's three-state exit, proven per ecosystem on a stubbed tree in seconds.

`audit.sh` documents a 0/1/4 contract in its own `--help` -- 0: nothing at or above
the level; 1: an advisory that fails a section; 4 (INCOMPLETE): an ecosystem could not
be audited at all. `test_check_script.py` stubs `audit.sh` whole, because what it tests
is check.sh's aggregation, so audit.sh's own body has never been executed by anything
but a person.

The interesting branch is the one a person cannot casually reach: you arrive at the
failing path only on a day you actually have a vulnerability. It shipped broken. It
called a `fail` helper that `_lib.sh` did not define, so under `set -euo pipefail`
the script aborted on that line with 127 -- swallowing the two remediation lines
below it and its own FAILED banner, and returning a code its `--help` does not name.
Nothing caught it: `check.sh`'s `gate()` counts anything but 0 and 4 as a failure, so
the gate still went red and the only casualties were the exit code and the sentence
telling the operator what to do about it.

**Two ecosystems now, and the second is why this file grew.** The script used to read
`frontend/package-lock.json` and nothing else while reporting under an unqualified
name, so `uv.lock` went unaudited behind a green gate. The test that would have caught
it is `test_absent_uv_is_incomplete_never_a_pass` below: an ecosystem with no tool is a
NAMED GAP and never a pass, and that has to hold for each of them separately or the
rule only ever protected the one somebody remembered.

The stub is the one `test_check_script.py` established, inverted -- there the gates
were stubs and check.sh was real; here `audit.sh` is real and `npm` and `uv` are the
stubs. The scripts are copied into a tmp tree verbatim: `_lib.sh` derives `REPO_ROOT`
from its own file location and never from `$PWD`, so the copy re-roots itself for free.
PATH is narrowed to a directory holding the stubs and the few externals the script
needs, which is what keeps the machine's real npm and uv -- and their real opinion of
this repository's dependencies -- out of the result.

`infra-check.sh` is copied REAL rather than faked, because audit.sh reads the Terraform
root list out of it: a root added there grows this tree too, with nobody remembering
this file. The rest of the tree is the smallest thing each coverage line looks at.
"""

import pathlib
import re
import shutil
import stat
import subprocess

_REPO = pathlib.Path(__file__).resolve().parents[2]

#: An npm that always has something to report, and fails the level query or does
#: not. `audit.sh` calls npm twice: once bare, to print the report in full, and
#: once with `--audit-level` for the verdict. Only the second decides the branch.
_NPM_STUB = """#!/usr/bin/env bash
printf '%s\\n' "stub npm audit report -- 1 high severity vulnerability"
case "$*" in *--audit-level=*) exit {verdict} ;; esac
exit 0
"""

#: A uv that answers `uv audit --frozen` and nothing else. One call, one verdict --
#: `uv audit` has no severity threshold to query, which is the asymmetry with npm
#: that audit.sh's header names.
_UV_STUB = """#!/usr/bin/env bash
printf '%s\\n' "stub uv audit report -- 68 packages"
exit {verdict}
"""


#: One workflow with one step, pinned the way the repository pins. `extra_uses` appends
#: to it, which is how the known positive below plants a moving tag.
_PINNED_STEP = "      - uses: actions/checkout@" + "0" * 40 + " # v7\n"


def _plant(
    tmp_path: pathlib.Path,
    *,
    npm: str | None,
    uv: str | None = _UV_STUB.format(verdict=0),
    extra_uses: str = "",
) -> tuple[pathlib.Path, pathlib.Path]:
    """A tmp tree with a real audit.sh, and each tool present or absent as asked."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("audit.sh", "_lib.sh", "infra-check.sh"):
        shutil.copy2(_REPO / "scripts" / name, scripts / name)

    # The lockfiles are the trees audit.sh claims to read. Their contents never matter
    # here -- the stubs are what answer -- but their absence is a different branch
    # of the script (a NAMED GAP), and these tests are not that one.
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package-lock.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("version = 1\n", encoding="utf-8")

    # What the three coverage lines look at before they print their claim. Each is the
    # smallest input that satisfies the check, so a test failing here means audit.sh
    # started asking a new question rather than that this fixture went stale.
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.14-slim@sha256:" + "0" * 64 + "\n", encoding="utf-8"
    )
    github = tmp_path / ".github"
    (github / "workflows").mkdir(parents=True)
    (github / "dependabot.yml").write_text(
        "\n".join(
            f"  - package-ecosystem: {name}"
            for name in ("npm", "uv", "github-actions", "docker", "terraform")
        )
        + "\n",
        encoding="utf-8",
    )
    (github / "workflows" / "ci.yml").write_text(_PINNED_STEP + extra_uses, encoding="utf-8")
    for root in _terraform_roots():
        lock = tmp_path / "infra" / "terraform" / root / ".terraform.lock.hcl"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text('provider "registry.terraform.io/hashicorp/aws" {}\n', encoding="utf-8")

    path_dir = tmp_path / "bin"
    path_dir.mkdir()
    # Everything the run needs by name, and nothing else. `bash` because both the
    # interpreter lookup and the stubs' own `env bash` shebangs go through this PATH,
    # `dirname` because `_lib.sh` calls it at source time to find REPO_ROOT, and
    # `grep` because the coverage lines read the tree with it; all the rest is a bash
    # builtin or is a stub. Symlinked rather than assumed, so the narrowed PATH cannot
    # depend on where this machine keeps them.
    for tool in ("bash", "dirname", "grep"):
        found = shutil.which(tool)
        assert found is not None, f"{tool} is not on PATH"
        (path_dir / tool).symlink_to(found)

    for name, body in (("npm", npm), ("uv", uv)):
        if body is None:
            continue
        stub = path_dir / name
        stub.write_text(body, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return scripts / "audit.sh", path_dir


def _terraform_roots() -> list[str]:
    """The roots audit.sh will look for, read where audit.sh reads them."""
    text = (_REPO / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    match = re.search(r"^ROOTS=\((?P<roots>[^)]*)\)", text, flags=re.MULTILINE)
    assert match is not None, "scripts/infra-check.sh declares no ROOTS=( ... )"
    roots = match.group("roots").split()
    assert roots, "scripts/infra-check.sh declares an empty ROOTS"
    return roots


def _run(audit: pathlib.Path, path_dir: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(audit)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env={"PATH": str(path_dir), "NO_COLOR": "1"},
    )


def test_an_advisory_fails_the_gate_with_the_remediation_still_visible(
    tmp_path: pathlib.Path,
) -> None:
    """Exit 1, the FAILED banner, and the sentence saying what to do next.

    The regression this file exists for. A 127 here means the branch called
    something that is not defined, and everything printed below the verdict was lost.
    """
    completed = _run(*_plant(tmp_path, npm=_NPM_STUB.format(verdict=1)))

    assert completed.returncode == 1, (
        f"expected the documented 1, got {completed.returncode} "
        f"(127 means the branch called an undefined helper)\n{completed.stderr}"
    )
    assert "Dependency audit: FAILED" in completed.stderr
    assert "npm audit fix" in completed.stderr
    assert "EXEMPTIONS.md" in completed.stderr


def test_a_clean_audit_is_exit_zero(tmp_path: pathlib.Path) -> None:
    completed = _run(*_plant(tmp_path, npm=_NPM_STUB.format(verdict=0)))

    assert completed.returncode == 0, completed.stderr
    assert "Dependency audit: OK" in completed.stderr


def test_absent_npm_is_incomplete_never_a_pass(tmp_path: pathlib.Path) -> None:
    """The other half of the contract: a gate that could not run is not a green one."""
    completed = _run(*_plant(tmp_path, npm=None))

    assert completed.returncode == 4, completed.stderr
    assert "Dependency audit: INCOMPLETE" in completed.stderr
    assert "frontend (npm)" in completed.stderr


def test_absent_uv_is_incomplete_never_a_pass(tmp_path: pathlib.Path) -> None:
    """The same rule for the ecosystem that used not to exist here at all.

    This is the finding, stated as a test: before the widening, a repository with no
    Python audit whatsoever published a green "Dependency audit". A gap named for one
    ecosystem and not the other is the rule protecting whichever one somebody
    remembered.
    """
    completed = _run(*_plant(tmp_path, npm=_NPM_STUB.format(verdict=0), uv=None))

    assert completed.returncode == 4, completed.stderr
    assert "Dependency audit: INCOMPLETE" in completed.stderr
    assert "backend (Python)" in completed.stderr


def test_a_python_advisory_fails_the_gate_with_its_own_remediation(
    tmp_path: pathlib.Path,
) -> None:
    """npm's remediation is `npm audit fix`, and it is no use to a locked wheel."""
    completed = _run(
        *_plant(
            tmp_path,
            npm=_NPM_STUB.format(verdict=0),
            uv=_UV_STUB.format(verdict=1),
        )
    )

    assert completed.returncode == 1, completed.stderr
    assert "Dependency audit: FAILED" in completed.stderr
    assert "uv lock --upgrade-package" in completed.stderr


def test_a_real_advisory_outranks_a_named_gap(tmp_path: pathlib.Path) -> None:
    """A vulnerability found is the louder fact than a scanner not installed.

    `hygiene.sh` states the rule and this is the same one: a gap must not downgrade
    a failure to "incomplete", or a missing tool becomes a way to soften a red.
    """
    completed = _run(*_plant(tmp_path, npm=_NPM_STUB.format(verdict=1), uv=None))

    assert completed.returncode == 1, completed.stderr
    assert "Dependency audit: FAILED" in completed.stderr


def test_a_coverage_line_refuses_to_print_a_claim_that_has_stopped_being_true(
    tmp_path: pathlib.Path,
) -> None:
    """The known positive for the three sections that audit nothing.

    Those lines say "not scanned, but pinned -- and here is what pins it". A line
    that printed that without looking would be the very fault this script was
    repaired for, one level down: a statement wider than its measurement. So the
    script checks, and this proves the check convicts -- one moving tag in one
    workflow turns the GitHub Actions line from a claim into a failure.
    """
    completed = _run(
        *_plant(
            tmp_path,
            npm=_NPM_STUB.format(verdict=0),
            extra_uses="      - uses: some-org/some-action@v1\n",
        )
    )

    assert completed.returncode == 1, completed.stderr
    assert "a workflow step runs a moving tag" in completed.stderr
    assert "Dependency audit: FAILED" in completed.stderr


def test_the_two_references_that_may_move_do_not_convict_it(tmp_path: pathlib.Path) -> None:
    """The other side of the same rule, or the exemption would be decorative.

    `@main` on the process's own composite actions is a decision argued in `ci.yml`
    and declared in `tests/fitness/test_action_pins.py`. If this section convicted
    them the repository could not be green, and the pressure would be to delete the
    check rather than to keep the decision.
    """
    engine = "Scalo-Sales-Engineering-Consulting/claude-marketplace/.github/actions"
    completed = _run(
        *_plant(
            tmp_path,
            npm=_NPM_STUB.format(verdict=0),
            extra_uses=f"      - uses: {engine}/sdd-specs@main\n"
            f"      - uses: {engine}/sdd-tests@main\n",
        )
    )

    assert completed.returncode == 0, completed.stderr
    assert "Dependency audit: OK" in completed.stderr


def test_workflows_that_cannot_be_read_are_not_reported_as_pinned(tmp_path: pathlib.Path) -> None:
    """A failed read is not a clean tree (issue #61, audit ticket E3-03).

    The four-stage `grep | grep -v | grep -v | grep -qv` this section used to be sent
    an empty stream when the first `grep` could not read the workflows, and "nothing
    left after filtering" is what a fully pinned tree looks like -- so a read that
    failed printed the coverage claim. The producer's status is now read on its own.
    """
    audit, path_dir = _plant(tmp_path, npm=_NPM_STUB.format(verdict=0))
    (tmp_path / ".github" / "workflows" / "ci.yml").chmod(0)

    completed = _run(audit, path_dir)

    assert completed.returncode == 1, completed.stderr
    assert "could not be read, so no pin was checked" in completed.stderr
    assert "Dependency audit: FAILED" in completed.stderr
