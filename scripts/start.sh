#!/usr/bin/env bash
# One-command local dev entry point (Linux/macOS): brings up the database,
# applies migrations, then runs the app. Does NOT install uv/Python/Docker
# itself (see README) - those remain manual, one-time prerequisites; this
# script only orchestrates what already-installed tooling does.
#
# The database is Postgres via docker-compose, and only Postgres (spec/design/architecture.md § One engine).
# With no usable Docker this script stops and says what to do about it, rather
# than substituting a second engine that behaves differently. See
# `resolve_database_url` in _lib.sh, which is the one place this is decided.
#
# --development (--dev) additionally starts the Vite dev server (in Docker,
# via docker-compose.yml's `frontend` service -- so the host never needs a
# matching Node version) and runs the backend with --reload. It uses port
# 8000 for the backend in that mode -- not the 8080 used otherwise --
# because frontend/vite.config.ts's dev proxy is hardcoded to localhost:8000
# (see README's "Developing" section). Without Docker that container is not
# available, so Vite runs on this machine instead.
#
# The flag matrix below is asserted by `scripts/hygiene.sh` and by CI's `scripts`
# job: every mode this script advertises has to stay reachable, because a mode
# that quietly disappears is one every skill and document still names.
set -euo pipefail

# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

# Answered before anything else. `--help` must cost nothing and require
# nothing: this script used to run `uv sync` first, so asking it what it does
# failed with "uv: command not found" on exactly the machine most likely to be
# asking -- one that is not set up yet. Sourcing _lib.sh above does not break
# that: it defines functions and sets paths, and checks nothing.
case "${1:-}" in
    -h|--help)
        cat <<'TEXT'
usage: start.sh [--development|--container] [--port N] [uvicorn arguments...]

  (no argument)   Postgres via docker compose, migrations, then the app on :8080.
                  The application runs on THIS machine, from this working tree.
  --development   ...and the Vite dev server with hot reload on :5173, with the
    --dev         backend on :8000 (which is the port vite.config.ts proxies to)
  --container     everything in Docker instead: the image, its migration step and
                  Postgres, on :8080. Nothing but Docker is needed -- no uv, no
                  Node, no Python. This is the in-house way to run it, and the
                  way to see the artefact CI builds rather than your tree.
  --port N        serve on N instead
  --no-seed       leave the guest book empty. By default a guest book that has
                  no entries is filled from golden-set/seed/ once the application
                  answers, so a fresh clone opens on a screen worth looking at;
                  a book that already has entries is never touched.

A DATABASE_URL already set in the environment is honoured and used as it stands;
this script then starts nothing and assumes that database is already up.

Postgres is the only engine (spec/design/architecture.md § One engine). With no usable Docker and no
DATABASE_URL of your own, this stops rather than running on something else.

Runs in the foreground. Ctrl+C stops the application and leaves Postgres up;
scripts/stop.sh stops that too, keeping the data.
TEXT
        exit 0
        ;;
esac

# Arguments first. --development/--dev and --port are consumed here; everything
# else is forwarded to run.py, whose argparse rejects what it does not know.
#
# `--port` is consumed rather than forwarded, and that is the repair for a flag
# that only half worked: forwarded, it reached uvicorn and nothing else, so the
# health poll in `_lib.sh` still asked 8080 and every caller that waits for the
# application -- `test.sh e2e` most of all -- waited on a port nothing was
# serving. Setting `APP_PORT` makes one value decide both.
dev_mode=0
container_mode=0
no_seed=0
want_port=""
args=()
for arg in "$@"; do
    if [ -n "$want_port" ]; then
        case "$arg" in
            ''|*[!0-9]*) die "--port takes a number, got: $arg" ;;
        esac
        APP_PORT="$arg"
        want_port=""
        continue
    fi
    case "$arg" in
        --development|--dev) dev_mode=1 ;;
        --container) container_mode=1 ;;
        --no-seed) no_seed=1 ;;
        --port) want_port=1 ;;
        *) args+=("$arg") ;;
    esac
done
[ -n "$want_port" ] && die "--port needs a number after it."
[ "$dev_mode" -eq 1 ] && [ "$container_mode" -eq 1 ] &&
    die "--development and --container contradict each other: one runs Vite against your
    working tree, the other runs a built image that has no working tree in it."

