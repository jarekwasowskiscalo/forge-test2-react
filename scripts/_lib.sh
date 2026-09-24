#!/usr/bin/env bash
# Shared helpers for every script in this directory.
#
# Sourced, never executed: `source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"`.
#
# It exists so a task script is the task and nothing else. Before it, each
# script repeated the same twenty lines of "is Docker installed, and is the
# daemon answering" -- and they had already drifted apart once, which is how the
# test suite ended up with a check `start.sh` did not have.
#
# Everything below is a *check*, never an install. Installing prerequisites
# happens in exactly one place, `install.sh`, and only when a human asked for it.
#
# THE ONE SHELL OPTION THIS FILE SETS ITSELF, and why it is one rather than three.
# Every executed script here opens with `set -euo pipefail`; this file was the one of
# twenty-seven that declared nothing, which left its own pipelines answering with
# whatever the caller had decided. `pipefail` is asserted, because without it
# `producer | grep` reports grep's verdict for a producer that never ran. `-e` and
# `-u` stay the executed script's: this file is SOURCED, and errexit in a shell that
# sourced it to try a helper by hand would end that shell at the first non-zero.
set -o pipefail

# The repo root, whichever directory the caller was standing in. Derived from
# this file's own path, never from $PWD: a script clicked from a file manager
# starts in the user's home directory, and one run from a skill starts wherever
# the agent happened to be.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

#: The shellcheck the project lints with. Pinned here and in ci.yml, because an
#: unpinned linter is one gate per machine rather than one gate.
SHELLCHECK_VERSION="v0.9.0"
export SHELLCHECK_VERSION

#: The actionlint the project checks its workflow with. Pinned for the same
#: reason as shellcheck above; ci.yml carries a literal copy of this version
#: (an Actions step cannot source this file), and hygiene.sh greps the two
#: against each other so the copies cannot drift apart silently.
ACTIONLINT_VERSION="1.7.7"
export ACTIONLINT_VERSION

#: The Terraform the infrastructure is planned and applied with. Pinned for the
#: third time and for the third reason: two Terraform versions produce two
#: different state file formats, and the newer one refuses to be read by the
#: older. An unpinned Terraform is not one gate per machine -- it is one machine
#: locking every other machine out of the state.
TERRAFORM_VERSION="1.13.3"
export TERRAFORM_VERSION

#: The development database's target, declared once.
#
# `start.sh` and `db.sh` each carried their own copy of the Postgres URL, which
# is exactly the drift this file exists to stop. To point at another server,
# set DATABASE_URL. That is the one mechanism for choosing it; a second knob
# would give one decision two spellings, which is how they drift.
# The port is derived, not repeated: `docker-compose.yml` publishes on
# `${POSTGRES_HOST_PORT:-5432}`, so spelling 5432 again here gave one fact two
# homes. They only had to disagree once. The clean room moves the port to a free
# one and used to work around this by supplying its own DATABASE_URL -- which
# made `resolve_database_url` file the clean room's OWN database as external, so
# `ensure_db_running` started nothing and alembic died on `connection refused`.
POSTGRES_URL_DEFAULT="postgresql+psycopg://app:app@localhost:${POSTGRES_HOST_PORT:-5432}/app"
export POSTGRES_URL_DEFAULT

# Colour only when someone is watching. A log file, a CI job or a skill reading
# stdout gets clean text.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    _C_BOLD=$'\033[1m'; _C_DIM=$'\033[2m'; _C_RED=$'\033[31m'
    _C_GREEN=$'\033[32m'; _C_YELLOW=$'\033[33m'; _C_OFF=$'\033[0m'
else
    _C_BOLD=''; _C_DIM=''; _C_RED=''; _C_GREEN=''; _C_YELLOW=''; _C_OFF=''
fi

#: Announce a step. One line, present tense, what is about to happen.
step() { printf '%s==> %s%s\n' "$_C_BOLD" "$*" "$_C_OFF"; }

#: A detail under a step -- a command being run, a path, a count.
info() { printf '    %s%s%s\n' "$_C_DIM" "$*" "$_C_OFF"; }

#: A step succeeded.
ok() { printf '    %sOK%s %s\n' "$_C_GREEN" "$_C_OFF" "$*"; }

#: Something is wrong but the run continues.
warn() { printf '    %swarning:%s %s\n' "$_C_YELLOW" "$_C_OFF" "$*" >&2; }

