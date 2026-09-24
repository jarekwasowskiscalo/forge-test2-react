"""What is true of this machine and this checkout right now. Read-only.

`preflight.py` answers "can this machine run the project at all" -- toolchain
presence, versions. This script answers the *next* question, the one every
"start the application" turns into: is it installed, is it already running, is the
build it serves stale, which database would it use, and is anything holding the
locks. The `run-app` skill reads the JSON and follows `advice[]` instead of
guessing state from memory.

Rules of the house apply:

- **Read-only.** Every probe inspects; nothing here starts, stops, builds or
  deletes anything. The `advice` entries name *scripts* (`./scripts/setup.sh`),
  never raw commands -- Article XII, the scripts are the interface.
- **Never crashes on a broken machine.** Subprocesses run with UTF-8 decoding
  and `errors="replace"` (under a non-UTF-8 locale one accented character in a
  path or a localised error message would raise inside `subprocess.run`),
  with timeouts, and every failure becomes a reported state rather than a
  traceback. Diagnosing a broken environment is the whole point.
- **Exit code 0 always.** This is a report, not a gate.
- **A process this checkout did not start is somebody else's.** The report says who
  holds the port -- pid, user, command, start time -- and answers separately whether
  it is this checkout's own application. Nothing here proposes ending a process whose
  ownership it could not establish, and "unknowable" is never read as "mine".
- **Article XI reaches this file.** `probe_database` publishes the *scheme* of
  `DATABASE_URL` and not the URL, because the rest is a credential. A stranger's
  full command line is the same hazard -- it can carry a password in an argument --
  so `argv` is read to decide ownership and never written into the report.

Usage:
    python3 scripts/app_status.py          # human-readable
    python3 scripts/app_status.py --json   # machine-readable, for the skills
"""

import argparse
import json
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Final

# A sibling module, imported the way `smoke_contract.py` imports `openapi_contract.py`:
# `scripts/` is on `sys.path` both when this file is run as a script and when a test
# inserts the directory. Standard library only on the other side too -- this module
# starts under whatever `python3` a bare machine has, and may not import anything that
# waits for `uv` to sync. The build-freshness fact lives there because `build.sh` and
# `test.sh` need the same verdict, and a second copy of a comparison always drifts.
from spa_build_state import BUILD_INPUTS, build_state, newest_mtime

SCHEMA_VERSION: Final = 1
REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_APP_PORT: Final = 8080


def _app_port() -> int:
    """The port this run means, which is not always 8080.

    `scripts/_lib.sh` defines it as `APP_PORT="${APP_PORT:-8080}"` and
    `start.sh --port N` sets it, so the environment is the one place that knows.
    Reading 8080 from a constant meant the report probed one port while the person
    had started the application on another -- and then advised about a port nobody
    was serving. A value that is not a number is treated as absent rather than
    raised on: this script never crashes on a broken environment.
    """
    try:
        return int(os.environ.get("APP_PORT", "") or DEFAULT_APP_PORT)
    except ValueError:
        return DEFAULT_APP_PORT


APP_PORT: Final = _app_port()
DEV_PORTS: Final[tuple[int, ...]] = (8000, 5173)
HEALTH_URL: Final = f"http://127.0.0.1:{APP_PORT}/api/health"


def _run(command: list[str], timeout: float = 15.0) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def classify_health_body(body: bytes) -> str:
    """What the thing answering :8080 actually is.

    `healthy` -- this application's `/api/health`. Anything else answering is a
    squatter: an old build, another project, a stale process -- and every result
    read off it is a result about the wrong program.
    """
    try:
        parsed = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return "answering-but-not-this-app"
    if isinstance(parsed, dict) and parsed.get("status") == "ok":
        return "healthy"
    return "answering-but-not-this-app"


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _listener_pid(port: int) -> int | None:
    """Best-effort PID of whatever listens on the port. None when unknowable.

    Best-effort is the contract, not a hedge: `lsof` is absent on a minimal image
    and refuses to name another user's process, and this report must degrade to
    "unknown" rather than fail.
    """
    completed = _run(["lsof", "-nP", "-ti", f":{port}", "-sTCP:LISTEN"])
    if completed is None or completed.returncode != 0:
        return None
    first = completed.stdout.strip().splitlines()
    try:
        return int(first[0]) if first else None
    except ValueError:
        return None


