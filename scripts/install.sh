#!/usr/bin/env bash
# Bootstraps the whole dev environment on a fresh Linux/macOS machine in one
# shot: installs uv (if missing), installs Docker (if missing, via
# _install-docker.sh), installs the project's Python + dependencies via
# `uv sync`, then hands off to start.sh to bring up Postgres, migrate, and
# run the app.
#
# This DOES modify your system (installs uv, installs Docker) - see
# _install-docker.sh for what that specifically entails.
set -euo pipefail

# The same library every other task script uses: `step`, `die`, REPO_ROOT.
# This script used to be the one exception -- its own `cd`, its own "==> ",
# its own error printing -- on the theory that a bootstrap must not depend on
# anything. `_lib.sh` checks nothing at source time, so the exception bought
# nothing and cost a second spelling of every message.
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

case "${1:-}" in
    -h|--help)
        cat <<'TEXT'
usage: install.sh [start.sh arguments...]

The only script here that modifies your machine. In order:
  1. install uv, pinned to the version CI runs (inside pyproject.toml's range), if missing
  2. install Docker, if missing (see _install-docker.sh for exactly what that does)
  3. uv sync -- the project's Python and its dependencies
  4. hand off to start.sh: Postgres, migrations, the application

Postgres is the only engine this application runs on (spec/design/architecture.md § One engine), so step 2 is
not optional. A machine that cannot have Docker can still work here, but it needs
a Postgres of its own: set DATABASE_URL (and APP_TEST_DATABASE_URL for the tests)
and use setup.sh instead of this script.

Everything is forwarded to start.sh, so its flags work here too.

On a machine that already has uv, Docker and Node, use setup.sh instead: it
installs the project's dependencies and touches nothing else.
TEXT
        exit 0
        ;;
esac

#: One version inside the range `[tool.uv] required-version` allows, and the SAME one
#: both workflows install (`UV_VERSION`). Three files, one answer.
#:
#: They used to give three different ones: the constitution said `==0.12.0`,
#: pyproject.toml said `>=0.12,<0.13` and argued against the exact pin by name, CI ran
#: 0.12.5, and the comment below asserted pyproject required 0.12.0 exactly -- which it
#: has never said. A false premise in a comment is worse than none: the next reader
#: fixes the file the comment blames.
UV_PIN="0.12.5"

step "Checking for uv (pinned to ${UV_PIN})"
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing..."
    # A version, not `latest`: uv is pre-1.0 and minor releases break, so a fresh
    # clone that installs whatever is current can fail its very first `uv sync` with
    # a required-version error -- on a machine where nothing has gone wrong yet, which
    # is the worst possible first impression. Reproducibility itself is `uv.lock`'s
    # job; this line only has to land inside the range pyproject.toml accepts.
    curl -LsSf "https://astral.sh/uv/${UV_PIN}/install.sh" | sh
    # The official installer places uv in ~/.local/bin (or ~/.cargo/bin on
    # older versions) but that won't be on PATH yet in this same process.
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if ! command -v uv >/dev/null 2>&1; then
        die "uv was installed but is still not on PATH. Open a new terminal and re-run this script."
    fi
fi
info "uv found at $(command -v uv) ($(uv --version))"

step "Checking for Docker"
if ! ./scripts/_install-docker.sh; then
    die "Docker is not ready yet (see message above). Follow its instructions and
       re-run this script. If this machine cannot have Docker, point DATABASE_URL
       at a Postgres you already have and run ./scripts/setup.sh instead."
fi

step "Installing Python + project dependencies (uv sync)"
uv sync

step "Environment ready. Starting Postgres, migrating, and running the app."
exec ./scripts/start.sh "$@"
