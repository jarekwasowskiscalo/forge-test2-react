"""This template keeps the script contract's mechanical half -- checked, not claimed.

The change process calls this template's scripts by the names `.specconf/stack.json`
declares (the process's `script-contract.md`) and trusts each to do its job. Three of the
things it takes on trust are cheap to prove here, from the template's own files, without
importing the process:

- `check.sh` still files exit 4 as a named gap rather than a failure. The gate scores
  that code as INCOMPLETE; if the script stopped telling the three states apart, the
  gate would be pinned to a rule nothing follows any more.
- `check.sh` leaves every junit it is responsible for where the profile says it does, and
  every script the profile names is committed executable. A script that runs only on the
  machine it was chmodded on is a contract entry that holds on one laptop.
- The two pytest suites, `backend` and `fitness`, are disjoint and together cover every
  group under `tests/`. The engine attributes a case to ONE suite, so a case both collect
  is attributed to whichever junit was read last -- and a group neither collects is a
  group whose red nobody reads.
- The profile's recorded answer about `allowed_skips` still has its premise. That answer
  is a comment -- `.specconf/stack.json` § `suites` -- and a comment goes stale at the
  first skip somebody adds or removes. Which suites skip is measurable from this
  repository's own sources, so it is measured here rather than believed.

Reads the scripts and the profile as text. No Docker, no database.
"""

import ast
import functools
import json
import pathlib
import re
import subprocess
from typing import Final

import pytest

from tests._repo import REPO_ROOT

CHECK_SH: Final[pathlib.Path] = REPO_ROOT / "scripts" / "check.sh"
TEST_SH: Final[pathlib.Path] = REPO_ROOT / "scripts" / "test.sh"
PROFILE: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "stack.json"

#: `    4) incomplete+=("$label") ;;` -> the code check.sh files as a named gap.
_CHECK_SH_CASE: Final = re.compile(r"^\s*(?P<code>\d+)\)\s*(?P<action>\w+)", re.MULTILINE)


def _profile() -> dict[str, object]:
    loaded = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _check_sh_gate_dispatch() -> dict[str, str]:
    """`{exit code -> what check.sh does with it}` from its own `gate()` function."""
    text = CHECK_SH.read_text(encoding="utf-8")
    match = re.search(r"gate\(\) \{\n(?P<body>.*?)\n\}", text, re.DOTALL)
    assert match is not None, (
        "check.sh no longer has a `gate()` function with a case block. That function is "
        "where the three states are named; if it moved, this reading has to move with it."
    )
    return {
        m.group("code"): m.group("action") for m in _CHECK_SH_CASE.finditer(match.group("body"))
    }


def test_check_sh_still_files_exit_4_as_a_gap_rather_than_a_failure() -> None:
    dispatch = _check_sh_gate_dispatch()
    assert dispatch.get("0") == "ok", dispatch
    assert dispatch.get("4") == "incomplete", (
        "check.sh no longer files exit 4 as `incomplete`. Either the three-state contract "
        f"changed deliberately -- and the process's gate must change with it -- or this broke: "
        f"{dispatch}"
    )


def test_check_leaves_every_flagged_junit_where_the_profile_says() -> None:
    """`check` runs every suite and leaves each junit at the profile's path -- the contract
    obligation that lets a stage boundary read test-level evidence off one run.

    Only the suites handed `--junitxml` are asked about here: a suite with
    `junit_flag: false` names its path inside its own runner configuration, and the
    profile's comment says where."""
    text = CHECK_SH.read_text(encoding="utf-8")
    flagged = {
        name: body for name, body in _declared_suites().items() if body.get("junit_flag", True)
    }
    assert {"backend", "fitness"} <= set(flagged), sorted(flagged)
    for name, body in flagged.items():
        assert f"--junitxml={body['junit']}" in text, (
            f"check.sh does not write the {name} junit to {body['junit']}; the process "
            "reads that path after `check` and would file the suite as having proved nothing"
        )


#: The groups under `tests/`, each a directory with a `test_*.py` in it.
def _test_groups() -> set[str]:
    return {
        f"tests/{path.name}"
        for path in (REPO_ROOT / "tests").iterdir()
        if path.is_dir() and any(path.glob("test_*.py"))
    }


def test_the_pytest_suites_split_tests_into_disjoint_halves() -> None:
    """`backend` and `fitness` re-run a case by the targets their `isolate` names, and the
    engine attributes a case to one suite. Overlapping targets make a fitness case
    `backend`'s too; missing targets make a group nobody can re-run alone."""
    targets: dict[str, list[str]] = {}
    for name in ("backend", "fitness"):
        isolate = _declared_suites()[name]["isolate"]
        assert isinstance(isolate, dict)
        declared = isolate["targets"]
        assert isinstance(declared, list)
        targets[name] = [str(target) for target in declared]
    backend, fitness = set(targets["backend"]), set(targets["fitness"])
    assert fitness == {"tests/fitness"}, targets
    assert not backend & fitness, targets
    assert backend | fitness == _test_groups(), (
        f"the groups under tests/ are {sorted(_test_groups())} and the two suites' isolate "
        f"targets are {targets}. A new group goes to exactly one of them"
    )