def _process_facts(pid: int) -> tuple[dict[str, str], str] | None:
    """What `ps` knows about one pid: the published facts, and the argv.

    Returned as two values because they are not equally publishable. The first is
    what the report may carry -- user, command, start time. The second is the full
    command line, which decides ownership and goes no further than this module: a
    stranger's arguments can hold a password, and this file already refuses to
    print `DATABASE_URL` for the same reason.

    A trailing `=` on each field prints values and no header, on both macOS and
    Linux. `args=` comes last because it is the one field that contains spaces.

    **`comm` is not among them, and that is the repair for a bug this file had.**
    macOS truncates that column to sixteen characters, so the venv interpreter
    `/Users/somebody/Projects/.../.venv/bin/python3` arrived as `/Users/jaroslaww`
    and the report named the command `jaroslaww` -- a slice of the user's name.
    `args` is not truncated, and its first word is the same executable, so the
    command name is taken from there.

    `-ww` because `ps` otherwise trims its output to the terminal width, and a
    trimmed command line would cut the repository's path out of the very string
    that decides ownership.
    """
    completed = _run(["ps", "-ww", "-p", str(pid), "-o", "user=,lstart=,args="])
    if completed is None or completed.returncode != 0:
        return None
    line = completed.stdout.strip().splitlines()
    if not line:
        return None
    fields = line[0].split(maxsplit=1)
    if len(fields) != 2:
        return None
    user, rest = fields
    # `lstart` is five whitespace-separated words -- "Tue Sep 16 20:58:11 2026".
    words = rest.split(maxsplit=5)
    if len(words) < 6:
        return None
    started = " ".join(words[:5])
    argv = words[5]
    command = pathlib.PurePath(argv.split(maxsplit=1)[0]).name
    return {"user": user, "started": started, "command": command}, argv


def _compose_app_is_running() -> bool:
    """Is THIS project's containerised application up?

    Container mode publishes the port through Docker's proxy, so the listener's
    command line says "com.docker.backend" and nothing about this checkout. The
    compose project is named after the directory, and `docker compose` run from
    here answers about that project alone -- which is what makes this a statement
    about ownership rather than about Docker in general.
    """
    services = _run(["docker", "compose", "ps", "--status", "running", "--services"])
    return services is not None and "app" in services.stdout.split()


def _listener_owner(port: int) -> dict[str, Any]:
    """Who holds the port, and whether it is this checkout. Never raises.

    `ours` is three-valued on purpose. `True` and `False` are findings; `None` is
    "could not tell", which happens whenever `lsof` is missing or the listener
    belongs to another user. The caller must treat `None` as *not mine* -- the
    whole defect being repaired here is an instruction to end a process on the
    strength of a pid that was sometimes not even there.
    """
    pid = _listener_pid(port)
    if pid is None:
        return {"pid": None, "user": None, "command": None, "started": None, "ours": None}

    facts = _process_facts(pid)
    if facts is None:
        return {"pid": pid, "user": None, "command": None, "started": None, "ours": None}

    published, argv = facts
    # Host mode runs `.venv/bin/python scripts/run.py`, and that interpreter lives
    # inside the checkout -- so the repository's own path in the command line is
    # proof of ownership that a pid alone could never be.
    ours = str(REPO_ROOT) in argv or _compose_app_is_running()
    return {"pid": pid, **published, "ours": ours}


def _free_port_above(port: int, span: int = 20) -> int | None:
    """The first port above `port` that nothing is listening on.

    Offered instead of a kill. Searched rather than taken from `bind(0)` so the
    suggestion is a neighbour a person recognises (8081 beside 8080) rather than
    an ephemeral five-digit number. It is a suggestion and nothing reserves it.
    """
    for candidate in range(port + 1, port + 1 + span):
        if candidate < 65536 and not _port_open(candidate):
            return candidate
    return None


# --------------------------------------------------------------------------- #
# Probes -- each returns one entry of `checks`
# --------------------------------------------------------------------------- #


def probe_toolchain() -> dict[str, Any]:
    """Presence only. Versions are preflight.py's job, and it says so."""
    return {
        "present": {
            name: shutil.which(name) is not None for name in ("uv", "node", "npm", "docker")
        },
        "note": "presence only; versions are scripts/preflight.py's job",
    }


