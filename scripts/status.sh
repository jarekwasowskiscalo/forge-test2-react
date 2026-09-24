#!/usr/bin/env bash
# What is true right now: Docker, the app on :8080, build freshness, which
# database, the locks. Changes nothing.
#
# A thin wrapper so there is a script for it like there is for everything else.
# The probes live in scripts/app_status.py, standard library only, so it also
# runs on a machine where uv is not installed yet:
#
#     python3 scripts/app_status.py --json
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

case "${1:-}" in
    -h|--help)
        echo "usage: status.sh [--json]"
        echo
        echo "Reports what is running and what is stale: the app on :8080 (and whether"
        echo "it is THIS app), the frontend build vs its sources, Docker and Postgres,"
        echo "the dev ports, the gate lock, and where the logs are. Read-only; the"
        echo "advice lines name the script to run, never a raw command."
        echo
        echo "  --json    machine-readable, for the run-app skill"
        exit 0 ;;
esac

if command -v uv >/dev/null 2>&1; then
    exec uv run python scripts/app_status.py "$@"
fi
command -v python3 >/dev/null 2>&1 ||
    die "neither uv nor python3 is on PATH. Install Python 3.14: https://www.python.org/downloads/"
exec python3 scripts/app_status.py "$@"
