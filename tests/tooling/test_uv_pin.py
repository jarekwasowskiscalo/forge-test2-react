"""One `uv` version, and every file that installs it agrees.

`scripts/install.sh` says it in its own words -- "the SAME one both workflows install.
Three files, one answer" -- and then an audit found a fourth file: the `Dockerfile`
installed `uv==0.12.0` while the other three said 0.12.5. A comment that counts the
homes of a fact is a comment that is wrong the day a fourth home appears; this test
counts them instead, and reads the value from each rather than from any one of them.

The constitution pins the *range* (`>=0.12,<0.13`, mirrored by pyproject.toml), and the
exact version only has to fall inside it -- so the range is checked here too, from the
file that declares it, rather than restated.

**The workflows are discovered rather than listed**, and that is the same lesson one
turn further on. Listing them worked until there were three, and a hand-kept list of
homes is exactly what this file exists because of. So: any workflow that installs uv
must pin it, and every pin must agree. That also catches a failure the list could not
see at all -- a `setup-uv` step with no `version:`, quietly installing whatever is
latest that morning.
"""

import re
from typing import Final

from tests._repo import REPO_ROOT

#: The two homes that are not workflows, each with the shape it writes the pin in.
HOMES: Final = {
    "scripts/install.sh": r'^UV_PIN="(\d+\.\d+\.\d+)"$',
    "Dockerfile": r"uv==(\d+\.\d+\.\d+)",
}

#: How a workflow says it is installing uv, and how it must then pin it.
INSTALLS_UV: Final = "astral-sh/setup-uv"
WORKFLOW_PIN: Final = r'^\s*UV_VERSION: "(\d+\.\d+\.\d+)"$'


def _pins() -> dict[str, str]:
    found: dict[str, str] = {}
    for relative, pattern in HOMES.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        match = re.search(pattern, text, flags=re.MULTILINE)
        assert match, f"{relative} no longer pins uv where this test looks"
        found[relative] = match.group(1)

    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflows found; this test would then pass over nothing"
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        if INSTALLS_UV not in text:
            continue
        match = re.search(WORKFLOW_PIN, text, flags=re.MULTILINE)
        assert match, (
            f"{path.name} installs uv and declares no UV_VERSION, so it installs "
            "whatever is latest that morning"
        )
        found[f".github/workflows/{path.name}"] = match.group(1)
    return found


def test_at_least_the_known_homes_are_still_found() -> None:
    """Discovery can silently find nothing; this is what stops that reading as green."""
    pins = _pins()
    assert set(HOMES) <= set(pins)
    assert any(name.startswith(".github/workflows/") for name in pins), (
        "no workflow was found to install uv, which cannot be true while CI runs"
    )


def test_every_home_of_the_uv_pin_names_the_same_version() -> None:
    pins = _pins()
    assert len(set(pins.values())) == 1, pins


def test_the_pin_falls_inside_the_range_pyproject_declares() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'required-version\s*=\s*"([^"]+)"', pyproject)
    assert match, "pyproject.toml no longer declares [tool.uv] required-version"
    lower, upper = re.findall(r"(\d+\.\d+)", match.group(1))[:2]
    pin = next(iter(set(_pins().values())))
    major_minor = tuple(int(part) for part in pin.split(".")[:2])
    assert (
        tuple(int(p) for p in lower.split("."))
        <= major_minor
        < tuple(int(p) for p in upper.split("."))
    ), f"uv {pin} is outside {match.group(1)}"
