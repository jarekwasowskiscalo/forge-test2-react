"""What `release.sh` writes to stdout is a git ref that production is checked out at.

`.github/workflows/release.yml` reads the last line and hands it to the deploy job
as `ref:`. So the value of this contract is not tidiness -- a wrong last line is a
production deployment of the wrong commit, or of nothing.

It was wrong. `summary()` in `scripts/_lib.sh` prints its banner to **stdout**, so
the last line was `Release v0.1.0: OK` with ANSI colour codes around it, and
`checkout` would have been handed that. The banner is gone for the same reason
`infra.sh output` has none: when stdout is the result, a report after it is the
thing that gets parsed.

**The push path used to be tested by nothing.** Every call in this file was
`--no-push` or `--dry-run`, so the branch that publishes a release -- the only part
of it that is awkward to take back -- ran zero times here. The fixture now builds a
bare repository as `origin`, which is what lets a real `git push` happen and be
asserted on.

The tree is a real git repository built from scratch rather than a clone of this
one, because every refusal below is about the state of a working tree and this one's
state is whatever the developer left. Two commands are stubbed onto PATH: `uv`,
because `release.sh` calls it to reach `scripts/release_version.py` (which imports
nothing outside the standard library) and to check the lockfile, and `gh`, because
it asks GitHub whether `CI passed` is green. Each stub reads a file beside the tree,
so a test states the answer it wants rather than the fixture deciding for all of
them -- beside rather than inside, because stating an answer must not dirty the
working tree a release refuses to be cut from.
"""

import pathlib
import shutil
import subprocess
import sys

import pytest

from tests._repo import REPO_ROOT

PYPROJECT = """\
[project]
name = "planted"
version = "0.0.0"
"""

#: What the `gh` stub reports for the `CI passed` check run, unless a test says
#: otherwise. The string is the `status/conclusion` pair `release.sh` demands.
GREEN = "completed/success"


def _git(tree: pathlib.Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(tree), *arguments], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _says(tree: pathlib.Path, name: str, answer: str) -> None:
    """Tell a stub what to answer. `release.sh` never sees these files."""
    (tree.parent / "answers" / name).write_text(answer, encoding="utf-8")


@pytest.fixture
def tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """A repository with a bare `origin`, one pushed commit, and the two stubs."""
    work = tmp_path / "work"
    work.mkdir()
    scripts = work / "scripts"
    scripts.mkdir()
    for name in ("release.sh", "_lib.sh", "release_version.py"):
        shutil.copy2(REPO_ROOT / "scripts" / name, scripts / name)
    (work / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")

    # What the stubs read, and deliberately OUTSIDE the repository: a test that
    # states its answer by writing a file would otherwise dirty the working tree,
    # and a dirty tree is one of the things being tested for.
    answers = tmp_path / "answers"
    answers.mkdir()

    stub = tmp_path / "bin"
    stub.mkdir()

    # `uv run python X` -> `python X`, and `uv lock --check` -> whatever the test
    # asked for. The previous version was `shift 2; exec python "$@"`, which
    # assumed the only invocation was ever `uv run`.
    uv = stub / "uv"
    uv.write_text(
        "#!/usr/bin/env bash\n"
        'case "$1" in\n'
        f'    lock) exit "$(cat {answers / "uv-lock"})" ;;\n'
        '    run) shift 2; exec "' + sys.executable + '" "$@" ;;\n'
        '    *) echo "stub uv: unexpected $*" >&2; exit 64 ;;\n'
        "esac\n"
    )
    uv.chmod(0o755)

    # One call: `gh api .../check-runs --jq ...`. The stub answers with the string
    # that jq expression would have produced, which is what `release.sh` compares.
    gh = stub / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        f'exit_code="$(cat {answers / "gh-exit"})"\n'
        '[ "$exit_code" = 0 ] || exit "$exit_code"\n'
        f"cat {answers / 'gh-verdict'}\n"
    )
    gh.chmod(0o755)

    _says(work, "uv-lock", "0")
    _says(work, "gh-exit", "0")
    _says(work, "gh-verdict", GREEN)

    _git(work, "init", "-b", "main")
    _git(work, "config", "user.email", "planted@example.invalid")
    _git(work, "config", "user.name", "Planted")
    _git(work, "add", ".")
    _git(work, "commit", "-m", "first")

    # The trunk as a server would have it. `release.sh` fetches this and refuses a
    # HEAD that is not exactly what it finds, so without it nothing on the push
    # path can be exercised at all.
    origin = tmp_path / "origin.git"
    _git(work, "init", "--bare", str(origin))
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "--quiet", "origin", "main")
    return work


def _release(tree: pathlib.Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(tree / "scripts" / "release.sh"), *arguments],
        capture_output=True,
        text=True,
        timeout=120,
        env={"PATH": f"{tree.parent / 'bin'}:/usr/bin:/bin", "HOME": str(tree)},
    )


