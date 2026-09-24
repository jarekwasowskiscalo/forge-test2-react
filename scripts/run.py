"""Cross-platform run entry point (Boundary: RunScript).

A single, platform-appropriate way to start the backend application,
invoked identically on Linux and macOS via `uv run scripts/run.py`.

Contains no application logic: it only parses optional --host/--port
arguments and delegates entirely to `app.main:app` via `uvicorn.run(...)`.
Relies on `uv run`'s own implicit `uv sync` (and its native error output
when the environment cannot be resolved) to satisfy the "clear failure if
the environment is not set up" requirement, rather than adding a custom
"is the environment set up" check here. The one narrow exception is the
`uvicorn` import itself: if it fails, that's the clearest, earliest signal
that dependencies were never installed, so it is caught below and reported
with an explicit "environment not set up" message (Requirement 2.4)
rather than surfacing as a bare traceback.
"""

import argparse
import sys
from pathlib import Path

try:
    import uvicorn
except ImportError as exc:
    print(
        f"error: environment not set up — run `uv sync` first (see README) [{exc}]",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# Project root (parent of this scripts/ directory). Running this file directly
# (e.g. `uv run scripts/run.py`) only puts this file's own directory on
# sys.path, not the project root, so `app.main:app` would otherwise fail to
# import regardless of the current working directory. `app_dir` is uvicorn's
# own supported mechanism for adding the app's location to sys.path before
# import, so this is configuration, not application logic.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the backend application.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host/interface to bind to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Restart the server on code changes (uvicorn --reload)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(PROJECT_ROOT),
    )


if __name__ == "__main__":
    main()
