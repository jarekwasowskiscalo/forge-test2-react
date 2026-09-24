"""The status report's pure parts: health classification, staleness, advice shape.

`scripts/app_status.py` is what the `run-app` skill trusts instead of guessing
machine state from memory, so the judgments that can be tested without Docker or
a network are tested here: what counts as *this* application answering, when a
build counts as stale, and that the advice table stays machine-consumable
(stable codes, a script named in every `run`).

No database, no Docker, no network -- the probes that need them are exercised by
running the script on a real machine, not by this file.
"""

import pathlib
import shutil
import subprocess
import sys
from typing import Final

import pytest

from tests._repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import app_status

_A_PORT_NOTHING_HOLDS: Final = 1
"""Privileged, unbindable without root, and not a port this project ever serves."""

# --------------------------------------------------------------------------- #
# classify_health_body -- what counts as THIS app
# --------------------------------------------------------------------------- #


def test_the_real_health_body_is_healthy() -> None:
    assert app_status.classify_health_body(b'{"status": "ok"}') == "healthy"


@pytest.mark.parametrize(
    "body",
    [
        b"<!doctype html><html>...</html>",  # the SPA catch-all, or another web app
        b'{"status": "degraded"}',
        b'{"ok": true}',
        b"OK",
        b"",
    ],
)
def test_anything_else_is_a_squatter(body: bytes) -> None:
    """An old build or another project answering 200 is the failure mode this
    classification exists for: every result read off it is about the wrong program."""
    assert app_status.classify_health_body(body) == "answering-but-not-this-app"


# --------------------------------------------------------------------------- #
# build_state -- missing / current / stale from mtimes
# --------------------------------------------------------------------------- #


def test_no_index_html_means_missing(tmp_path: pathlib.Path) -> None:
    assert app_status.build_state(tmp_path / "static", [1000.0]) == "missing"


def test_sources_newer_than_the_build_mean_stale(tmp_path: pathlib.Path) -> None:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("built", encoding="utf-8")
    built = (static / "index.html").stat().st_mtime
    assert app_status.build_state(static, [built + 100]) == "stale"
    assert app_status.build_state(static, [built - 100]) == "current"
    assert app_status.build_state(static, []) == "current"


# --------------------------------------------------------------------------- #
# advise -- the decision table run-app consumes
# --------------------------------------------------------------------------- #


def _checks(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "python_env": {"installed": True},
        "docker": {"state": "up"},
        "app_port": {"state": "free", "port": 8080, "pid": None},
        "frontend_build": {"state": "current"},
        "database": {"postgres_volume_exists": False},
    }
    base.update(overrides)
    return base


def _held(**fields: object) -> dict[str, object]:
    """An `app_port` check for a port somebody is holding.

    Defaults to the honest worst case -- a listener nothing could identify -- so a
    test that cares about one fact states that fact and inherits ignorance for the
    rest, which is the shape a real machine hands over most often.
    """
    holder: dict[str, object] = {
        "state": "listening-not-answering",
        "port": 8080,
        "pid": None,
        "user": None,
        "command": None,
        "started": None,
        "ours": None,
        "free_port": 8081,
    }
    holder.update(fields)
    return holder


def _codes(checks: dict[str, object]) -> list[str]:
    return [entry["code"] for entry in app_status.advise(checks)]


def test_a_clean_machine_gets_no_advice() -> None:
    assert _codes(_checks()) == []


def test_the_codes_are_stable_and_ordered() -> None:
    """The skill branches on these strings; renaming one silently breaks it."""
    checks = _checks(
        python_env={"installed": False},
        docker={"state": "daemon-down"},
        app_port={"state": "answering-but-not-this-app", "port": 8080, "pid": 4242},
        frontend_build={"state": "missing"},
        database={"postgres_volume_exists": True},
    )
    assert _codes(checks) == [
        "NOT_INSTALLED",
        "DOCKER_DOWN",
        "PORT_SQUATTER",
        "BUILD_MISSING",
        "DB_FRESH_CHOICE",
    ]


# --------------------------------------------------------------------------- #
# Who holds the port -- a pid is not an identification, and not a mandate
# --------------------------------------------------------------------------- #


def test_the_squatter_advice_names_the_owner_and_not_just_the_pid() -> None:
    """A pid names nothing a person can judge.

    The advice this replaces said "something else holds :8080 (pid 4242)" and then
    told the reader to end it. Whose process, running what, since when -- all three
    were absent, and all three are what makes the difference between a forgotten
    server of one's own and somebody else's work.
    """
    checks = _checks(
        app_port=_held(
            pid=4242, user="dana", command="postgres", started="Tue Sep 16 09:12:00 2026"
        )
    )
    (entry,) = app_status.advise(checks)
    assert entry["code"] == "PORT_SQUATTER"
    for fact in ("4242", "dana", "postgres", "Tue Sep 16 09:12:00 2026"):
        assert fact in entry["detail"], f"the advice does not say {fact!r}: {entry['detail']}"


