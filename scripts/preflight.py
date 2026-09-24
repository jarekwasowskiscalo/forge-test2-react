"""Preflight prerequisite check (Boundary: PreflightScript).

Reports the presence/version status of the environment's prerequisites in
clear, human-readable terms, without installing anything or modifying any
system configuration. Runnable independently of performing environment
setup or starting the application (Requirement 3.1) — this module uses only
the Python standard library (`sys`, `shutil`, `subprocess`, `dataclasses`,
`typing`), so it works via a bare `python3 scripts/preflight.py` even on a
machine where `uv` and the project's dependencies are not installed yet.
That is the entire point: this script must be able to diagnose its own
missing prerequisites.

Each prerequisite is implemented as one `Check` function returning a
`CheckResult`. Checks are read-only: they only inspect the environment
(`shutil.which`, `subprocess.run` of a `--version` flag) and never install a
tool or modify PATH/system configuration (Requirement 3.7). New prerequisites
are added by writing a new `check_*` function and appending it to the
`CHECKS` list — existing check functions never need to change to add one
(Requirement 3.8).

The Docker check is informational (`required=False`): it always runs and
always appears in the report, but its result never causes `run_preflight`
to return a nonzero exit code (Requirement 3.4).
"""

import pathlib
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

MIN_PYTHON_VERSION = (3, 14)

#: The uv range `[tool.uv] required-version` in pyproject.toml accepts. It must
#: say the same thing as that line: this check exists so a machine is told it is
#: not ready *here*, rather than by the next `uv sync` refusing halfway through a
#: task. An exact pin used to live in both places, and it made the template
#: unusable on any machine whose uv was one patch newer.
#:
#: A range and not a floor: uv's minor releases have changed lockfile handling,
#: so "newer is fine" is not a claim this project makes past the current minor.
UV_VERSION_FLOOR = (0, 12, 0)
UV_VERSION_CEILING = (0, 13, 0)
UV_VERSION_RANGE_STR = ">=0.12,<0.13"

