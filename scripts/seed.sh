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
# Two lists are filled, each on its own condition: the guest book gets its welcome
# entries when it holds none, and the to-do list gets its example tasks when it
# holds none -- whatever the other one holds. An example task is added not done
# and then marked through the marking route when the corpus says it is done, the
# way a person's task gets there.
#
# Safe to run unconditionally, and that is the point: it refuses production, and
# it skips a list that already holds something -- a guest book with entries, a
# to-do list with a task. "Seed every new environment" and "run on every deploy"
# are therefore the same instruction.
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

It fills two lists from golden-set/seed/, each on its own condition:

  guest book     its welcome entries, when it holds no entry -- whatever the
                 to-do list holds
  to-do list     its example tasks, when it holds no task -- whatever the guest
                 book holds. Each is added not done, and the done one is then
                 marked, the way a person's task gets there.

Two refusals make this safe to wire into a deployment:

  * It will not seed production. It asks /api/health, which reports the
    environment the deployment was given, and stops there -- before it reads
    either list.
  * It will not seed a list that already holds something -- a guest book with
    entries, a to-do list with a task -- and it asks each list on its own, so it
    is idempotent and every run after the first costs one GET per list.

The welcome entries belong to the guest book, an example that may be deleted
(CLAUDE.md); the example tasks belong to the to-do list, which stays. The two
halves of golden-set/ and the rules each owes: golden-set/README.md.
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