def test_test_sh_keeps_the_backend_forms_off_tests_fitness() -> None:
    """The half the targets cannot say: what `test.sh backend` and `test.sh --no-db` run.

    Both arms pass `--ignore=tests/fitness` and the `fitness` arm runs that tree, so the
    two junits the profile names are two disjoint sets of cases."""
    text = TEST_SH.read_text(encoding="utf-8")
    arms = {
        match.group("arm"): match.group("body")
        for match in re.finditer(
            r"^\s{4}(?P<arm>backend|--no-db|fitness)\)\s*(?P<body>[^\n]*;;)$",
            text,
            re.MULTILINE,
        )
    }
    assert set(arms) == {"backend", "--no-db", "fitness"}, (
        f"test.sh's dispatch no longer has the three arms this reads: {sorted(arms)}"
    )
    for arm in ("backend", "--no-db"):
        assert "--ignore=tests/fitness" in arms[arm], (
            f"`test.sh {arm}` collects tests/fitness again, so every fitness case is in two "
            f"junits: {arms[arm]}"
        )
    assert "run_fitness" in arms["fitness"], arms
    runner = re.search(r"^run_fitness\(\) \{(?P<body>[^\n]*)\}$", text, re.MULTILINE)
    assert runner is not None, "test.sh no longer defines run_fitness() on one line"
    assert "tests/fitness" in runner.group("body"), runner.group("body")
    assert "--ignore" not in runner.group("body"), runner.group("body")


