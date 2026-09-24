#!/usr/bin/env bash
# Fill an environment with the seed corpus, so its screen is worth looking at.
#
# `golden-set/seed/` is one of the corpus's two halves: what a freshly created
# environment opens with, as against `golden-set/fixtures/`, which the suites
# read and assert about. This script is the whole interface to that half --
# `start.sh`, `preview.sh` and `deploy.sh` all call it rather than reaching for
# the Python behind it, so there is one definition of "seed an environment"
# instead of three copies that drift (constitution, article XII).
#
# Safe to run unconditionally, and that is the point: it refuses production, and
# it skips a guest book that already has entries. "Seed every new environment"
# and "run on every deploy" are therefore the same instruction.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: seed.sh [--base-url URL] [--boundary]

  (no argument)  seed the application on this machine (APP_PORT, default 8080)
  --base-url URL seed something else -- a preview, a stage. Include the /api
                 prefix and no trailing slash.
  --boundary     also post the fixture entries that sit exactly on the published
                 limits. For reviewing the SCREEN rather than the flow; no
                 deployment passes it.

Two refusals make this safe to wire into a deployment:

  * It will not seed production. It asks /api/health, which reports the
    environment the deployment was given, and stops there.
  * It will not seed a guest book that already has entries, so it is idempotent
    and every run after the first costs one GET.

The corpus belongs to the guest book, and so does this: deleting the example
deletes golden-set/ and this script with it (CLAUDE.md). The two halves and the
rules each owes: golden-set/README.md.
TEXT
}

base_url=""
boundary=()

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --base-url) shift; [ $# -gt 0 ] || die "--base-url needs a URL"; base_url="$1" ;;
        --boundary) boundary=(--boundary) ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

require_uv

# The default is derived from APP_PORT rather than written down, for the same
# reason the health URL is: the port is one variable, and a second copy of 8080
# here would be right until somebody ran on another port.
if [ -z "$base_url" ]; then
    base_url="http://127.0.0.1:${APP_PORT}/api"
    app_is_up || die "nothing is answering at $APP_HEALTH_URL.
    Start the application first: ./scripts/start.sh"
fi

step "Seeding $base_url from the seed corpus"
uv run python scripts/seed_golden_set.py --base-url "$base_url" "${boundary[@]+"${boundary[@]}"}"

summary "Seed" 0
