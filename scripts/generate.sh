#!/usr/bin/env bash
# Regenerate the API types the frontend consumes, and commit the result.
#
# Generated from Python and committed as TypeScript, so a change to a Pydantic
# schema becomes a reviewable diff instead of a runtime surprise. CI runs this
# with --check and fails on a difference.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: generate.sh [--check]

  (no argument)  regenerate, then tell you what changed
  --check        fail if anything is out of date, change nothing (what CI runs)

Generated:
  frontend/src/api/schema.d.ts   <- the Pydantic schemas, via openapi.json

openapi.json itself is deliberately NOT committed: it is an intermediate, and a
generated file in git goes stale. CI rebuilds it before diffing the types.
TEXT
}

check_only=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --check) check_only=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

require_uv
ensure_frontend_deps

step "Dumping the OpenAPI document from the Pydantic schemas"
uv run python scripts/dump_openapi.py

if [ "$check_only" -eq 1 ]; then
    step "Checking the committed API types"
    (cd frontend && npm run gen:api:check)
    summary "Generate --check" 0
fi

step "Regenerating the API types"
(cd frontend && npm run gen:api)


if git diff --quiet -- frontend/src/api/schema.d.ts; then
    ok "already up to date -- nothing to commit"
else
    step "Changed:"
    git --no-pager diff --stat -- frontend/src/api/schema.d.ts
    info "commit these files with the change that caused them"
fi

summary "Generate" 0