# Re-derived, because `_lib.sh` computed it from the default before the flag was
# read. One value decides the port; this is where it stops being two.
export APP_PORT
APP_HEALTH_URL="http://127.0.0.1:${APP_PORT}/api/health"

#: Fill the guest book from `golden-set/seed/` once the application answers.
#
# In the background and behind a poll, because the two paths that serve the
# application never come back: the plain one `exec`s uvicorn and the development
# one hands the terminal to Vite. Seeding before the poll would be seeding
# something that is not there yet.
#
# `seed.sh` carries the judgement -- it refuses production and skips a guest book
# that already has entries -- so this decides only WHEN to ask, never whether.
# Failure is a printed line: an empty guest book is a worse start than a full
# one, and neither is a reason not to have started.
#
# Bounded rather than `while true`: a run stopped with Ctrl+C before the
# application answered would otherwise leave a poller behind for the life of the
# terminal.
seed_when_up() {
    local base_url="$1"
    (
        # `app_is_up` rather than a curl of our own: it already falls back to
        # python3 on a machine without curl, and a second probe here would be a
        # second answer to "is it up". It reads the global, so the override is
        # made inside this subshell and reaches nothing else.
        APP_HEALTH_URL="${base_url}/health"
        # `_` rather than a named counter: this poll is silent, so there is
        # nothing to print the number into, and shellcheck is right that a
        # variable set and never read is a variable somebody meant to use.
        for _ in $(seq 1 60); do
            if app_is_up; then
                "$REPO_ROOT/scripts/seed.sh" --base-url "$base_url" >/dev/null 2>&1 ||
                    warn "the seed corpus did not go in; the application is running"
                return 0
            fi
            sleep 1
        done
    ) &
}

# --------------------------------------------------------------------------- #
# --container: hand the whole thing to compose and stop here
# --------------------------------------------------------------------------- #
#
# Before `resolve_database_url`, deliberately. In this mode the database lives
# inside the compose network and is reached as `db:5432` -- a DATABASE_URL
# resolved for THIS machine would name localhost and a published port, which is
# the wrong address from inside a container and the wrong thing to export.
if [ "$container_mode" -eq 1 ]; then
    require_docker
    step "Building the image and starting Postgres, the migration and the application"
    info "everything runs in Docker: this machine needs no uv, no Node and no Python"
    # `--wait` blocks until the healthchecks pass, so when this returns the
    # application is answering rather than merely started. `migrate` exits, and
    # compose treats a completed one-shot service as satisfied rather than
    # unhealthy.
    APP_PORT="$APP_PORT" docker compose --profile app up --build --wait
    ok "the application answers on http://127.0.0.1:${APP_PORT}"
    # Inline here, unlike the two paths below: `--wait` has already blocked until
    # the healthchecks passed, so there is nothing to poll for and this script
    # still owns its terminal.
    #
    # Guarded on uv, and the guard is this mode's promise rather than caution:
    # the line above says this machine needs no uv, no Node and no Python, and
    # `seed.sh` needs uv. Letting it fail and warning would keep the promise in
    # the letter and break it in the spirit -- every container run on a machine
    # without uv would print a warning about something it was told it did not
    # need. So the seeding is skipped and SAID to be skipped: an empty guest book
    # somebody was told about is a different thing from one that surprises them.
    if [ "$no_seed" -eq 0 ]; then
        if command -v uv >/dev/null 2>&1; then
            "$REPO_ROOT/scripts/seed.sh" --base-url "http://127.0.0.1:${APP_PORT}/api" ||
                warn "the seed corpus did not go in; the application is running"
        else
            info "not seeded: the seeder needs uv, which this mode does not ask for"
            info "to fill it later: ./scripts/seed.sh (needs uv), or add entries on the screen"
        fi
    fi
    info "logs:  docker compose --profile app logs -f app"
    info "stop:  ./scripts/stop.sh"
    exit 0
fi

# Decided before anything is pulled, started or migrated, so there is exactly
# one decision point and it comes first.
resolve_database_url

