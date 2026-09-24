"""The four mechanism sentences in `.specconf/stack.json` still describe this repository.

The engine names the PROPERTY a design skill needs and the profile names the MECHANISM:
`storage_contract`, `migration_mechanism`, `readiness`, `binding_target`. The engine renders
all four into a worker's preflight brief, reads none of the prose, and by the worker
contract the brief outranks the skill's own body -- so a sentence here beats the skill's
rule, which is exactly why it has to be true.

All four are optional to the engine, for a rollout reason rather than a design one, and
optional is what this test compensates for: drop a key and nothing fails, the brief simply
stops printing a heading and the worker goes back to assuming. The Flutter template holds
its own four the same way (`test/fitness/profile_mechanisms_test.dart` there).

A standing guarantee of the template, not a requirement of one change, so it cites
nothing. Reads the profile, the scripts and the sources as text. No Docker, no database.
"""

import json
import pathlib
import re
from typing import Final

import pytest

from tests._repo import REPO_ROOT

PROFILE: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "stack.json"

#: The four keys, and the question each answers.
MECHANISMS: Final[dict[str, str]] = {
    "storage_contract": 'how an "at most one" rule survives two writers',
    "migration_mechanism": "how a change of data shape reaches a running installation",
    "readiness": 'what evidences "the application comes up"',
    "binding_target": "what a screen's field binds to",
}

#: A repository path as the sentences write it: a directory with a slash, or a file with a
#: suffix. Prose never has either, so the pattern needs no list of known roots.
_PATH: Final = re.compile(
    r"(?<![\w/.])(?:\./)?(?P<path>(?:[\w.-]+/)+(?:[\w.-]+\.(?:py|sh|md|yaml|ts))?)"
)

#: `/api/health` with a leading slash, as a route rather than as part of a URL path.
_ROUTE: Final = re.compile(r"GET (?P<route>/api/[\w-]+)")


def _profile() -> dict[str, object]:
    loaded = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _sentence(key: str) -> str:
    value = _profile().get(key)
    assert isinstance(value, str), f"{key} is not declared in .specconf/stack.json"
    return value


def test_the_profile_answers_every_mechanism_question_the_engine_asks() -> None:
    missing = [
        f"{key} ({question})"
        for key, question in MECHANISMS.items()
        if not isinstance(_profile().get(key), str) or not str(_profile()[key]).strip()
    ]
    assert not missing, (
        f"{missing}: a key left out and a key declared empty say the same thing to the "
        "engine -- this stack has no such mechanism -- and the design skill then says "
        "nothing where it would have named one. Every one of the four has a mechanism "
        "here; write it at the foot of .specconf/stack.json."
    )


@pytest.mark.parametrize("key", sorted(MECHANISMS))
def test_every_path_a_mechanism_names_is_there(key: str) -> None:
    named = {m.group("path") for m in _PATH.finditer(_sentence(key))}
    assert named, f"{key} names no file at all -- a mechanism nobody can find is a claim"
    gone = sorted(path for path in named if not (REPO_ROOT / path).exists())
    assert not gone, (
        f".specconf/stack.json § {key} names {gone}, which this repository no longer has. "
        "The sentence reaches a worker's brief and outranks its skill; move it with the file."
    )


def test_the_readiness_route_is_the_one_the_scripts_poll_and_the_app_serves() -> None:
    match = _ROUTE.search(_sentence("readiness"))
    assert match is not None, "readiness no longer names a `GET /api/...` route"
    route = match.group("route")
    lib = (REPO_ROOT / "scripts" / "_lib.sh").read_text(encoding="utf-8")
    assert f'APP_HEALTH_URL="http://127.0.0.1:${{APP_PORT}}{route}"' in lib, (
        f"readiness says {route}, and scripts/_lib.sh's APP_HEALTH_URL -- the probe start.sh "
        "polls -- asks something else. One of the two is wrong about when the app is up."
    )
    router = (REPO_ROOT / "app" / "platform" / "routers" / "health.py").read_text(encoding="utf-8")
    leaf = route.removeprefix("/api")
    assert re.search(rf"""@router\.get\(\s*["']{re.escape(leaf)}["']""", router), (
        f"app/platform/routers/health.py no longer serves {leaf} (under the /api prefix), "
        "so the readiness the profile promises answers 404."
    )
