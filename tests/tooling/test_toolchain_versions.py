"""One Python and one Node, in every home that names them.

The Dockerfile's two base images name the Python the application runs on and the
Node the SPA is built with. So do the CI env blocks, `.python-version`,
`pyproject.toml` (twice -- ruff's `target-version` is the SYNTAX floor and is held to
the hooks' oldest interpreter by `tests/fitness/test_hook_closure_syntax.py` instead),
the Lambda `runtime` in Terraform, the preflight's
constants, `scripts/_lib.sh`'s error message and the README's first-run sentence. The
constitution's Article XIII is deliberately not among them: it states a permitted floor,
not the pin.
Nothing held them to one value: Dependabot bumped the two images from 3.12 / 22 to
3.14 / 26 in September 2026 and every other home stayed where it was, so the test
suite ran on an interpreter production did not, and the README described a third.
`tests/tooling/test_container_pins.py` checks that a base image is pinned by digest
and that a tag stands beside it -- never what the tag says.

This test reads the value from every home and asks that they agree. The homes are
listed, and the workflows and Terraform roots are discovered, for the reason
`test_uv_pin.py` gives: a hand-kept list is the list missing the home that
mattered. A fact with this many homes is not a fact to restate here either -- the
test asserts equality, not a number.
"""

import json
import re
from collections.abc import Callable, Iterable
from typing import Final

from tests._repo import REPO_ROOT

#: Where the Python major.minor is written, and how each home writes it.
PYTHON_HOMES: Final[tuple[tuple[str, str], ...]] = (
    ("Dockerfile", r"^FROM python:(\d+\.\d+)-"),
    (".python-version", r"^(\d+\.\d+)\s*$"),
    ("pyproject.toml", r'^requires-python = ">=(\d+\.\d+)"'),
    ("pyproject.toml", r'^python_version = "(\d+\.\d+)"'),
    ("scripts/preflight.py", r"^MIN_PYTHON_VERSION = \((\d+), (\d+)\)"),
    ("scripts/preflight.sh", r"Install Python (\d+\.\d+):"),
    ("scripts/status.sh", r"Install Python (\d+\.\d+):"),
    ("scripts/package.sh", r'^LAMBDA_PYTHON="(\d+\.\d+)"'),
    ("README.md", r"\(Python (\d+\.\d+)\)"),
)

#: NOT a home. `spec/constitution.md` § Article XIII says "Python ≥ 3.12" and that is a
#: PERMITTED FLOOR rather than the pin -- 3.14 satisfies it, and narrowing it would be a
#: change to a CRITICAL article, which the constitution says needs an ADR that cannot exist
#: until the first change goes through `/sdd`. The pin lives in `pyproject.toml`.

#: Where the Node major is written.
NODE_HOMES: Final[tuple[tuple[str, str], ...]] = (
    ("Dockerfile", r"^FROM node:(\d+)-"),
    ("scripts/preflight.py", r"^NODE_MAJOR = (\d+)"),
    ("scripts/_lib.sh", r"Install Node (\d+) or newer"),
    ("README.md", r"\bNode (\d+)\b"),
)

#: How a workflow and a Terraform root write the same two facts.
WORKFLOW_PYTHON: Final = r'^\s*PYTHON_VERSION: "(\d+\.\d+)"'
WORKFLOW_NODE: Final = r'^\s*NODE_VERSION: "(\d+)"'
LAMBDA_RUNTIME: Final = r'^\s*runtime\s*=\s*"python(\d+\.\d+)"'

Reader = Callable[[str], str]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def _value(match: re.Match[str]) -> str:
    """`3.14` from any of the shapes above: `3.14`, `py314` (`3`, `14`), `(3, 14)`."""
    groups = [group for group in match.groups() if group is not None]
    return ".".join(groups) if len(groups) > 1 else groups[0]


def _collect(
    homes: Iterable[tuple[str, str]],
    discovered: Iterable[tuple[str, str]],
    read: Reader,
) -> dict[str, str]:
    """`{home: value}` for every listed home (which must match) and every discovered
    one (which may not name the fact at all -- a workflow with no Python step)."""
    found: dict[str, str] = {}
    for relative, pattern in homes:
        match = re.search(pattern, read(relative), flags=re.MULTILINE)
        assert match, f"{relative} no longer names the version where this test looks: {pattern}"
        found[f"{relative} ({pattern})"] = _value(match)
    for relative, pattern in discovered:
        for match in re.finditer(pattern, read(relative), flags=re.MULTILINE):
            found[f"{relative}:{match.start()}"] = _value(match)
    return found


