#!/usr/bin/env bash
# Stops everything start.sh may have started in Docker - Postgres, and the
# application container when `start.sh --container` put one there. Not a full
# teardown: containers and the data volume are kept, so a later start.sh is fast.
#
# On a machine with no usable Docker there is nothing to stop and that is not
# an error - see the branch below.
set -euo pipefail

# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

case "${1:-}" in
    -h|--help)
        cat <<'TEXT'
usage: stop.sh

Stops the Postgres container and, if `start.sh --container` or `--development`
started them, the application and Vite containers beside it. Both are kept, along with the data volume, so
the next start.sh is fast and your data is still there. To delete the data as
well: scripts/clean.sh --all.

With no usable Docker this does nothing and succeeds: there is no container to
stop, and Ctrl+C already stopped whatever was running on this machine.
TEXT
        exit 0
        ;;
esac

# Exiting 0 is the point, not laziness. A machine with no usable Docker may still
# be running this application against a Postgres of its own, so the paired
# teardown has to succeed there -- otherwise every wrapper, skill and agent that
# runs stop.sh reports a failed teardown on a machine that never had a container.
if ! docker_usable; then
    info "$DOCKER_UNUSABLE_REASON -- nothing to stop."
    info "a database this environment supplied is not this script's to stop either."
    exit 0
fi

# `--profile app` so the application container is included when there is one.
# Naming a profile that started nothing is not an error: compose stops what
# matches and says nothing about what does not exist.
step "Stopping the containers (docker compose stop)"
docker compose --profile app --profile dev stop
