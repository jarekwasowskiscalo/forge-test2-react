#!/usr/bin/env bash
# Remove what can be regenerated. Never touches anything git tracks.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: clean.sh [--all]

  (no argument)  caches and build output: __pycache__, .pytest_cache, .ruff_cache,
                 .mypy_cache, app/static, frontend/dist, openapi.json, reports --
                 including the reports the deleted behave suite left behind
  --all          ...and everything that takes minutes to rebuild: .venv,
                 frontend/node_modules, the leftover e2e-test-app/ tree, and the
                 database container with its volume

Nothing here is tracked by git. If a file you care about disappears, it was
generated and something is wrong with .gitignore, not with this script.
TEXT
}

deep=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --all) deep=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

step "Removing caches"
find . -type d -name __pycache__ -not -path "./.git/*" -not -path "*/node_modules/*" -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
ok "caches"

step "Removing build output"
# The deleted behave suite's output tree is gone with the suite; nothing here has to
# remember it any more. What stays is the rule:
# build output of anything that still exists, which is exactly why it needed
# naming: those files outlive the tree, their <system-out> blocks carry whole
# request and response bodies, and nothing cleaned them once the tree they lived
# in stopped being part of the repository. `.sdd/reports` and `.sdd/logs` are the
# same argument for the SDD framework: derivable, machine-local, and able to
# quote somebody's field value out of a failing assertion.
rm -rf app/static frontend/dist openapi.json e2e/reports \
    .sdd/reports .sdd/logs
ok "build output"

if [ "$deep" -eq 1 ]; then
    step "Removing environments"
    # The third one is the virtualenv of the suite `e2e/` replaced, along with
    # whatever else is left of that tree. It was dropped from this list in the
    # same commit that deleted the tree from git, so a developer upgrading across
    # that commit kept both forever with no script that touched them.
    rm -rf .venv frontend/node_modules e2e-test-app
    ok "environments -- next run reinstalls them"

    step "Removing the database container and its volume"
    require_docker
    docker compose down -v >/dev/null 2>&1 || true
    ok "database"
fi

summary "Clean" 0