def probe_python_env() -> dict[str, Any]:
    venv = (REPO_ROOT / ".venv").is_dir()
    node_modules = REPO_ROOT / "frontend" / "node_modules"
    lockfile = REPO_ROOT / "frontend" / "package-lock.json"
    node_deps_fresh = node_modules.is_dir() and (
        not lockfile.is_file() or lockfile.stat().st_mtime <= node_modules.stat().st_mtime
    )
    return {
        "venv": venv,
        "node_modules": node_modules.is_dir(),
        "node_deps_fresh": node_deps_fresh,
        "installed": venv and node_deps_fresh,
    }


def probe_docker() -> dict[str, Any]:
    if shutil.which("docker") is None:
        return {"state": "absent"}
    completed = _run(["docker", "info", "--format", "{{.OSType}}"])
    if completed is None or completed.returncode != 0:
        return {"state": "daemon-down"}
    return {"state": "up", "os_type": (completed.stdout or "").strip() or "linux"}


def probe_database(docker_up: bool) -> dict[str, Any]:
    import os

    db_service = False
    volume = False
    if docker_up:
        services = _run(["docker", "compose", "ps", "--status", "running", "--services"])
        db_service = services is not None and "db" in services.stdout.split()
        volumes = _run(["docker", "volume", "ls", "--format", "{{.Name}}"])
        volume = volumes is not None and any(
            name.endswith("postgres_data") for name in volumes.stdout.split()
        )
    url = os.environ.get("DATABASE_URL", "")
    return {
        "postgres_service_running": db_service,
        "postgres_volume_exists": volume,
        # The scheme says which engine; the rest of the URL carries credentials
        # and never reaches a report.
        "database_url_scheme": url.split("://", 1)[0] if url else None,
    }


def probe_app_port() -> dict[str, Any]:
    if not _port_open(APP_PORT):
        return {
            "state": "free",
            "port": APP_PORT,
            "pid": None,
            "user": None,
            "command": None,
            "started": None,
            "ours": None,
            "free_port": None,
        }
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as response:
            state = classify_health_body(response.read())
    except (urllib.error.URLError, OSError, TimeoutError):
        # Two seconds of silence is also what a slow start looks like. Which of
        # the two this is, `ours` below answers -- the state alone cannot.
        state = "listening-not-answering"
    owner = _listener_owner(APP_PORT)
    return {
        "state": state,
        "port": APP_PORT,
        **owner,
        "free_port": _free_port_above(APP_PORT),
    }


def probe_dev_ports() -> dict[str, Any]:
    return {str(port): _port_open(port) for port in DEV_PORTS}


def probe_frontend_build() -> dict[str, Any]:
    sources = [newest_mtime(REPO_ROOT / rel) for rel in BUILD_INPUTS]
    return {"state": build_state(REPO_ROOT / "app" / "static", sources)}


def probe_logs() -> dict[str, Any]:
    return {
        name: {"path": str(path), "exists": path.is_file()}
        for name, path in (
            ("app", REPO_ROOT / ".sdd" / "logs" / "app.log"),
            ("e2e_app", REPO_ROOT / ".sdd" / "logs" / "e2e-app.log"),
        )
    }


# --------------------------------------------------------------------------- #
# Advice -- the ordered decision table run-app consumes
# --------------------------------------------------------------------------- #


def _describe_holder(port: dict[str, Any]) -> str:
    """The listener in words a person can act on, degrading one fact at a time.

    "something else" was the whole description a person used to get, next to an
    instruction to end it. Each fact here is optional, because each can genuinely
    be unknown -- `lsof` will not name another user's process, and `ps` will not
    always be there -- and the sentence has to stay readable when any of them is.
    """
    named = [str(port[key]) for key in ("command", "user") if port.get(key)]
    who = " run by ".join(named) if named else "an unidentified process"
    if port.get("pid"):
        who += f" (pid {port['pid']}"
        who += f", started {port['started']})" if port.get("started") else ")"
    elif not named:
        who = "a process this machine would not name"
    return who