def test_the_squatter_advice_offers_a_free_port_before_anything_else() -> None:
    """A free port ends the collision without touching anybody's process."""
    checks = _checks(app_port=_held(pid=4242, ours=False, free_port=8081))
    (entry,) = app_status.advise(checks)
    assert "--port 8081" in entry["run"]


def test_the_squatter_advice_asks_before_stopping_what_is_not_ours() -> None:
    """The gap this closes, stated as an assertion.

    `DB_FRESH_CHOICE` has always said "ask the user" and "never reset unasked";
    the port branch said "a stray process by pid" and required nothing at all.
    """
    checks = _checks(app_port=_held(pid=4242, ours=False))
    (entry,) = app_status.advise(checks)
    assert "ask the user" in entry["run"].lower()
    assert "stop.sh" not in entry["run"], (
        "a stop offered for a process this checkout does not own is the defect, "
        f"not the repair: {entry['run']}"
    )


def test_an_unidentifiable_holder_is_not_treated_as_ours() -> None:
    """`lsof` refuses to name another user's process, so "unknown" is common.

    Unknown has to fall on the cautious side. Reading it as "probably mine" is how
    an instruction to stop a process reaches a process nobody identified.
    """
    (entry,) = app_status.advise(_checks(app_port=_held(ours=None, pid=None)))
    assert entry["code"] == "PORT_SQUATTER"
    assert "ask the user" in entry["run"].lower()


def test_our_own_slow_start_is_not_called_a_squatter() -> None:
    """The false positive: `listening-not-answering` after a 2 s timeout.

    An application of this checkout's own that has not finished starting reaches
    the identical state, and used to reach the identical advice -- which named the
    pid of the very application the reader was trying to start.
    """
    (entry,) = app_status.advise(_checks(app_port=_held(pid=4242, ours=True)))
    assert entry["code"] == "APP_STARTING"
    assert "wait" in entry["run"]


def test_a_stranger_answering_on_the_port_is_still_a_squatter() -> None:
    """Not ours and answering the wrong body is the original case, still held."""
    checks = _checks(app_port=_held(state="answering-but-not-this-app", pid=7, ours=False))
    (entry,) = app_status.advise(checks)
    assert entry["code"] == "PORT_SQUATTER"


def test_the_advice_speaks_of_the_port_the_report_probed() -> None:
    """`--port N` moves the port, so a hardcoded 8080 in the text would misname it."""
    checks = _checks(app_port=_held(port=8092, pid=4242, ours=False, free_port=8093))
    (entry,) = app_status.advise(checks)
    assert ":8092" in entry["detail"]
    assert "8080" not in entry["detail"] and "8080" not in entry["run"]


def test_the_holder_description_degrades_one_fact_at_a_time() -> None:
    """Each fact is genuinely optional, and the sentence has to survive each loss."""
    assert "4242" in app_status._describe_holder({"pid": 4242})
    assert "dana" in app_status._describe_holder({"pid": 4242, "user": "dana"})
    described = app_status._describe_holder({})
    assert described and "None" not in described


def test_a_long_executable_path_is_not_truncated_into_a_command_name(
    tmp_path: pathlib.Path,
) -> None:
    """A real process, because this defect only exists between `ps` and the parser.

    The first draft asked `ps` for `comm`, which macOS truncates to sixteen
    characters. A venv interpreter under a home directory came back as
    `/Users/jaroslaww` and the report named the command `jaroslaww` -- a slice of
    the user's own name, printed as the identity of the process it was about to
    advise ending. The command now comes from `args`, which is not truncated.

    **A SYMLINK, not a borrowed `argv[0]`.** The draft before this one passed the
    long path as `args[0]` with `executable=sys.executable`, on the reasoning that
    `argv[0]` is whatever the caller says it is. It is -- until the interpreter
    re-execs itself, which a macOS **framework** build does through
    `Python.app/Contents/MacOS/Python`, overwriting `argv[0]` on the way.

    That is not an abstract risk, it is which Python each machine happens to hand
    over. `uv sync` on the macOS runner reports `Using CPython 3.14.7 interpreter at:
    /opt/homebrew/opt/python@3.14/bin/python3.14` -- Homebrew's framework build --
    and the assertion failed there with `command` coming back as `Python`, the app
    bundle's own binary name. A developer's uv-managed interpreter is a plain Mach-O
    executable and rewrites nothing, so the same test passed on every workstation.

    The cross-platform leg runs weekly, on the trunk, on a pull request carrying the
    `cross-platform` label, or when `.github/` itself changes -- so the trunk carried
    this red until a pull request that touched CI ran the leg and surfaced it.

    A symlink moves the long name into the path actually executed, where no runtime
    can rewrite it. `sleep` rather than a copied binary: a copy of a signed system
    binary will not start on macOS at all, and a `#!` script would put the
    interpreter in `argv[0]` (`ps` reports `/bin/sh <path>`), which is the same
    defeat by a different route.
    """
    stranger = tmp_path / "a" / "very" / "long" / "path" / "past" / "sixteen" / "lonelyserver3"
    assert len(str(stranger)) > 16, "the path has to be long enough to be truncated"

    sleep = shutil.which("sleep")
    assert sleep is not None, "no `sleep` on PATH to borrow a name for"
    stranger.parent.mkdir(parents=True, exist_ok=True)
    stranger.symlink_to(sleep)

    process = subprocess.Popen([str(stranger), "30"])
    try:
        facts = app_status._process_facts(process.pid)
        assert facts is not None, "ps named nothing for a process we just started"
        published, argv = facts
        assert published["command"] == "lonelyserver3", (
            f"the command came back as {published['command']!r} -- a truncated path, not a program"
        )
        assert str(stranger) in argv, "the command line was trimmed; ownership reads that string"
        assert published["started"] and published["user"]
    finally:
        process.kill()
        process.wait(timeout=10)