@functools.cache
def _committed_modes() -> dict[str, str]:
    """`scripts/x.sh` -> the mode git recorded. The executable bit lives in the index,
    which is what a checkout is made from; a filesystem mounted `noexec` reports
    something the commit never said. Empty when git cannot answer."""
    completed = subprocess.run(
        ["git", "ls-files", "-s", "--", "scripts"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    modes: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        fields, _, path = line.partition("\t")
        modes[path] = fields.split()[0]
    return modes


def test_the_committed_mode_reader_tells_the_two_modes_apart() -> None:
    modes = _committed_modes()
    if not modes:
        pytest.skip("no git checkout here -- the committed mode cannot be read")
    assert modes["scripts/check.sh"] == "100755"
    assert modes["scripts/app_status.py"] == "100644", (
        "a bare Python helper is run by `uv run`, never by its bit"
    )


def test_every_contract_script_the_profile_names_is_committed_executable() -> None:
    scripts = _profile()["scripts"]
    assert isinstance(scripts, dict)
    modes = _committed_modes()
    for entry, path in scripts.items():
        if str(entry).startswith("$"):
            continue
        assert isinstance(path, str)
        assert (REPO_ROOT / path).is_file(), f"{entry}: {path} is missing"
        mode = modes.get(path)
        if mode is not None:
            assert mode == "100755", (
                f"{entry}: {path} is committed as {mode}, not 100755 -- "
                "`git update-index --chmod=+x` it, or it runs only where it was written"
            )
        else:
            assert (REPO_ROOT / path).stat().st_mode & 0o111, f"{entry}: {path} is not executable"


# --------------------------------------------------------------------------------------
# The recorded answer about `allowed_skips`, and the premise it rests on.
#
# The key is optional and this profile declares it nowhere, which `.specconf/stack.json`
# § `suites` states as an answer rather than leaving as a silence. The answer is a
# measurement -- which suites skip, and which skip nothing -- and a measurement written
# into a comment is true until somebody edits a test. These three assertions are what turn
# it back into a question when that happens.
# --------------------------------------------------------------------------------------

#: Where each suite of `.specconf/stack.json` § `suites` keeps the sources that could
#: carry a skip. Declared here rather than read out of `scripts/test.sh`, for the reason
#: `test_test_layout.py` declares `WITHOUT_DATABASE`: the script dispatches `backend` to
#: pytest with no path at all (`pyproject.toml` names the testpath) and `frontend` to
#: vitest through its own config, so there is no one expression in it to read. The map is
#: held against the profile below, so a suite added there fails here until somebody says
#: where it lives.
SUITE_SOURCES: Final[dict[str, tuple[str, ...]]] = {
    "backend": ("tests/unit", "tests/integration", "tests/tooling"),
    "fitness": ("tests/fitness",),
    "frontend": ("frontend/src",),
    "e2e": ("e2e",),
}

#: The suites the recorded answer says DO skip cases. Both halves are asserted -- that
#: these still skip, and that the others still do not -- because the answer turns on the
#: difference: a suite that skips nothing has nothing to declare, and a suite that skips
#: for reasons its declaration would not name cannot afford to declare at all. `fitness`
#: is here for the second reason: its skips fire only off a git checkout or over a
#: revision with no upgrade(), which is a condition, not a kind a declaration names.
RECORDED_AS_SKIPPING: Final[frozenset[str]] = frozenset({"backend", "fitness"})

#: `pytest.skip(...)`, `@pytest.mark.skip`, `@pytest.mark.skipif` -- spelled as dotted
#: names, because they are looked for in the syntax tree and not in the text. A `skipif`
#: NAMED in a docstring (`tests/tooling/test_preflight.py`, `e2e/suite/conftest.py`) is
#: then not a false positive, and a grep for the same thing would have two.
_PYTHON_SKIPS: Final[frozenset[str]] = frozenset(
    {"pytest.skip", "pytest.mark.skip", "pytest.mark.skipif"}
)

#: vitest's spellings of the same thing, on any of the functions that declare a case.
_TS_SKIP: Final = re.compile(r"\b(?:it|test|describe|suite|bench)\.(?:skip|todo|skipIf)\b")

#: `//` to the end of the line, and `/* ... */` across them. Removed before the search
#: above -- the same rule as the Python half, one syntax down -- and replaced by the
#: newlines it spanned, so the line a match reports is still the line in the file.
_TS_COMMENT: Final = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)


def _dotted(node: ast.expr) -> str:
    """`pytest.mark.skipif` for that attribute chain, and `""` for anything else."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return ""
    parts.append(node.id)
    return ".".join(reversed(parts))


def _skips_in(name: str) -> list[str]:
    """Every skip in the sources of one declared suite, over all of its trees."""
    return sorted(skip for tree in SUITE_SOURCES[name] for skip in _skips_under(REPO_ROOT / tree))


def _skips_under(root: pathlib.Path) -> list[str]:
    """Every `<path>:<line>` under `root` that takes a case out of a run.

    Both languages, because a suite's sources are whatever that suite runs: the backend's
    and the black box's are Python, the frontend's are TypeScript, and asking the wrong
    question of a tree simply finds nothing there.
    """
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found += [
            f"{path.relative_to(REPO_ROOT)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and _dotted(node) in _PYTHON_SKIPS
        ]
    for path in sorted([*root.rglob("*.ts"), *root.rglob("*.tsx")]):
        source = _TS_COMMENT.sub(
            lambda match: "\n" * match.group(0).count("\n"),
            path.read_text(encoding="utf-8"),
        )
        found += [
            f"{path.relative_to(REPO_ROOT)}:{number}"
            for number, line in enumerate(source.splitlines(), start=1)
            if _TS_SKIP.search(line)
        ]
    return sorted(found)


def _declared_suites() -> dict[str, dict[str, object]]:
    """`{name -> body}` for every suite the profile declares, `$comment` dropped."""
    suites = _profile()["suites"]
    assert isinstance(suites, dict)
    out: dict[str, dict[str, object]] = {}
    for name, body in suites.items():
        if str(name).startswith("$"):
            continue
        assert isinstance(body, dict)
        out[str(name)] = body
    return out


def test_every_declared_suite_says_where_its_sources_are() -> None:
    """A suite nobody mapped is a suite the two tests below never ask about, and the
    recorded answer would go on claiming to cover it."""
    declared = set(_declared_suites())
    assert declared == set(SUITE_SOURCES), (
        f"the profile declares {sorted(declared)} and this module maps "
        f"{sorted(SUITE_SOURCES)}. Map the new suite to the tree its cases live in, then "
        "measure whether it skips and say so in .specconf/stack.json § `suites`"
    )


def test_a_suite_that_declares_allowed_skips_has_something_to_skip() -> None:
    """`allowed_skips` names cases that legitimately do not run. Declared for a suite whose
    sources cannot skip, it names nothing and only changes how a blackout reads -- which is
    the one thing the key does that nobody asked it for."""
    for name, body in _declared_suites().items():
        reasons = body.get("allowed_skips")
        if reasons is None:
            continue
        assert _skips_in(name), (
            f"suites.{name} declares allowed_skips {reasons} and nothing under "
            f"{', '.join(SUITE_SOURCES[name])} skips. Remove the declaration, or say which case it "
            "is for"
        )


def test_the_suites_recorded_as_skipping_still_skip() -> None:
    """The half of the answer that says `backend` must not declare.

    It rests on the suite skipping cases no declaration of its would name -- the corpus
    parametrisation and the logging sink -- so that a declaration would file every green
    run incomplete. Take those away and the suite could afford the key after all, which is
    a decision to re-make rather than a test to delete.
    """
    for name in sorted(RECORDED_AS_SKIPPING):
        assert _skips_in(name), (
            f"nothing under {', '.join(SUITE_SOURCES[name])} skips any more, and "
            ".specconf/stack.json § `suites` rests on the opposite. Re-measure: a suite "
            f"that skips only what a declaration would name can spend allowed_skips, and "
            f"suites.{name} was kept from it for exactly that reason"
        )


def test_the_suites_recorded_as_skipping_nothing_still_skip_nothing() -> None:
    """The other half: `frontend` and `e2e` have nothing to declare because they skip
    nothing at all. The first skip added to either makes that sentence false."""
    for name in sorted(set(SUITE_SOURCES) - RECORDED_AS_SKIPPING):
        found = _skips_in(name)
        assert not found, (
            f".specconf/stack.json § `suites` records {name} as skipping nothing, and it "
            f"now skips at: {', '.join(found)}. Either the skip is wrong, or the recorded "
            "answer is -- and the answer decides whether this suite declares allowed_skips"
        )