def _origin(tree: pathlib.Path) -> pathlib.Path:
    return tree.parent / "origin.git"


def _remote_refs(tree: pathlib.Path) -> list[str]:
    """Every ref the bare origin carries, so "nothing was published" is assertable.

    `HEAD` is dropped because it is a symbolic name for one of the others, and the
    peeled `refs/tags/x^{}` rows because an annotated tag is one ref that
    `ls-remote` prints twice.
    """
    listing = _git(tree, "ls-remote", str(_origin(tree)))
    names = (line.split("\t")[1] for line in listing.splitlines() if line)
    return sorted(n for n in names if n.startswith("refs/") and not n.endswith("^{}"))


def _remote_sha(tree: pathlib.Path, ref: str) -> str:
    """What the bare origin has at `ref` -- the server's state, not this checkout's."""
    listing = _git(tree, "ls-remote", str(_origin(tree)), ref)
    return listing.split("\t")[0] if listing else ""


def test_the_last_line_of_stdout_is_the_version_and_nothing_else(
    tree: pathlib.Path,
) -> None:
    """The contract `release.yml` depends on, asserted at the character.

    No banner, no colour codes, no trailing report -- `checkout` is given this
    string verbatim, and a git ref with an escape sequence in it resolves to
    nothing at all.
    """
    result = _release(tree, "minor", "--no-push")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "v0.1.0"
    assert "\033" not in result.stdout.splitlines()[-1]