def _workflows() -> list[str]:
    #: Every workflow here is this application's. The change process's own left with
    #: it in 2026-09; it pinned a different floor on purpose -- the process runs on
    #: whatever `python3` a machine has -- and an exclusion naming a file that is gone
    #: is an exemption nobody re-reads.
    paths = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    assert paths, "no workflows found; this test would then pass over nothing"
    return [path.relative_to(REPO_ROOT).as_posix() for path in paths]


def _terraform() -> list[str]:
    paths = sorted((REPO_ROOT / "infra").rglob("*.tf"))
    assert paths, "no Terraform found; this test would then pass over nothing"
    return [path.relative_to(REPO_ROOT).as_posix() for path in paths]


def _python_versions(read: Reader = _read) -> dict[str, str]:
    discovered = [(w, WORKFLOW_PYTHON) for w in _workflows()] + [
        (t, LAMBDA_RUNTIME) for t in _terraform()
    ]
    return _collect(PYTHON_HOMES, discovered, read)


def _node_versions(read: Reader = _read) -> dict[str, str]:
    return _collect(NODE_HOMES, [(w, WORKFLOW_NODE) for w in _workflows()], read)


def _disagreement(found: dict[str, str]) -> str | None:
    values = sorted(set(found.values()))
    if len(values) == 1:
        return None
    by_value = {value: sorted(home for home, v in found.items() if v == value) for value in values}
    return f"{by_value}"


def test_the_discovered_homes_are_not_empty() -> None:
    """Every workflow declares the Python it runs on and at least one Terraform root
    declares a Lambda runtime -- otherwise the discovery half has gone blind."""
    python = _python_versions()
    assert any(home.startswith(".github/") for home in python), "no workflow names PYTHON_VERSION"
    assert any(home.startswith("infra/") for home in python), "no Terraform names a runtime"
    assert any(home.startswith(".github/") for home in _node_versions()), (
        "no workflow names NODE_VERSION"
    )


def test_one_python_everywhere() -> None:
    """The image, the CI, the interpreter file, the linters, the Lambda and the
    preflight name the same Python -- or the suite proves nothing about production."""
    found = _python_versions()
    assert _disagreement(found) is None, (
        f"the homes of the Python version disagree: {_disagreement(found)}. Move them "
        "together -- a Python the tests never run on is a production nobody tested."
    )


def test_one_node_everywhere() -> None:
    """The image's build stage, the CI, the preflight and the two sentences that tell a
    newcomer what to install name the same Node major."""
    found = _node_versions()
    assert _disagreement(found) is None, (
        f"the homes of the Node major disagree: {_disagreement(found)}. The SPA that "
        "ships is built on the image's Node; CI and the newcomer should build on the same."
    )


def test_the_comparison_sees_one_home_drifting() -> None:
    """Known positive: a Dependabot bump of the image alone must be reported."""
    real = _read
    drifted = {
        "Dockerfile": real("Dockerfile").replace("FROM python:", "FROM python:9.99-slim-", 1)
    }

    def read(relative: str) -> str:
        return drifted.get(relative, real(relative))

    found = _python_versions(read)
    assert _disagreement(found) is not None
    assert "Dockerfile" in (_disagreement(found) or "")


# --------------------------------------------------------------------------- #
# The constitution's Allowed list, against the manifests
#
# Article XIII is CRITICAL and names versions. Two kinds of number live in one
# sentence and they are read differently: "Python >= 3.12" is a permitted FLOOR,
# which `>=3.14` satisfies, while "React 19" is an exact major, which React 18
# would not. Nothing read either against a manifest, and the article said React 18
# for as long as React 19 had been installed -- a CRITICAL article, wrong, with no
# mechanism that could notice.
# --------------------------------------------------------------------------- #

_CONSTITUTION: Final = "spec/constitution.md"
_PACKAGE_JSON: Final = "frontend/package.json"

#: The label in the Allowed list, the version it names, and the npm package that
#: has to satisfy it. An exact prefix: "React 19" is satisfied by 19.2.8 and not by
#: 18.3.1, and "TypeScript 5.9" not by 5.8.
_ALLOWED_PINS: Final[tuple[tuple[str, str, str], ...]] = (
    ("React", r"\bReact (\d+)\b", "react"),
    ("TypeScript", r"\bTypeScript (\d+\.\d+)\b", "typescript"),
    ("Tailwind", r"\bTailwind (\d+)\b", "tailwindcss"),
)