#: The run has FAILED, and continues only to say what to do about it.
#
# Red like `die`, non-exiting like `warn`, and neither of those two would do at
# such a call site. `die` exits on the spot, so the remediation lines under it
# and the script's own closing banner never print -- the operator gets a verdict
# and no instruction. `warn` is yellow, and yellow is already spoken for:
# `audit.sh` spends it on the two paths that end in exit 4, and a gate that
# reports "this dependency is vulnerable" in the same colour as "npm is not
# installed, so nothing was audited" has thrown away the distinction exit 4
# exists to draw. Indented four spaces because it is a detail under a `step`,
# lining up with the `ok` in the branch next to it.
fail() { printf '    %sfailed:%s %s\n' "$_C_RED" "$_C_OFF" "$*" >&2; }

#: Stop, with an explanation an operator can act on. Always say what to DO.
die() { printf '%serror:%s %s\n' "$_C_RED" "$_C_OFF" "$*" >&2; exit 1; }

#: `docker` on PATH and a daemon that answers.
require_docker() {
    command -v docker >/dev/null 2>&1 ||
        die "docker not found on PATH. Run scripts/install.sh, or install it yourself: https://docs.docker.com/get-docker/"
    docker info >/dev/null 2>&1 ||
        die "Docker is installed but the daemon is not answering. Start Docker Desktop (or the docker service) and try again."
}

#: Is there a usable Docker here? A QUESTION, not a demand.
#
# `require_docker` dies; this reports, and sets DOCKER_UNUSABLE_REASON to a
# sentence the caller can print. Anything with a second option needs the question
# rather than the demand, and a copy of the probe at each of those call sites is
# what this file exists to prevent.
#
# Two questions in order, because the second only means something if the first
# was answered yes: a `docker info` against a binary that is not there is an
# error message about the wrong thing.
docker_usable() {
    DOCKER_UNUSABLE_REASON=""
    if ! command -v docker >/dev/null 2>&1; then
        DOCKER_UNUSABLE_REASON="docker is not on PATH"
        return 1
    fi
    if ! docker info >/dev/null 2>&1; then
        DOCKER_UNUSABLE_REASON="the Docker daemon is not answering"
        return 1
    fi
    return 0
}

#: Resolve DATABASE_URL, and say where it came from.
#
# The one place that decides, so `start.sh` and `db.sh` cannot disagree. Called
# explicitly and never at source time: `generate.sh` and `scripts/dump_openapi.py`
# provision their own throwaway database and must keep doing so.
#
# There is one engine (spec/design/architecture.md § One engine), so this no longer chooses between two. What is
# left is the question that still has two answers: is this a database somebody
# else provisioned, or the project's own compose service? APP_DB_EXTERNAL carries
# it, because `ensure_db_running` must not run `docker compose up` against a
# database it did not create.
resolve_database_url() {
    APP_DB_EXTERNAL=0
    export APP_DB_EXTERNAL

    # A DATABASE_URL somebody set is never silently overridden: it may name a
    # database this script did not create, possibly one holding real data, and
    # substituting the project's own for it would be the worst thing available
    # here.
    if [ -n "${DATABASE_URL:-}" ]; then
        APP_DB_EXTERNAL=1
        export DATABASE_URL APP_DB_EXTERNAL
        info "using the DATABASE_URL already set in this environment"
        return 0
    fi

    docker_usable ||
        die "$DOCKER_UNUSABLE_REASON

    This application runs on Postgres and only on Postgres (spec/design/architecture.md § One engine), so there
    is nothing to fall back to. Two ways forward:

      * start Docker, and this script provisions Postgres itself, or
      * point DATABASE_URL at a Postgres you already have (and
        APP_TEST_DATABASE_URL for the test suite)."

    DATABASE_URL="$POSTGRES_URL_DEFAULT"
    export DATABASE_URL
}

#: `uv`, the only Python entry point this project has.
require_uv() {
    command -v uv >/dev/null 2>&1 ||
        die "uv not found on PATH. Run scripts/install.sh, or install it yourself: https://docs.astral.sh/uv/getting-started/installation/"
}

#: `gh`, needed by anything that has to ask GitHub a question rather than git.
#
# One caller today: `release.sh` asks whether `CI passed` is green on the commit it
# is about to tag. That is a question about the server's opinion of a commit, and
# git has no way to ask it.
require_gh() {
    command -v gh >/dev/null 2>&1 ||
        die "gh not found on PATH. Install the GitHub CLI: https://cli.github.com/
    On a runner it is already there; this is the workstation case."
}

#: `node` and `npm`, needed by anything that touches frontend/.
require_node() {
    command -v node >/dev/null 2>&1 ||
        die "node not found on PATH. Install Node 26 or newer: https://nodejs.org/"
    command -v npm >/dev/null 2>&1 ||
        die "npm not found on PATH, although node is. Reinstall Node: https://nodejs.org/"
}