# With a DATABASE_URL supplied from outside, this script starts no compose
# services at all -- including the `frontend` one -- so Vite has to run on this
# machine. That needs no configuration: vite.config.ts's proxy already defaults
# to localhost:8000, which is where the backend below is; VITE_API_PROXY_TARGET
# exists only because inside a container localhost is the container. Node is
# checked, never installed: `npm ci` from a start script is how a lockfile gets
# updated by something nobody asked to install, and _lib.sh states that rule for
# every script here.
#
# Resolved now rather than in the dev branch below, so an operator with no Node
# learns it immediately instead of after `uv sync` and a migration run.
frontend_mode="compose"
if [ "$dev_mode" -eq 1 ] && [ "${APP_DB_EXTERNAL:-0}" = "1" ]; then
    if command -v npm >/dev/null 2>&1 && [ -d frontend/node_modules ]; then
        frontend_mode="host"
    else
        frontend_mode="none"
        warn "no Vite dev server: the frontend runs in Docker in this mode, and there is no Docker."
        if command -v npm >/dev/null 2>&1; then
            info "frontend dependencies are missing -- run scripts/setup.sh, then: cd frontend && npm run dev"
        else
            info "install Node 22 or newer (https://nodejs.org/) and run scripts/setup.sh, then: cd frontend && npm run dev"
        fi
        info "it proxies /api to :8000 already, so there is nothing to configure"
    fi
fi

step "Syncing Python environment (uv sync)"
uv sync

# A local run always leaves a file an agent can read after the process is gone.
# The container stays console-only (`docker logs`); this default is for the
# developer's and the pipeline's machine. LOG_FILE= (empty) disables it.
if [ -z "${LOG_FILE+x}" ]; then
    mkdir -p "$REPO_ROOT/.sdd/logs"
    export LOG_FILE="$REPO_ROOT/.sdd/logs/app.log"
fi

# `APP_DB_EXTERNAL` as well as the mode: a Postgres this environment supplied is
# not ours to start, stop or recreate. `resolve_database_url` above has already
# honoured it and said so out loud, and composing one up regardless contradicts that
# in the one case where it matters -- a container from another checkout holding 5432,
# where `docker compose up` does not merely do nothing but FAILS on the port bind and
# takes the whole run with it.
#
# Spelled here rather than left to `ensure_db_running`, which this block predates and
# bypasses: it is a third copy of "start the database" and the two others already
# agree. Merging them is a bigger change than this one.
if [ "${APP_DB_EXTERNAL:-0}" != "1" ]; then
    step "Starting Postgres (docker compose up -d --wait)"
    docker compose up -d --wait
fi

step "Applying database migrations (alembic upgrade head)"
uv run alembic upgrade head

if [ "$dev_mode" -eq 0 ]; then
    step "Starting the application"
    [ "$no_seed" -eq 0 ] && seed_when_up "http://127.0.0.1:${APP_PORT}/api"
    exec uv run scripts/run.py --port "$APP_PORT" ${args[@]+"${args[@]}"}
fi

step "Starting backend with hot reload (:8000)"
uv run scripts/run.py --port 8000 --reload ${args[@]+"${args[@]}"} &
backend_pid=$!

# :8000 rather than APP_PORT -- in this mode that is where the backend is, and
# vite.config.ts proxies to it. The seeder talks to the API directly, so it wants
# the backend's port and not the one the browser uses.
[ "$no_seed" -eq 0 ] && seed_when_up "http://127.0.0.1:8000/api"

# One cleanup for all three frontend modes rather than one per branch: a
# `cleanup` defined inside a branch reads to shellcheck as unreachable (SC2317),
# and the thing it has to guarantee is the same either way -- stopping the
# frontend must not leave an orphaned backend holding :8000, which the next run
# would then fail to bind.
cleanup() {
    step "Stopping backend (pid $backend_pid)"
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
    if [ "$frontend_mode" = "compose" ]; then
        docker compose --profile dev stop frontend >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

case "$frontend_mode" in
    compose)
        step "Starting frontend dev server in Docker with hot reload (:5173)"
        docker compose --profile dev up --build frontend
        ;;
    host)
        # No `--host`, unlike the compose command above: 0.0.0.0 is what makes a
        # published container port reachable, and on this machine it would just
        # put the dev server on the LAN.
        step "Starting frontend dev server on this machine with hot reload (:5173)"
        (cd frontend && npm run dev)
        ;;
    *)
        info "backend only -- Ctrl+C to stop it"
        wait "$backend_pid"
        ;;
esac