#: Packages whose major must equal React's, because they ARE React. A `@types/react`
#: one major behind types the wrong library and reports nothing.
_REACT_FAMILY: Final[tuple[str, ...]] = ("react", "react-dom", "@types/react", "@types/react-dom")


def _article_xiii() -> str:
    """The Allowed and Forbidden article, sliced off at the next heading."""
    text = _read(_CONSTITUTION)
    _, sep, below = text.partition("## Article XIII")
    assert sep, f"{_CONSTITUTION} no longer has an Article XIII -- update this parser with it"
    end = below.find("\n## ")
    return below if end == -1 else below[:end]


def _installed(package: str) -> str:
    """The version `frontend/package.json` asks for, with its range operator dropped."""
    manifest = json.loads(_read(_PACKAGE_JSON))
    for section in ("dependencies", "devDependencies"):
        if package in manifest.get(section, {}):
            return str(manifest[section][package]).lstrip("^~>=< ")
    raise AssertionError(f"{_PACKAGE_JSON} declares no `{package}` in either dependency section")


def test_the_article_is_where_this_test_thinks_it_is() -> None:
    """The known positive. An article that moved would otherwise pass every rule below."""
    article = _article_xiii()
    assert "**Allowed.**" in article, (
        f"the Allowed list is no longer inside Article XIII of {_CONSTITUTION}; every version "
        "assertion below is reading the wrong slice of the file"
    )
    for label, pattern, _package in _ALLOWED_PINS:
        assert re.search(pattern, article), (
            f"Article XIII no longer names a version for {label}. Either it stopped pinning one "
            f"-- which is a change to a CRITICAL article -- or the shape changed and this "
            "pattern must move with it."
        )


def test_every_version_the_constitution_allows_is_the_one_installed() -> None:
    """The article is the policy and the manifest is the fact; they are one number.

    Article XIII said React 18 while `package.json` had asked for `^19.2.8` since
    the SPA was written. A CRITICAL article nothing reads is a comment.
    """
    article = _article_xiii()
    wrong = []
    for label, pattern, package in _ALLOWED_PINS:
        match = re.search(pattern, article)
        assert match, label  # the test above owns this failure
        declared = match.group(1)
        installed = _installed(package)
        if installed != declared and not installed.startswith(f"{declared}."):
            wrong.append(f"{label}: the constitution allows {declared}, {package} is {installed}")
    assert not wrong, (
        "Article XIII and frontend/package.json name different versions, and the article is "
        f"the one people quote: {wrong}. Changing the article is a change to a CRITICAL "
        "article; changing the dependency is an upgrade. Either is fine and neither is silent."
    )


def test_the_react_packages_share_one_major() -> None:
    """One library, four manifest entries, and the types are the half that drifts."""
    majors = {package: _installed(package).split(".")[0] for package in _REACT_FAMILY}
    assert len(set(majors.values())) == 1, (
        f"the React packages are on different majors: {majors}. `@types/react` a major behind "
        "`react` describes a library nobody is running, and it reports no error for doing so."
    )


def test_the_constitution_states_a_python_floor_the_pin_satisfies() -> None:
    """The other reading, kept apart from the one above on purpose.

    "Python >= 3.12" is a permitted floor and `requires-python = ">=3.14"` satisfies
    it. Narrowing the article to the pin would be a change to a CRITICAL article,
    so what is asserted is the relation, not equality -- see the note beside
    PYTHON_HOMES.
    """
    article = _article_xiii()
    allowed = re.search(r"Python\s*≥\s*(\d+)\.(\d+)", article)
    assert allowed, f"Article XIII no longer states a Python floor in {_CONSTITUTION}"
    pinned = re.search(r'^requires-python = ">=(\d+)\.(\d+)"', _read("pyproject.toml"), re.M)
    assert pinned, "pyproject.toml no longer states `requires-python` in the expected shape"

    floor = (int(allowed.group(1)), int(allowed.group(2)))
    pin = (int(pinned.group(1)), int(pinned.group(2)))
    assert pin >= floor, (
        f"pyproject.toml pins Python {pin[0]}.{pin[1]}, below the {floor[0]}.{floor[1]} floor "
        "Article XIII allows. The pin may be above the floor and never below it."
    )