def test_the_report_never_carries_the_holders_command_line() -> None:
    """Article XI reaches a stranger's argv: it can hold a password.

    `probe_database` publishes the scheme of `DATABASE_URL` and not the URL for
    exactly this reason. Ownership is decided from the command line; the report
    gets the facts a person needs and not the arguments.
    """
    owner = app_status._listener_owner(_A_PORT_NOTHING_HOLDS)
    assert set(owner) == {"pid", "user", "command", "started", "ours"}
    assert "argv" not in owner and "args" not in owner


def test_a_healthy_app_is_reported_not_restarted() -> None:
    checks = _checks(app_port={"state": "healthy", "port": 8080, "pid": 1})
    (entry,) = app_status.advise(checks)
    assert entry["code"] == "ALREADY_RUNNING_HEALTHY"


def test_a_stale_build_behind_a_healthy_app_is_named_in_the_detail() -> None:
    checks = _checks(
        app_port={"state": "healthy", "port": 8080, "pid": 1},
        frontend_build={"state": "stale"},
    )
    codes = _codes(checks)
    assert codes == ["ALREADY_RUNNING_HEALTHY"], "no separate BUILD_STALE while it runs"
    (entry,) = app_status.advise(checks)
    assert "stale" in entry["detail"]


def test_every_advice_run_names_a_script_or_a_wait() -> None:
    """Article XII: the advice hands out scripts, never raw commands."""
    checks = _checks(
        python_env={"installed": False},
        docker={"state": "absent"},
        app_port={"state": "listening-not-answering", "port": 8080, "pid": None},
        frontend_build={"state": "missing"},
        database={"postgres_volume_exists": True},
    )
    for entry in app_status.advise(checks):
        assert (
            ("scripts/" in entry["run"])
            or ("wait" in entry["run"])
            or ("remove" in entry["run"])
            or ("Docker" in entry["run"])
        ), f"{entry['code']}: {entry['run']}"


# --------------------------------------------------------------------------- #
# Which port the report is even about
# --------------------------------------------------------------------------- #


def test_the_port_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """`start.sh --port N` sets `APP_PORT`, and this report has to mean the same one.

    It read a constant 8080 while `scripts/_lib.sh:248` defined the port as
    `APP_PORT="${APP_PORT:-8080}"` -- so after `--port 8090` the report probed a
    port nobody was serving and advised about it with total confidence.
    """
    monkeypatch.setenv("APP_PORT", "8090")
    assert app_status._app_port() == 8090


def test_an_unset_port_is_still_8080(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every existing caller sets nothing; the default cannot move."""
    monkeypatch.delenv("APP_PORT", raising=False)
    assert app_status._app_port() == app_status.DEFAULT_APP_PORT == 8080


@pytest.mark.parametrize("value", ["", "eight thousand", "80 80"])
def test_a_port_that_is_not_a_number_never_raises(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """Exit code 0 always: a broken environment is what this script is for."""
    monkeypatch.setenv("APP_PORT", value)
    assert app_status._app_port() == app_status.DEFAULT_APP_PORT


def test_the_report_shape_is_stable() -> None:
    report = app_status.build_report()
    assert set(report) == {"schema_version", "platform", "checks", "advice"}
    assert set(report["checks"]) == {
        "toolchain",
        "python_env",
        "docker",
        "database",
        "app_port",
        "dev_ports",
        "frontend_build",
        "logs",
    }
