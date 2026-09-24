#!/usr/bin/env bash
# Install this project's dependencies. Does not install uv, Docker or Node.
#
# The split from install.sh is deliberate: that one changes your machine, this
# one only changes this directory. On a machine that already has the toolchain,
# this is the whole of "get me ready to work".
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

case "${1:-}" in
    -h|--help)
        cat <<'TEXT'
usage: setup.sh

Installs, in order:
  - the Python environment (uv sync -- exactly the pinned versions,
    including the e2e suite, which is a dependency group rather than a
    virtualenv of its own)
  - frontend dependencies (npm ci)

Needs uv, Node and Docker to already be present. Run preflight.sh to find out,
or install.sh to have them installed for you.
TEXT
        exit 0 ;;
    "") ;;
    *) die "setup.sh takes no arguments" ;;
esac

require_uv
step "Python environment (uv sync)"
uv sync
ok "$(uv run python --version)"

ensure_frontend_deps
ok "frontend dependencies"

step "Next"
info "scripts/start.sh   run the application"
info "scripts/test.sh    run every test suite"
info "scripts/help.sh    everything else"
summary "Setup" 0
