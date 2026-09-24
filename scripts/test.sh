#!/usr/bin/env bash
# Run the tests. With no argument, all of them.
#
# Three suites answer three different questions, and they need four different
# things to be true of the machine, so each one says what it needs before it
# starts rather than failing halfway through with a buried connection error.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: test.sh [backend|unit|integration|fitness|tooling|frontend|e2e|ui|all] [extra arguments...]

  (no argument)  every suite, in the order that fails fastest
  backend        pytest over tests/unit, tests/integration and tests/tooling --
                 starts its own throwaway Postgres via testcontainers. NOT
                 tests/fitness: that is a suite of its own, with its own junit
  unit           the rules that touch no database -- seconds, and no Docker
  --coverage     anywhere in the arguments of a backend suite: measure and print,
                 never gate
  integration    services, migrations and the HTTP contract over real storage
  fitness        the detectors that read this repository's own source as text --
                 its own suite, no database, and never inside `backend`
  tooling        the scripts and the end-to-end harness
  frontend       vitest
  e2e            the black box: HTTP scenarios (pytest-bdd) plus the UI smoke
                 (Playwright), one gate, one junit, against a running
                 application (started if needed, SPA rebuilt when it is missing
                 or older than its sources)
  ui             the UI smoke alone -- same prerequisites, faster loop
  e2e --collect-only
                 collect the black box and stop: a .feature naming a step nothing
                 defines dies here in seconds, with no application, no database
                 and no Docker

Extra arguments are forwarded to the underlying runner, so
`test.sh backend -k guestbook` works. `test.sh frontend --watch` re-runs on
every save.

  --no-db        backend only, and only the tests that need no database.
                 This is what CI runs on the macOS leg.

Postgres is the only engine (spec/design/architecture.md § One engine), so the backend suite needs one. With no
Docker there is exactly one way to run it:

  APP_TEST_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/postgres
                 a Postgres you already have -- natively installed (brew, apt),
                 or someone else's container. Full fidelity, nothing skipped,
                 and no daemon asked for. It names a SERVER: each run creates
                 its own uniquely named, migrated database inside it and drops
                 it again when the run ends.
TEXT
}

# pytest, for either of the two suites it runs. The title is the suite's, so a
# fitness run is not announced as the backend it was taken out of.
run_pytest() {
    step "$1"
    shift
    # The reports directory, before the argument scan rather than inside it. CI passes
    # `--coverage` and `--junitxml=.sdd/reports/backend.junit.xml` together, so creating
    # it under `--coverage` worked -- and made the junit path depend on a flag that has
    # nothing to do with it. Drop `--coverage` alone and pytest died on a path it could
    # not open.
    mkdir -p .sdd/reports
    # Coverage is a report, never a verdict: no threshold, and nothing here fails
    # on a number. See the reasoning in pyproject.toml. Taken from any position,
    # because a suite name comes first and `--coverage` reads as an afterthought
    # wherever the caller puts it.
    local cov=()
    local rest=()
    for arg in "$@"; do
        if [ "$arg" = "--coverage" ]; then
            cov=(--cov --cov-report=term --cov-report="xml:.sdd/reports/coverage.xml")
        else
            rest+=("$arg")
        fi
    done
    set -- ${rest[@]+"${rest[@]}"}
    if [ "${1:-}" = "--no-db" ]; then
        shift
        info "no-database subset -- no Docker needed"
        uv run pytest --no-db ${cov[@]+"${cov[@]}"} "$@"
        return
    fi
    require_uv
    # A Postgres somebody else provisioned needs no daemon here. Asked BEFORE the
    # Docker demand, because demanding a container in order to reach a database that
    # is already running is this project refusing the one no-Docker route it has --
    # and the variable has been advertised in tests/conftest.py and
    # spec/design/testing.md the whole time this check stood in front of it.
    if [ -n "${APP_TEST_DATABASE_URL:-}" ]; then
        info "APP_TEST_DATABASE_URL names a Postgres -- using it; no Docker needed"
    else
        require_docker
        info "the suite starts its own Postgres container per session"
    fi
    uv run pytest ${cov[@]+"${cov[@]}"} "$@"
}