def advise(checks: dict[str, Any]) -> list[dict[str, str]]:
    advice: list[dict[str, str]] = []

    if not checks["python_env"]["installed"]:
        advice.append(
            {
                "code": "NOT_INSTALLED",
                "detail": "dependencies are missing or older than their lockfiles",
                "run": "./scripts/setup.sh",
            }
        )

    docker_state = checks["docker"]["state"]
    if docker_state in ("absent", "daemon-down"):
        advice.append(
            {
                "code": "DOCKER_DOWN",
                "detail": "there is nowhere to run Postgres: start.sh, the backend tests "
                "and e2e all need one",
                "run": "start Docker Desktop / the docker service, or point "
                "APP_TEST_DATABASE_URL and DATABASE_URL at a Postgres you already have",
            }
        )

    port = checks["app_port"]
    if port["state"] == "healthy":
        advice.append(
            {
                "code": "ALREADY_RUNNING_HEALTHY",
                "detail": f"this application answers on :{port.get('port', APP_PORT)}"
                + (
                    " but the build it serves is stale"
                    if checks["frontend_build"]["state"] == "stale"
                    else ""
                ),
                "run": "nothing to start; restart via ./scripts/stop.sh + ./scripts/start.sh "
                "only if a fresh build or code is needed",
            }
        )
    elif port["state"] in ("answering-but-not-this-app", "listening-not-answering"):
        held = port.get("port", APP_PORT)
        if port.get("ours") is True:
            advice.append(
                {
                    "code": "APP_STARTING",
                    "detail": f"this checkout's own application holds :{held} and has not "
                    "answered /api/health yet -- a start that is still warming up looks "
                    "exactly like this",
                    "run": f"wait, polling http://127.0.0.1:{held}/api/health; if it never "
                    "answers, ./scripts/stop.sh then ./scripts/start.sh",
                }
            )
        else:
            advice.append(
                {
                    "code": "PORT_SQUATTER",
                    "detail": f"{_describe_holder(port)} holds :{held} and this checkout "
                    + (
                        "did not start it"
                        if port.get("ours") is False
                        else "cannot tell whether it did"
                    )
                    + "; any result read off that port is about the wrong program",
                    "run": (
                        f"./scripts/start.sh --port {port['free_port']} leaves it alone"
                        if port.get("free_port")
                        else "./scripts/start.sh --port N leaves it alone"
                    )
                    + " -- ask the user before stopping a process this checkout does not own",
                }
            )

    build = checks["frontend_build"]["state"]
    if build == "missing":
        advice.append(
            {
                "code": "BUILD_MISSING",
                "detail": "app/static has no build; the app would serve 404 for the UI",
                "run": "./scripts/build.sh (or ./scripts/start.sh --development, which "
                "serves sources via Vite)",
            }
        )
    elif build == "stale" and port["state"] != "healthy":
        advice.append(
            {
                "code": "BUILD_STALE",
                "detail": "frontend sources are newer than app/static",
                "run": "./scripts/build.sh before starting, or use --development",
            }
        )

    if checks["database"]["postgres_volume_exists"]:
        advice.append(
            {
                "code": "DB_FRESH_CHOICE",
                "detail": "a Postgres volume with data exists; 'from scratch' is a choice, "
                "not a default",
                "run": "keep the data (just start) OR ./scripts/db.sh reset -- destructive, "
                "ask the user first",
            }
        )

    # The change process's own gate lock (.sdd/gate.lock) is not probed here, by
    # decision: it is the process's file, judged by the process's own contention
    # module against its own threshold, and an application script that read it would
    # be the one coupling from this tree into that one.
    return advice


def build_report() -> dict[str, Any]:
    checks: dict[str, Any] = {
        "toolchain": probe_toolchain(),
        "python_env": probe_python_env(),
        "docker": probe_docker(),
    }
    checks["database"] = probe_database(checks["docker"]["state"] == "up")
    checks["app_port"] = probe_app_port()
    checks["dev_ports"] = probe_dev_ports()
    checks["frontend_build"] = probe_frontend_build()
    checks["logs"] = probe_logs()
    return {
        "schema_version": SCHEMA_VERSION,
        "platform": platform.system().lower(),
        "checks": checks,
        "advice": advise(checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="What is true right now. Changes nothing.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("Application status (read-only):")
    for name, value in report["checks"].items():
        print(f"  {name}: {json.dumps(value, ensure_ascii=False)}")
    if report["advice"]:
        print("\nAdvice, in order:")
        for entry in report["advice"]:
            print(f"  [{entry['code']}] {entry['detail']}")
            print(f"      -> {entry['run']}")
    else:
        print("\nNothing in the way.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