#: Install frontend dependencies if they are missing or older than the lockfile.
#
# `npm ci` rather than `npm install`: it installs exactly the lockfile and fails
# when the two have drifted, which is the same guarantee `uv sync` gives on the
# Python side. A script that silently updated the lockfile would make "it works
# on my machine" reachable again.
ensure_frontend_deps() {
    require_node
    if [ ! -d "$REPO_ROOT/frontend/node_modules" ] ||
       [ "$REPO_ROOT/frontend/package-lock.json" -nt "$REPO_ROOT/frontend/node_modules" ]; then
        step "Installing frontend dependencies (npm ci)"
        (cd "$REPO_ROOT/frontend" && npm ci)
    fi
}

#: The built SPA measured against the sources it was built from.
#
# Prints `missing`, `stale` or `current` on the first line of stdout, and with
# `--explain` a second line saying what was compared against what. The judgment itself
# lives in `scripts/spa_build_state.py` -- one home, because `build.sh --if-stale`
# branches on it, `test.sh` delegates to that, and `app_status.py` reports it, and three
# mtime comparisons written three times are three answers within a month. Exit code is 0
# whatever the verdict: the caller decides what to do about it.
#
# `python3` before `uv run python`, which is the opposite of `status.sh`'s order and is
# a decision rather than an oversight: the module is standard library only by
# declaration, this call sits in the inner loop of `./scripts/test.sh ui`, and `uv run`
# would sync a project environment to answer a question about file mtimes. The fallback
# is there for a machine that has `uv` and no system `python3`.
spa_build_report() {
    if command -v python3 >/dev/null 2>&1; then
        python3 "$REPO_ROOT/scripts/spa_build_state.py" "$@"
        return
    fi
    command -v uv >/dev/null 2>&1 ||
        die "neither python3 nor uv is on PATH, so the built SPA cannot be checked against its sources. Install Python 3.14: https://www.python.org/downloads/"
    uv run python "$REPO_ROOT/scripts/spa_build_state.py" "$@"
}

#: The compose `db` service, started if it is not already running.
#
# Needed by anything that talks to the development database -- which includes
# the e2e suite, because it empties the target's database between scenarios.
#
# Checking this is not redundant with `app_is_up`. `/api/health` deliberately
# touches no service or persistence layer, so an application whose database has
# gone away still answers 200; the first thing to notice is then the e2e suite
# failing 21 scenarios on a connection error. Ask the database directly.
ensure_db_running() {
    # A database this environment supplied is not ours to start. `resolve_database_url`
    # has honoured a pre-set DATABASE_URL since it was written ("never silently
    # overridden"), and this function went on composing a container up anyway --
    # a contradiction that is invisible while the container happens to be ours and
    # fatal the moment it is not.
    if [ "${APP_DB_EXTERNAL:-0}" = "1" ]; then
        info "the database was supplied by this environment -- nothing to start"
        return 0
    fi
    require_docker
    # Three answers, not two: compose that cannot say what is running is not a stopped
    # database, and starting one blind over it names the wrong problem.
    local running=0
    lists_line db docker compose ps --status running --services 2>/dev/null || running=$?
    [ "$running" -ne 2 ] ||
        die "docker compose could not say which services are running. Run: docker compose ps"
    if [ "$running" -ne 0 ]; then
        step "Starting Postgres"
        docker compose up -d --wait db
    fi
}

#: The development database, resolved and running, ready for alembic.
#
# Two steps that always go together: decide which Postgres this run means, then
# make sure it answers. Kept as one verb so `start.sh` and `db.sh migrate` cannot
# come to different conclusions about it.
ensure_db_ready() {
    resolve_database_url
    ensure_db_running
}

#: The port the application serves on, and the one thing that decides it.
#
# `start.sh --port N` sets this, and so may the environment. It exists because
# 8080 was written into `APP_HEALTH_URL` while `--port` only reached uvicorn:
# the flag started an application on N and then every poll asked 8080, so
# `test.sh e2e` on a machine where something else holds 8080 started a second
# application, hit "address already in use", and reported "the application did
# not come up" -- a message about the wrong thing entirely.
APP_PORT="${APP_PORT:-8080}"

#: The URL that answers when the application is up.
#
# `/api/health`, with the prefix. Plain `/health` is matched by the SPA
# catch-all, which answers 200 from the HTML shell whether or not the API works
# -- and 404 forever on a checkout with no frontend build, which would hang any
# poll built on it.
APP_HEALTH_URL="http://127.0.0.1:${APP_PORT}/api/health"

#: True when the application answers.
#
# Liveness of the *process* only -- see `ensure_db_running` for why that is not
# the same question as "is this application usable".
#
# The probe is checked for before it is used. Without curl this function could
# only ever answer "down", so `test.sh e2e` would start a second application on
# a port the first one already holds, and the operator would get a bind error
# rather than "install curl". Python is a hard prerequisite of this project and
# curl is not, so python is the fallback and not the other way round.
_PROBE_PY='import sys, urllib.request; urllib.request.urlopen(sys.argv[1], timeout=2).read()'