def test_a_dry_run_says_the_version_and_changes_nothing(tree: pathlib.Path) -> None:
    """So the answer to "what would this release be called" costs nothing to ask."""
    before = _git(tree, "rev-parse", "HEAD")

    result = _release(tree, "major", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "v1.0.0"
    assert _git(tree, "rev-parse", "HEAD") == before
    assert _git(tree, "tag") == ""
    assert _remote_refs(tree) == ["refs/heads/main"]


def test_it_tags_the_head_it_was_given(tree: pathlib.Path) -> None:
    """The tag names HEAD itself, which is the whole of the arrangement.

    There is no release commit to point at any more: the thing being tagged is the
    commit a pull request already put on the trunk.
    """
    head = _git(tree, "rev-parse", "HEAD")

    assert _release(tree, "patch", "--no-push").returncode == 0

    assert _git(tree, "tag") == "v0.0.1"
    assert _git(tree, "rev-parse", "v0.0.1^{commit}") == head


def test_a_release_writes_no_version_and_makes_no_commit(tree: pathlib.Path) -> None:
    """A02, asserted at its source rather than at the symptom.

    The release used to write `pyproject.toml` and commit it without `uv.lock`,
    which left every released commit failing `uv sync --locked`. A release that
    creates no commit cannot desynchronise the two, and the cheapest proof of that
    is that the commit being tagged is byte-for-byte the one that was already
    there.
    """
    before = _git(tree, "rev-parse", "HEAD")
    manifest = (tree / "pyproject.toml").read_bytes()

    assert _release(tree, "minor", "--no-push").returncode == 0

    assert _git(tree, "rev-parse", "HEAD") == before
    assert _git(tree, "status", "--porcelain") == ""
    assert (tree / "pyproject.toml").read_bytes() == manifest


def test_the_push_touches_exactly_one_ref(tree: pathlib.Path) -> None:
    """The tag, and nothing else -- the branch ruleset refuses everything else.

    `--follow-tags` used to push the trunk and the tag together and claim in a
    comment that this was one transaction. It is not one (`--atomic` appears
    nowhere), and the trunk half could never have landed: the ruleset covers
    `~DEFAULT_BRANCH` with an empty bypass list. One ref cannot be half pushed.
    """
    trunk_before = _remote_sha(tree, "refs/heads/main")

    result = _release(tree, "minor")

    assert result.returncode == 0, result.stderr
    assert _remote_refs(tree) == ["refs/heads/main", "refs/tags/v0.1.0"]
    assert _remote_sha(tree, "refs/heads/main") == trunk_before


def test_the_arithmetic_walks_from_the_last_tag(tree: pathlib.Path) -> None:
    """Two releases in a row: the second starts from the first, not from zero.

    Worth re-proving under the arrangement that makes no commit, because both tags
    now land on the SAME commit -- which is exactly the case `git describe` had no
    defined tie-break for, and why the lookup sorts by version instead.
    """
    assert _release(tree, "minor", "--no-push").returncode == 0
    assert _release(tree, "patch", "--no-push").returncode == 0

    assert set(_git(tree, "tag").split()) == {"v0.1.0", "v0.1.1"}
    assert _git(tree, "rev-parse", "v0.1.0^{commit}") == _git(tree, "rev-parse", "v0.1.1^{commit}")


def test_a_dirty_tree_is_refused(tree: pathlib.Path) -> None:
    """A tag has to name a commit that exists, not one plus what was lying around."""
    (tree / "pyproject.toml").write_text(PYPROJECT + "\n# edited\n", encoding="utf-8")

    result = _release(tree, "patch", "--no-push")

    assert result.returncode != 0
    assert "working tree" in result.stderr
    assert _git(tree, "tag") == ""


def test_a_release_off_the_trunk_is_refused(tree: pathlib.Path) -> None:
    """Everything a release contains has to have been reviewed on the way in."""
    _git(tree, "checkout", "-b", "feature")

    result = _release(tree, "patch", "--no-push")

    assert result.returncode != 0
    assert "trunk" in result.stderr


def test_a_tag_that_already_exists_but_is_not_reachable_is_refused(
    tree: pathlib.Path,
) -> None:
    """A tag is not moved. Two releases pointing at one name is worse than a gap.

    The scenario has to be a tag the lookup cannot see, because a tag it CAN see is
    simply the base the next version is computed from -- which is the ordinary case
    and works. What is left is a release cut on a branch that was then abandoned or
    rebased away: the tag survives, is unreachable from the trunk, and the
    arithmetic walks straight into it.
    """
    _git(tree, "checkout", "-b", "abandoned")
    (tree / "left-behind").write_text("x", encoding="utf-8")
    _git(tree, "add", ".")
    _git(tree, "commit", "-m", "a release that never landed")
    _git(tree, "tag", "-a", "v0.1.0", "-m", "left behind")
    _git(tree, "checkout", "main")

    result = _release(tree, "minor", "--no-push")

    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert _git(tree, "rev-parse", "v0.1.0^{commit}") != _git(tree, "rev-parse", "HEAD"), (
        "the tag was moved onto the trunk, which is the thing being refused"
    )


def test_a_head_the_trunk_does_not_carry_is_refused(tree: pathlib.Path) -> None:
    """A commit that is only here has been through no pull request and no ruleset.

    The whole arrangement rests on the tagged commit having been reviewed onto the
    trunk. A local commit looks identical to a merged one from inside the checkout,
    so the trunk is read from the remote rather than believed.
    """
    (tree / "unreviewed").write_text("x", encoding="utf-8")
    _git(tree, "add", ".")
    _git(tree, "commit", "-m", "never opened a pull request")

    result = _release(tree, "patch")

    assert result.returncode != 0
    assert "origin/main" in result.stderr
    assert _git(tree, "tag") == "", "a refused release left a tag behind to clean up"
    assert _remote_refs(tree) == ["refs/heads/main"]


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [
        ("completed/failure", "completed/failure"),
        ("in_progress/null", "in_progress/null"),
        ("absent", "absent"),
    ],
)
def test_a_commit_without_a_green_verdict_is_refused(
    tree: pathlib.Path, verdict: str, expected: str
) -> None:
    """A release cut from a red trunk deploys a red trunk.

    Three ways of not being green, and the one that matters most is the last: a
    commit with no `CI passed` at all reads as "no bad news" to anybody skimming,
    which is how an unchecked commit gets released.
    """
    _says(tree, "gh-verdict", verdict)

    result = _release(tree, "patch")

    assert result.returncode != 0
    assert expected in result.stderr
    assert _git(tree, "tag") == ""
    assert _remote_refs(tree) == ["refs/heads/main"]


def test_a_drifted_lockfile_is_refused(tree: pathlib.Path) -> None:
    """A release has to be reproducible from the commit it names.

    This is the gate that A02 never had. The drift it catches can no longer be
    caused by `release.sh` itself -- nothing writes `pyproject.toml` any more -- but
    a commit whose lockfile is stale is not one to tag, and the first thing that
    used to notice ran after the tag and the release page were published.
    """
    _says(tree, "uv-lock", "1")

    result = _release(tree, "patch")

    assert result.returncode != 0
    assert "uv.lock" in result.stderr
    assert _git(tree, "tag") == ""
    assert _remote_refs(tree) == ["refs/heads/main"]


def test_nothing_is_asked_of_the_network_without_a_push(tree: pathlib.Path) -> None:
    """`--no-push` publishes nothing, so it needs no `gh` and no remote.

    The three refusals above guard publication. Making them unconditional would
    cost a person the ability to ask what a release would be called, or to cut a
    local tag, from somewhere with no network and no GitHub login.
    """
    _says(tree, "gh-exit", "1")
    _says(tree, "gh-verdict", "completed/failure")

    assert _release(tree, "patch", "--no-push").returncode == 0
    assert _release(tree, "minor", "--dry-run").returncode == 0
    assert _git(tree, "tag") == "v0.0.1"
    assert _remote_refs(tree) == ["refs/heads/main"]
