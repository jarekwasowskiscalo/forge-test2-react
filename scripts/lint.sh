#!/usr/bin/env bash
# Static checks: everything that reads the code without running it.
#
# All of them run even if an early one fails, and the failures are listed at the
# end. Stopping at the first would mean four round trips to find four problems.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: lint.sh [--fix]

  (no argument)  report problems, change nothing
  --fix          also apply what can be fixed automatically:
                 ruff's safe fixes, ruff format, and eslint --fix

Checks run: ruff, ruff format, mypy (strict), eslint, tsc.
TEXT
}

fix=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --fix) fix=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

require_uv
ensure_frontend_deps

failed=()
run() {
    local label="$1"; shift
    step "$label"
    if "$@"; then ok "$label"; else failed+=("$label"); fi
}

if [ "$fix" -eq 1 ]; then
    run "ruff (with fixes)"   uv run ruff check --fix .
    run "ruff format"         uv run ruff format .
else
    run "ruff"                uv run ruff check .
    run "ruff format --check" uv run ruff format --check .
fi

# No file list: `files` in pyproject.toml is the single answer to what is
# type-checked, and ci.yml has always run mypy bare. The two agreed only by
# coincidence, and the coincidence ended the moment `files` grew `e2e` -- which
# would have type-checked the suite in CI and not here, the exact "green
# locally, red in CI" this script exists to prevent.
run "mypy (strict)" uv run mypy

if [ "$fix" -eq 1 ]; then
    run "eslint (with fixes)" bash -c 'cd frontend && npx eslint . --fix'
else
    # --max-warnings 0 to match CI. A warning nobody has to fix is a warning
    # everybody learns to scroll past.
    run "eslint" bash -c 'cd frontend && npm run lint -- --max-warnings 0'
fi

run "TypeScript" bash -c 'cd frontend && npm run typecheck'

if [ ${#failed[@]} -gt 0 ]; then
    printf '\n%sFailed:%s %s\n' "$_C_RED" "$_C_OFF" "${failed[*]}" >&2
    summary "Lint" 1
fi
summary "Lint" 0