run_backend() { run_pytest "Backend tests (pytest)" "$@"; }
run_fitness() { run_pytest "Fitness tests (pytest)" --no-db tests/fitness "$@"; }

run_frontend() {
    step "Frontend tests (vitest)"
    ensure_frontend_deps
    # `npm run test` is `vitest run`, which forces a single pass -- forwarding
    # --watch to it does nothing at all. Route the intent to the watch script.
    if [ "${1:-}" = "--watch" ] || [ "${1:-}" = "-w" ]; then
        shift
        info "watch mode -- Ctrl+C to leave"
        (cd frontend && npm run test:watch -- "$@")
        return
    fi
    (cd frontend && npm run test -- "$@")
}

run_e2e() {
    # Both black-box trees by default -- one gate, one junit. `--only-ui` is the
    # internal switch behind `test.sh ui`: the same prerequisites and the same
    # application, with the HTTP scenarios left out for a faster loop.
    local trees=("e2e/suite" "e2e/ui")
    if [ "${1:-}" = "--only-ui" ]; then
        trees=("e2e/ui")
        shift
    fi
    step "End-to-end tests (${trees[*]})"
    require_uv

    # Before anything is started: a `.feature` that names a step nothing defines,
    # or a step module that does not import, should not cost ninety seconds of
    # application startup to discover. No test body runs here -- no application,
    # no database, no Docker.
    #
    # Collection alone does not prove every step is *bound*: pytest-bdd resolves
    # a step to its definition when the scenario runs. That check is
    # `tests/fitness/test_e2e_scenarios.py`, which needs nothing either and so runs in
    # the backend gate, in `check.sh --fast`, and on every platform.
    #
    # `--collect-only` stops here, with the collection printed: the one form of
    # "collect" article XII lets a worker type. The skills used to instruct
    # `uv run pytest ... --collect-only`, and the hook refused them at the RED proof.
    if [ "${1:-}" = "--collect-only" ]; then
        shift
        step "Collecting ${trees[*]} -- nothing runs, nothing starts"
        uv run pytest "${trees[@]}" --collect-only -q "$@"
        return
    fi
    if ! uv run pytest "${trees[@]}" --collect-only -q >/dev/null; then
        die "the scenarios do not collect -- see './scripts/test.sh e2e --collect-only'. Nothing was run."
    fi

    # The UI smoke enters screens, and a screen is the built SPA: without
    # `app/static/index.html` the catch-all answers 404 and every UI test fails
    # for the same absent reason. Built here, once, rather than discovered seven
    # times -- and skipped when the build that exists is still the build of these
    # sources, because `build.sh` costs tens of seconds and the smoke is meant to be
    # a loop.
    #
    # Freshness, not presence. This used to ask only whether `app/static/index.html`
    # existed, which made the smoke run against whatever bundle was lying there: on
    # 2026-09-16 it reported three UI failures against components that had already been
    # fixed, because the bundle predated the fix. The mirror image is worse -- a bundle
    # still holding the old, PASSING behaviour reports green for a screen nobody built --
    # and neither shape can be seen from the result. `build.sh --if-stale` owns the
    # comparison and says what it compared; the decision is not repeated here.
    #
    # Caught rather than inherited from `set -e`, because the one failure that matters
    # here deserves a sentence: `build.sh` exits 4 when a source was saved while the
    # compiler was running, and the bundle it produced is therefore already not a bundle
    # of these sources. Running the smoke against it anyway is precisely the hazard this
    # call was changed to remove, so nothing runs and the reason is said out loud.
    local build_rc=0
    "$REPO_ROOT/scripts/build.sh" --if-stale || build_rc=$?
    if [ "$build_rc" -ne 0 ]; then
        die "the SPA was not built from these sources, so anything the UI smoke said would be about the wrong code. Nothing was started and nothing was run -- run this command again."
    fi

    # Idempotent and quick when the browser is already there; a first run on a
    # fresh machine downloads Chromium once. Only Chromium -- spec/design/testing.md § The UI smoke in a browser.
    uv run playwright install chromium

    # The suite drives a running application over HTTP; it cannot start one
    # itself without becoming the thing it is testing. So: use the app that is
    # already up, or start one and take it down again afterwards.
    # Before anything else: the suite empties the target's database between
    # scenarios, so Postgres has to be up even when an application is already
    # answering. It can answer without one -- `/api/health` touches no
    # persistence layer.
    # One decision about which database, made here and inherited by the
    # application `start.sh` may be about to launch, so the suite and the
    # application cannot disagree about which one they mean.
    resolve_database_url

    # AFTER the decision, not before it. These two demand the means to START a
    # Postgres, and asking for them first meant a run that was going to use a
    # Postgres somebody else already had still required a daemon -- and, worse, still
    # ran `docker compose up`, which fails when the database it is about to honour is
    # a container from another checkout holding the same port.
    if [ "${APP_DB_EXTERNAL:-0}" != "1" ]; then
        require_docker
        ensure_db_running
    fi

    # The suite deletes every row it can reach, before every scenario, and
    # "the host reads as local" was never a statement about whether it may. An
    # SSH tunnel or a `kubectl port-forward` to a shared database looks exactly
    # like the compose container from inside a connection string. So the
    # permission is written into the database itself -- `COMMENT ON DATABASE`,
    # carrying this run's id -- and the harness refuses a database that does not
    # carry this run's mark.
    #
    # Minted here and never inherited: honouring an E2E_RUN_ID already in the
    # environment would let a value exported into a shell profile keep a stamp
    # from three weeks ago matching for ever, which is the freshness the harness
    # is checking. Seconds plus the pid, because the requirement is that an OLD
    # stamp stops matching, not that the value be unguessable.
    E2E_RUN_ID="$(date +%s)-$$"
    export E2E_RUN_ID
    #
    # WHO may stamp is the whole decision. A database this script provisioned is
    # disposable by construction. A DATABASE_URL somebody else set is not, and
    # this script has no way to find out -- so `--consent-required` makes the
    # Python side refuse unless E2E_ALLOW_REMOTE_RESET names that exact database.
    # `_lib.sh`'s rule that a supplied DATABASE_URL is never silently overridden
    # is untouched by this: the URL is honoured, or the run stops. It is never
    # swapped for another.
    local consent=()
    if [ "${APP_DB_EXTERNAL:-0}" = "1" ]; then
        consent=(--consent-required)
    fi
    uv run python scripts/e2e_database.py \
        --url "$DATABASE_URL" --run-id "$E2E_RUN_ID" ${consent[@]+"${consent[@]}"} ||
        die "the database was not marked disposable, so nothing was run and nothing was emptied."

    # The suite reads its own base URL, and it must be the port this script
    # actually started. Defaulted rather than overwritten: an operator pointing
    # the suite at a deployed application through TARGET_BASE_URL is telling it
    # something this script cannot know, and must win.
    export TARGET_BASE_URL="${TARGET_BASE_URL:-http://127.0.0.1:${APP_PORT}/api}"

    local started=0
    if app_is_up; then
        info "using the application already running on :$APP_PORT"
    else
        info "no application on :$APP_PORT -- starting one"
        # The logs land in .sdd/logs/ (gitignored), never in /tmp: /tmp is
        # POSIX-only and a temp cleaner's property, and a failing e2e run's
        # first artefact is exactly these files. The app itself writes a DEBUG
        # file alongside, so the run leaves something an agent can read.
        mkdir -p "$REPO_ROOT/.sdd/logs"
        local app_log="$REPO_ROOT/.sdd/logs/e2e-app.log"
        export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
        export LOG_FILE="${LOG_FILE:-$REPO_ROOT/.sdd/logs/app.log}"
        # There is no engine to state any more (spec/design/architecture.md § One engine): `start.sh` starts a
        # Postgres or stops, so the flag that used to forbid a fallback has
        # nothing left to forbid and was removed with it.
        #
        # `--port` forwarded so `APP_PORT=8090 ./scripts/test.sh e2e` works on a
        # machine where something else already holds the default. Without it the
        # started application binds 8080 while every poll here asks $APP_PORT.
        #
        # `--no-seed` because the black box owns the whole database of whatever it
        # runs against: `empty_world` truncates before EVERY scenario, so seed data
        # would be five POSTs that the first scenario then deletes. Harmless, and
        # pointless, and it would make a `start.sh` log read as though the suite
        # had found data it did not write.
        "$REPO_ROOT/scripts/start.sh" --port "$APP_PORT" --no-seed >"$app_log" 2>&1 &
        local app_pid=$!
        started=1
        # shellcheck disable=SC2064  # $app_pid must expand now, not at trap time
        trap "kill $app_pid 2>/dev/null || true" EXIT INT TERM

        local waited=0
        until app_is_up; do
            sleep 1
            waited=$((waited + 1))
            if [ "$waited" -ge 90 ]; then
                die "the application did not come up within 90s. See $app_log"
            fi
        done
        ok "application up after ${waited}s"
    fi

    # One runner, from the repository root: the features are
    # resolved from `__file__`, so there is no working directory to stand in and
    # no second interpreter to find. The report path is baked in rather than
    # left to the caller, so a developer's run and CI's produce the same
    # artifact in the same place.
    local status=0
    # `if !` rather than a bare call: under `set -e` a failing suite would abort
    # the function before the message below, and the operator would be left
    # wondering whether the application they started is still running.
    # `--session-timeout`: this suite also waits on an application and a browser
    # it started, so a per-test ceiling alone leaves the in-between -- fixtures,
    # resets, page loads -- able to hang the leg. Fifteen minutes is triple a
    # slow full run; the per-test 120s lives in pyproject.toml.
    if ! uv run pytest "${trees[@]}" --session-timeout=900 --junitxml=e2e/reports/junit.xml "$@"; then
        status=1
    fi

    # The census AFTER the report is written, and deliberately WITHOUT a
    # --junitxml of its own: it reads the file the line above just wrote and
    # must not replace it. It subtracts what the feature files declare from
    # what the runner collected -- the failure that is silent by construction,
    # where a renamed step drops two scenarios and every report downstream
    # still says green. Full runs only: a `ui`-only junit holds no scenarios
    # and the subtraction would convict the wrong thing. Its red fails this
    # gate even beside a green suite: gate.py's decide() charges a non-zero
    # runner with a green report to the gate itself.
    if [ "${#trees[@]}" -eq 2 ]; then
        if ! uv run python scripts/scenario_census.py; then
            status=1
        fi
    fi

    if [ "$started" -eq 1 ]; then
        info "stopping the application this run started (the EXIT trap does it)"
    fi
    return "$status"
}