#: The Node major CI builds the frontend with (.github/workflows) and the
#: Dockerfile's frontend stage. Informational: nothing here installs Node.
NODE_MAJOR = 26


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a single prerequisite check.

    Attributes:
        name: Human-readable prerequisite name, e.g. "uv".
        required: Whether this prerequisite's failure should fail preflight
            overall. Docker's check sets this to False (informational).
        ok: Whether the prerequisite is present and meets its requirement.
        message: Human-readable status, e.g.
            "uv 0.12.5 found (>=0.12,<0.13 required)".
    """

    name: str
    required: bool
    ok: bool
    message: str


Check = Callable[[], CheckResult]


def _parse_version(text: str) -> tuple[int, ...] | None:
    """Best-effort extraction of a dotted numeric version from free text.

    Defensive by design: `uv --version` / `docker --version` output format
    can drift across releases. If no numeric dotted version can be found,
    this returns None so callers can fall back to "present, version
    undetermined" rather than crashing (per design's Implementation Notes
    Risks).
    """
    for token in text.replace(",", " ").split():
        parts = token.split(".")
        if not parts:
            continue
        digits: list[int] = []
        for part in parts:
            digit_chars = "".join(ch for ch in part if ch.isdigit())
            if not digit_chars:
                digits = []
                break
            digits.append(int(digit_chars))
        if digits:
            return tuple(digits)
    return None


def check_python_version() -> CheckResult:
    """Report whether the running Python interpreter meets the minimum
    required version (Requirement 3.2). Required=True.
    """
    name = "Python interpreter"
    current = sys.version_info[:2]
    version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    required_str = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
    if current >= MIN_PYTHON_VERSION:
        return CheckResult(
            name=name,
            required=True,
            ok=True,
            message=f"Python {version_str} found (>= {required_str} required)",
        )
    return CheckResult(
        name=name,
        required=True,
        ok=False,
        message=f"Python {version_str} found, but >= {required_str} is required",
    )


def check_uv() -> CheckResult:
    """Report whether `uv` is installed and, where determinable, whether its
    version satisfies the project's requirement (Requirement 3.3).
    Required=True.
    """
    name = "uv"
    uv_path = shutil.which("uv")
    if uv_path is None:
        return CheckResult(
            name=name,
            required=True,
            ok=False,
            message="uv not found on PATH (required — see README for install instructions)",
        )

    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            # `text=True` alone decodes with the platform default, which under a
            # non-UTF-8 locale is not UTF-8 -- and every tool queried here emits
            # UTF-8. One accented character in a path or a localised error message
            # then raises UnicodeDecodeError *inside* `subprocess.run`, where the
            # handler below cannot see it: UnicodeDecodeError descends from
            # ValueError, not from OSError or SubprocessError. This script's whole
            # contract is to diagnose a broken environment without crashing, and
            # that is exactly the environment it would crash in.
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(
            name=name,
            required=True,
            ok=True,
            message=f"uv found at {uv_path}, but version could not be determined ({exc})",
        )

    output = (result.stdout or "") + (result.stderr or "")
    version = _parse_version(output)
    if version is None:
        return CheckResult(
            name=name,
            required=True,
            ok=True,
            message=f"uv found at {uv_path}, present, version undetermined "
            f"(unexpected `uv --version` output: {output.strip()!r})",
        )

    version_str = ".".join(str(part) for part in version)
    if UV_VERSION_FLOOR <= version < UV_VERSION_CEILING:
        return CheckResult(
            name=name,
            required=True,
            ok=True,
            message=f"uv {version_str} found ({UV_VERSION_RANGE_STR} required)",
        )

    return CheckResult(
        name=name,
        required=True,
        ok=False,
        message=f"uv {version_str} found, but {UV_VERSION_RANGE_STR} is required "
        f"(pyproject.toml states the same range; run `uv self update`)",
    )


def check_docker() -> CheckResult:
    """Report whether Docker is present on the machine, as an informational
    prerequisite for future use (Requirement 3.4). Required=False: its
    absence must never fail preflight overall.

    Every unhappy branch names the way forward, because this is the first thing
    somebody runs on a new machine and it used to say only what was missing. Docker
    is genuinely required for exactly one thing -- building the production image.
    Everything else needs a *Postgres*, and a container is only one way to have one.
    """
    name = "Docker"
    docker_path = shutil.which("docker")
    if docker_path is None:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message="Docker not found on PATH (informational only — not required by this feature)."
            " Docker is not required to run the tests: point APP_TEST_DATABASE_URL at a Postgres you already have, or run the subset that needs no database (./scripts/test.sh --no-db, ./scripts/check.sh --no-docker).",
        )
    # Presence of the binary is the least interesting fact about Docker. What
    # actually stops a developer is a daemon that is not running, so the probe is
    # `docker info` rather than `docker --version`: only the first one talks to it.
    try:
        info = subprocess.run(
            # `{{.ServerVersion}}` rather than a format nothing reads: only the exit
            # code is judged below, and a template asking for a value no caller wants
            # is a line the next reader has to decide the meaning of.
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            # `text=True` alone decodes with the platform default, which under a
            # non-UTF-8 locale is not UTF-8 -- and every tool queried here emits
            # UTF-8. One accented character in a path or a localised error message
            # then raises UnicodeDecodeError *inside* `subprocess.run`, where the
            # handler below cannot see it: UnicodeDecodeError descends from
            # ValueError, not from OSError or SubprocessError. This script's whole
            # contract is to diagnose a broken environment without crashing, and
            # that is exactly the environment it would crash in.
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message=f"Docker found at {docker_path}, but could not be queried ({exc})",
        )

    if info.returncode != 0:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message=f"Docker found at {docker_path}, but the daemon is not running or not "
            "reachable — start Docker Desktop / the docker service."
            " Docker is not required to run the tests: point APP_TEST_DATABASE_URL at a Postgres you already have, or run the subset that needs no database (./scripts/test.sh --no-db, ./scripts/check.sh --no-docker).",
        )

    return CheckResult(
        name=name,
        required=False,
        ok=True,
        message=f"Docker found at {docker_path}, daemon reachable",
    )


def check_docker_compose() -> CheckResult:
    """Report whether the Compose v2 plugin is available (Requirement 3.4).

    Every script in `scripts/` calls `docker compose`, never `docker-compose`.
    A Linux install from a distribution package often ships the engine without
    the plugin, which passes a `docker` check and then fails at the first
    `docker compose up` with an unhelpful "is not a docker command".
    Informational, like Docker itself.
    """
    name = "docker compose"
    if shutil.which("docker") is None:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message="not checked — Docker itself is not on PATH",
        )
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            # `text=True` alone decodes with the platform default, which under a
            # non-UTF-8 locale is not UTF-8 -- and every tool queried here emits
            # UTF-8. One accented character in a path or a localised error message
            # then raises UnicodeDecodeError *inside* `subprocess.run`, where the
            # handler below cannot see it: UnicodeDecodeError descends from
            # ValueError, not from OSError or SubprocessError. This script's whole
            # contract is to diagnose a broken environment without crashing, and
            # that is exactly the environment it would crash in.
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(
            name=name, required=False, ok=False, message=f"could not be queried ({exc})"
        )
    if result.returncode != 0:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message="the Compose v2 plugin is missing — every script here uses "
            "`docker compose`, not `docker-compose`",
        )
    return CheckResult(
        name=name,
        required=False,
        ok=True,
        message=((result.stdout or "").strip() or "available"),
    )


def check_node() -> CheckResult:
    """Report whether Node is present for the frontend build (Requirement 3.4).

    Informational: the backend and the test suite run without it. But
    `app/static/` is gitignored, so a checkout serves no UI at all until
    `npm run build` has run once, and nothing else in the environment tells a
    developer that Node is what they are missing.
    """
    name = "Node"
    node_path = shutil.which("node")
    if node_path is None:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message=f"Node not found on PATH — needed to build the frontend "
            f"(`cd frontend && npm ci && npm run build`); CI uses Node {NODE_MAJOR}",
        )
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(
            name=name,
            required=False,
            ok=True,
            message=f"Node found at {node_path}, version undetermined ({exc})",
        )
    version = _parse_version((result.stdout or "") + (result.stderr or ""))
    if version is None:
        return CheckResult(name=name, required=False, ok=True, message=f"Node found at {node_path}")
    version_str = ".".join(str(part) for part in version)
    if version[0] < NODE_MAJOR:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message=f"Node {version_str} found, but the frontend is built with Node "
            f"{NODE_MAJOR} in CI and Vite 8 needs a modern runtime",
        )
    return CheckResult(
        name=name,
        required=False,
        ok=True,
        message=f"Node {version_str} found (CI builds with Node {NODE_MAJOR})",
    )


def check_terraform() -> CheckResult:
    """Terraform, and whether it is the version this project pins.

    Informational, never required: nothing in the normal loop touches the
    infrastructure, and `scripts/infra-check.sh` and `scripts/infra.sh` both fall
    back to the pinned Docker image when the binary is absent.

    The VERSION is what this reports on, not the presence. Two Terraform versions
    write two state formats and the newer one cannot be read by the older -- so
    an unpinned binary is not one plan per machine, it is one machine locking
    every other machine out of the shared state. Saying so here is cheaper than
    discovering it from a colleague's failed `init`.
    """
    name = "Terraform"
    pinned = _pinned_terraform_version()
    terraform_path = shutil.which("terraform")
    if terraform_path is None:
        return CheckResult(
            name=name,
            required=False,
            ok=True,
            message=f"not on PATH (informational). The infrastructure scripts use the "
            f"pinned image hashicorp/terraform:{pinned} instead, so this is only worth "
            f"installing if you work in infra/ often.",
        )
    try:
        result = subprocess.run(
            [terraform_path, "version"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(
            name=name,
            required=False,
            ok=True,
            message=f"Terraform found at {terraform_path}, version undetermined ({exc})",
        )
    version = _parse_version((result.stdout or "") + (result.stderr or ""))
    version_str = ".".join(str(part) for part in version) if version else "unknown"
    if version_str != pinned:
        return CheckResult(
            name=name,
            required=False,
            ok=False,
            message=f"Terraform {version_str} found, and this project pins {pinned}. The "
            f"scripts will use the pinned image rather than this binary. State written by a "
            f"newer Terraform cannot be read by an older one, which is why the pin is not a "
            f"preference.",
        )
    return CheckResult(
        name=name,
        required=False,
        ok=True,
        message=f"Terraform {version_str} found, matching the pin",
    )


def _pinned_terraform_version() -> str:
    """The version `scripts/_lib.sh` pins. Read, never restated.

    A second copy of a version number in this file is a second thing to update,
    and the one that is forgotten is the one that reports a mismatch that is not
    real.
    """
    lib = (pathlib.Path(__file__).resolve().parent / "_lib.sh").read_text(encoding="utf-8")
    found = re.search(r'TERRAFORM_VERSION="([^"]+)"', lib)
    return found.group(1) if found else "unknown"


CHECKS: list[Check] = [
    check_python_version,
    check_uv,
    check_docker,
    check_docker_compose,
    check_node,
    check_terraform,
]


def run_preflight(checks: list[Check] = CHECKS) -> int:
    """Run each check, print a human-readable report, and return the
    process exit code.

    Exit code is 1 if any `required=True` check failed, 0 otherwise. A
    failing `required=False` check (e.g. missing Docker) is reported but
    never causes a nonzero exit code (Requirement 3.4).
    """
    results = [check() for check in checks]

    print("Preflight check results:")
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        kind = "required" if result.required else "informational"
        print(f"  [{status}] ({kind}) {result.name}: {result.message}")

    failed_required = [r for r in results if r.required and not r.ok]

    print()
    if failed_required:
        print("Environment not ready — missing or unmet required prerequisites:")
        for result in failed_required:
            print(f"  - {result.name}: {result.message}")
        return 1

    print("Environment ready — all required prerequisites are present.")
    return 0


if __name__ == "__main__":
    sys.exit(run_preflight())
