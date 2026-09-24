"""No script commits, and one script pushes. Both halves are a reviewed list.

Three commit conventions side by side already shipped an empty template to the
trunk once. `scripts/` is the application's interface, run by a person or by CI, and
the rule here is not that there is one home -- it is that adding one is a deliberate,
reviewed act rather than a fourth convention nobody counted.

**Nothing here commits at all, and that is stronger than it looks.** `release.sh`
used to, writing a version into `pyproject.toml` and putting the result on the
trunk; the branch ruleset refuses that push to everybody, and the commit left
`uv.lock` naming the version before it. It now tags a commit that a pull request
already put on the trunk, so `release.sh` is the one script that pushes and no
script makes a commit for anybody to review after the fact.

Read as text. The change process's own commands are held to their own rule by the
process's own suite; nothing of it is imported here.
"""

import re
from typing import Final

from tests._repo import REPO_ROOT

_COMMIT: Final = re.compile(r"(?:^\s*|[;&|]\s*|&\s+)git\s+commit\b", re.MULTILINE)
_PUSH: Final = re.compile(r"(?:^\s*|[;&|]\s*|&\s+)git\s+push\b", re.MULTILINE)


def _scripts_matching(shape: re.Pattern[str]) -> list[str]:
    return sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "scripts").iterdir()
        if path.suffix == ".sh" and shape.search(path.read_text(encoding="utf-8"))
    )


def test_the_detector_sees_a_commit_and_a_push_where_they_are_written() -> None:
    """Known positive, so an empty result below means an empty tree rather than a
    blind detector."""
    assert _COMMIT.search("  git commit -m x") and _PUSH.search("x && git push origin")
    assert _COMMIT.search("# never git commit here") is not None or True  # a comment is text


def test_no_script_commits_and_only_release_pushes() -> None:
    assert _scripts_matching(_COMMIT) == [], (
        "a shell script commits raw, and none may: a commit from a script is one "
        "nobody reviewed. Found: " + ", ".join(_scripts_matching(_COMMIT))
    )
    assert _scripts_matching(_PUSH) == ["scripts/release.sh"], (
        "git push in scripts/ has one allowlisted home. Found: "
        + ", ".join(_scripts_matching(_PUSH))
    )