app_is_up() {
    if command -v curl >/dev/null 2>&1; then
        curl -fsS --max-time 2 "$APP_HEALTH_URL" >/dev/null 2>&1
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "$_PROBE_PY" "$APP_HEALTH_URL" >/dev/null 2>&1
        return
    fi
    die "neither curl nor python3 is available, so the application cannot be probed"
}

#: Print a closing banner and END THE SCRIPT with that status.
#
# It exits rather than returning, because every call site is the last thing its
# script does and a `return 0` there reads as "we are finished" while quietly
# letting execution fall through to the next block. That is not hypothetical:
# `generate.sh --check` did exactly that and regenerated the files it was asked
# only to inspect.
#: Exit 4 means "nothing failed, but not everything ran". Distinct from 0 because
# `check.sh` is Article XII's definition of "will CI pass", and a run that skipped
# two gates must not be indistinguishable from one that passed them --
# `run-checks/SKILL.md` already states the rule ("A skipped suite is not a passing
# suite") and had no machine-readable way to obey it. Distinct from 1 because
# nothing failed, and calling that red teaches people to ignore red. 2 and 3 were
# already spoken for fleet-wide (contention, ERROR), and the note above records what
# reusing a code costs.
#
# THE BANNER GOES TO STDERR, beside `warn`, `fail`, `die` and check.sh's "Failed
# gates:" / "Not run:" lists, and that is deliberate: stdout is the PAYLOAD -- a
# runner's log, a `--json` block, a version -- and stderr is the VERDICT. A suite that
# printed 100 KB before it failed would otherwise put its banner at the far end of
# 100 KB, where whoever reads the first screenful never gets to it; split this way,
# `./scripts/check.sh >run.log` leaves the whole answer on the terminal. On a
# terminal the two streams land together, and nothing a person sees changes.
summary() {
    if [ "$2" -eq 0 ]; then
        printf '\n%s%s: OK%s\n' "$_C_GREEN$_C_BOLD" "$1" "$_C_OFF" >&2
    elif [ "$2" -eq 4 ]; then
        printf '\n%s%s: INCOMPLETE%s\n' "$_C_YELLOW$_C_BOLD" "$1" "$_C_OFF" >&2
    else
        printf '\n%s%s: FAILED%s\n' "$_C_RED$_C_BOLD" "$1" "$_C_OFF" >&2
    fi
    exit "$2"
}

#: Ask a pipeline a yes/no question without losing the producer's own status.
#
# `producer | grep -q X` cannot tell "X is absent" from "the producer never ran": under
# `pipefail` both are non-zero, and a condition reads any non-zero as "no". So these two
# are the ONE place in scripts/ a pipeline stands as a condition, and the only reader of
# PIPESTATUS (tests/fitness/test_pipeline_verdicts.py holds both halves).
#
# THREE answers, not two: 0 yes, 1 no, 2 the producer could not be asked. Every caller
# handles the third -- as `die`, `fail`, or a named gap -- and none may fold it into "no".
#
# The decision is taken from the two statuses, never from the pipeline's: under
# `pipefail` a producer that `grep -q` cut off with SIGPIPE (141) AFTER a match makes the
# whole pipeline non-zero, and the `if` would read a found answer as "no". So the `if`
# only keeps errexit away from the pipeline, the array is captured in either branch in
# one statement (a separate `rc=$?` first would overwrite it), and `_pipeline_answer`
# reads grep's own status: matched and the producer finished or was cut off -> yes;
# not matched and the producer finished -> no; anything else -> could not ask.

#: Does <producer> print <line>, exactly? 0 yes · 1 no · 2 the producer failed.
lists_line() {
    local needle="$1"; shift
    local statuses
    if "$@" | grep -qxF -- "$needle"; then statuses=("${PIPESTATUS[@]}"); else statuses=("${PIPESTATUS[@]}"); fi
    _pipeline_answer "${statuses[0]}" "${statuses[1]}"
}

#: Does <producer> print a line matching <regex>? The same three answers as lists_line.
lists_match() {
    local pattern="$1"; shift
    local statuses
    if "$@" | grep -qE -- "$pattern"; then statuses=("${PIPESTATUS[@]}"); else statuses=("${PIPESTATUS[@]}"); fi
    _pipeline_answer "${statuses[0]}" "${statuses[1]}"
}

#: <producer status> <grep status> -> 0 yes · 1 no · 2 could not ask.
_pipeline_answer() {
    if [ "$2" -eq 0 ]; then
        [ "$1" -eq 0 ] || [ "$1" -eq 141 ] || return 2
        return 0
    fi
    [ "$2" -eq 1 ] && [ "$1" -eq 0 ] && return 1
    return 2
}
