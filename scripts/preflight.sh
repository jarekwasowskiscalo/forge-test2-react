#!/usr/bin/env bash
# Check this machine against what the project needs. Changes nothing.
#
# A thin wrapper so there is a script for it like there is for everything else.
# The checks themselves are in scripts/preflight.py, in Python and using only
# the standard library, so it also runs before uv exists:
#
#     python3 scripts/preflight.py
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

case "${1:-}" in
    -h|--help)
        echo "usage: preflight.sh"
        echo
        echo "Reports on Python, uv, Node and Docker. Exits non-zero if a required"
        echo "prerequisite is missing or the wrong version. Installs nothing."
        exit 0 ;;
esac

# `uv run` when uv is available (it provisions the right Python), plain python3
# otherwise -- the case this check exists for is precisely a machine that has
# not been set up yet.
if command -v uv >/dev/null 2>&1; then
    exec uv run python scripts/preflight.py "$@"
fi
command -v python3 >/dev/null 2>&1 ||
    die "neither uv nor python3 is on PATH. Install Python 3.14: https://www.python.org/downloads/"
exec python3 scripts/preflight.py "$@"
