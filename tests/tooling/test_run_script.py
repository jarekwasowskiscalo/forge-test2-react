"""Integration tests for the cross-platform run entry point (Boundary: RunScript).

Unlike the rest of this suite (which drives `app.main:app` in-process via
FastAPI's `TestClient`), `scripts/run.py` is the actual cross-platform entry
point a developer or CI invokes from a shell (`uv run scripts/run.py`). The
thing under test here is process startup, argument parsing, and real port
binding -- none of which a `TestClient` exercises -- so these tests launch
`scripts/run.py` as a real subprocess.

Placed alongside the rest of the project's tests (not a separate
`scripts/tests/` tree) because this repository runs a single unified
`uv run pytest` command (see design.md's Testing Strategy / E2E section,
and this feature's own task list, which lists "an automated test suite
run" -- singular -- as the observable). Splitting tooling tests into a
second pytest root would require a second invocation and second config,
which nothing in the spec calls for.

Two contracts are held here: `uv run scripts/run.py` starts the backend
application and a request against it succeeds once the environment is set
up correctly; and against an environment that has not been set up (here:
`uvicorn` unimportable) the entry point fails with a message identifying
the environment as not set up, rather than starting in a partially working
state.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from tests._repo import REPO_ROOT

PROJECT_ROOT = REPO_ROOT
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "run.py"

READY_TIMEOUT_SECONDS = 5.0
READY_POLL_INTERVAL_SECONDS = 0.15


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    """Stop `uv run scripts/run.py` and the uvicorn it spawned.

    `terminate()` signals the `uv` wrapper only, and that is enough here: uv
    forwards SIGTERM to its child. A leaked uvicorn would not fail this test --
    it would fail the next one, on a port it is still holding.
    """
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _find_free_port() -> int:
    """Bind to port 0 to let the OS assign a free port, then release it.

    There is an inherent (very small) race between releasing the socket
    here and the subprocess binding it, but this is the standard
    lightweight way to pick a free port for a test without hard-coding one
    that might collide with another service on the machine.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(port: int, process: subprocess.Popen) -> None:
    """Poll `/api/health` until it responds or the timeout elapses.

    Polls in short intervals rather than sleeping once for a fixed
    duration, so the test is both fast on a healthy machine and resilient
    to slower CI startup times, without being flaky either way.
    """
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(
                "scripts/run.py exited early with return code "
                f"{process.returncode} before becoming ready"
            )
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/health", timeout=0.5
            ) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last_error = exc
        time.sleep(READY_POLL_INTERVAL_SECONDS)
    raise AssertionError(
        f"scripts/run.py did not become ready on port {port} within "
        f"{READY_TIMEOUT_SECONDS}s (last error: {last_error!r})"
    )


def test_run_script_starts_backend_and_serves_health() -> None:
    """A correctly set-up environment starts the app.

    Launches `uv run scripts/run.py --port <free port>` as a real
    subprocess (inheriting the current environment, which already has
    `uv` on PATH -- the same way a developer or CI would invoke it),
    waits for the health endpoint to respond, and asserts the documented
    success payload.
    """
    port = _find_free_port()
    process = subprocess.Popen(
        ["uv", "run", "scripts/run.py", "--port", str(port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready(port, process)

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
            assert response.status == 200
            #: Parsed rather than compared byte for byte: the body also names the
            #: environment and the release, and what this test is about is that
            #: run.py brought a server up that answers at all.
            assert json.loads(response.read())["status"] == "ok"
    finally:
        _terminate_tree(process)


def test_run_script_fails_clearly_when_environment_not_set_up() -> None:
    """A not-set-up environment fails with an explicit message.

    Simulates "environment not set up" by invoking `scripts/run.py` with
    this test process's own interpreter (`sys.executable`, guaranteed to
    exist and to be the one this suite runs under -- unlike a hardcoded
    `python3`, which may resolve to a different install) plus the `-S` flag.
    `-S` suppresses the interpreter's automatic `import site` on startup,
    which is what makes a venv's installed packages (including `uvicorn`)
    importable in the first place; without it, `import uvicorn` fails
    while the stdlib remains fully available. This works identically on
    Linux and macOS with no PATH-layout or well-known-location assumptions, so
    the scenario is exercised on every CI leg.

    Under that condition `import uvicorn` fails, which is exactly the
    condition `scripts/run.py`'s narrow `try/except ImportError` is meant
    to catch and report clearly instead of a bare
    traceback.
    """
    result = subprocess.run(
        [sys.executable, "-S", str(RUN_SCRIPT), "--port", str(_find_free_port())],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert "environment not set up" in result.stderr