case "${1:-all}" in
    -h|--help) usage; exit 0 ;;
    # `backend` and its no-database form leave tests/fitness to the `fitness` suite.
    # The two are declared apart in .specconf/stack.json § suites, and the engine
    # attributes a case to ONE suite: a fitness case in both junits would be read
    # as whichever report came last. An explicit path under tests/fitness is still
    # collected -- pytest never ignores a path it was handed on the command line.
    backend)   shift; run_backend "$@" --ignore=tests/fitness ;;
    frontend)  shift; run_frontend "$@" ;;
    e2e)       shift; run_e2e "$@" ;;
    ui)        shift; run_e2e --only-ui "$@" ;;
    --no-db)   shift; run_backend --no-db "$@" --ignore=tests/fitness ;;
    # The three groups that declare, by living where they live, that they need no
    # database. `--no-db` is passed rather than assumed: it is what stops the
    # session fixture provisioning a Postgres nobody is going to open.
    unit)        shift; run_backend --no-db tests/unit "$@" ;;
    fitness)     shift; run_fitness "$@" ;;
    tooling)     shift; run_backend --no-db tests/tooling "$@" ;;
    integration) shift; run_backend tests/integration "$@" ;;
    all)
        shift || true
        # Ordered by what a suite costs to run: the frontend needs no Docker, the
        # backend brings up a Postgres, and the black box additionally builds the SPA
        # and starts the application.
        #
        # Not "the cheapest FAILURE first", which this used to claim: `run_backend`
        # provisions the database in `pytest_configure`, so the unit tests do wait
        # behind the container. `./scripts/test.sh unit` is the fast loop -- seconds,
        # and no Docker at all.
        run_frontend
        run_fitness
        run_backend --ignore=tests/fitness
        run_e2e
        summary "All tests" 0
        ;;
    *) usage >&2; die "unknown suite: $1" ;;
esac
