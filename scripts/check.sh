#!/usr/bin/env bash
# Every gate of THIS APPLICATION that CI runs, in one command. Containment, not
# equivalence: everything here runs in CI, and CI runs more.
#
# What it runs that this cannot is a closed list, not a shrug -- `spec/design/testing.md`
# § What only CI can answer names each entry and says why it lives there. Reaching for
# that list is the difference between a known gap and a surprise at the merge button.
#
# The point is not convenience -- it is that "green locally, red in CI" costs a
# round trip and teaches people to distrust the pipeline. Every gate below has a
# counterpart in .github/workflows/ci.yml, and a gate added there belongs here.
#
# The specification gates are not here, and that is a decision rather than a gap:
# they are the change process's own, and this script is the application's -- it calls
# nothing of the process and names none of its files. `sdd-specs` is the command that
# gives the same verdict locally; it arrives on PATH with the plugin.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: check.sh [--fast] [--no-docker]

  (no argument)  every gate, including the Docker image and the e2e suite
  --fast         skip the two slow ones (docker build, e2e) -- good for a
                 tight edit loop, not good enough before a push
  --no-docker    every gate this machine can honestly run, and a named list of
                 the ones it cannot. Implies --fast, because the Docker image
                 and the e2e suite are not skipped here by choice. The backend
                 gate cannot run at all unless APP_TEST_DATABASE_URL names a
                 Postgres, and is reported as a named gap when it does not.
                 Exits 4 (INCOMPLETE), never 0: this is not the pull request
                 condition and must not read like it.

                 For the same machine WITHOUT the coverage gap, point
                 APP_TEST_DATABASE_URL at a Postgres you already have and
                 drop this flag -- the backend gate then runs in full and only
                 the image and e2e still need a daemon.

Gates: repository hygiene, lint, infrastructure, generated-code drift, frozen API
contract, backend tests, frontend tests, frontend build, dependency audit, docker
image, e2e.

Exit: 0 every gate ran and passed; 1 a gate ran and failed; 4 every gate that
ran passed, but a gate did not run.

What this cannot reproduce is named rather than implied, and it is seven things
rather than one: spec/design/testing.md, section "What only CI can answer".
TEXT
}

fast=0
no_docker=0
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --fast) fast=1 ;;
        # `fast=1` is set HERE, before the `if [ "$fast" -eq 0 ]` block below, so
        # that block stays byte-identical. test_sdd_gate_parity.py reads it with a
        # regex to derive PROFILES["fast"], and asks in its own message not to be
        # rewritten casually. Two variables rather than one, though: `fast` decides
        # which gates run, `no_docker` decides the exit code and the banner, and
        # collapsing them would make a deselected gate and an unrunnable one look
        # the same at the exit -- which is the distinction this flag exists for.
        --no-docker) no_docker=1; fast=1 ;;
        # Named rather than left to "unknown option", because it is the word
        # every other script here uses for the escape hatch, so it is the word that
        # gets typed. It is the wrong word for this script: the choice here is not
        # which database but which gates can honestly run, and two of the three
        # affected gates have no database in them at all.
        --sqlite) usage >&2; die "there is no second engine to choose (spec/design/architecture.md § One engine). The choice here is which gates can honestly run: use --no-docker." ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

failed=()
#: Gates that ran, passed what they could, and said something was not checked.
#: Discovered from what each gate REPORTED, never from a list check.sh keeps of
#: what it believes touches Docker -- that list goes stale the first time a gate
#: grows a second prerequisite.
incomplete=()
gate() {
    local label="$1"; shift
    step "$label"
    local rc=0
    "$@" || rc=$?
    case "$rc" in
        0) ok "$label" ;;
        4) incomplete+=("$label") ;;
        *) failed+=("$label") ;;
    esac
}

hygiene_args=()
backend_args=(backend)
#: What the backend gate runs. Without a daemon it needs a Postgres somebody else
#: provisioned, and there is no second engine to fall back to (spec/design/architecture.md § One engine) -- so
#: with neither, it runs the subset that needs no database and the rest becomes a
#: NAMED GAP. The gate keeps its label either way, because the label is what
#: `gate.py` matches on and a second one would be a second gate to keep in step;
#: what it actually covered is said below, under "Not run". The gap is NOT pushed
#: onto `incomplete` -- that array is what gates REPORT about themselves, and
#: `test.sh --no-db` passes honestly for the subset it was asked to run.
backend_is_a_gap=0
if [ "$no_docker" -eq 1 ]; then
    hygiene_args+=(--no-docker)
    if [ -z "${APP_TEST_DATABASE_URL:-}" ]; then
        backend_args=(--no-db)
        backend_is_a_gap=1
    fi
fi

gate "Repository hygiene" "$REPO_ROOT/scripts/hygiene.sh" ${hygiene_args[@]+"${hygiene_args[@]}"}
gate "Static checks"        "$REPO_ROOT/scripts/lint.sh"
gate "Infrastructure"       "$REPO_ROOT/scripts/infra-check.sh" ${hygiene_args[@]+"${hygiene_args[@]}"}
gate "Generated code is current" "$REPO_ROOT/scripts/generate.sh" --check
gate "API contract is frozen" "$REPO_ROOT/scripts/contracts.sh"
# `--junitxml` here, and not only in CI: the script contract (the plugin's docs/script-contract.md)
# says `check` runs every suite and LEAVES its junit at the path .specconf/stack.json names,
# so the process reads test-level evidence off this run instead of running the suites a
# second time at every stage boundary. The frontend and e2e suites write theirs unasked.
# Fitness first and on its own: it is its own suite (tests/fitness, no database), the
# backend gate no longer collects it, and it answers in seconds on any machine -- so it
# is never a gap, under `--no-docker` or without a Postgres.
gate "Fitness tests"        "$REPO_ROOT/scripts/test.sh" fitness --junitxml=.sdd/reports/fitness.junit.xml
gate "Backend tests"       "$REPO_ROOT/scripts/test.sh" "${backend_args[@]}" --junitxml=.sdd/reports/backend.junit.xml
gate "Frontend tests"       "$REPO_ROOT/scripts/test.sh" frontend
gate "Frontend build"       "$REPO_ROOT/scripts/build.sh"
gate "Dependency audit"     "$REPO_ROOT/scripts/audit.sh"

if [ "$fast" -eq 0 ]; then
    gate "Docker image"     "$REPO_ROOT/scripts/build.sh" --docker
    gate "End-to-end tests" "$REPO_ROOT/scripts/test.sh" e2e
else
    warn "--fast: skipped the Docker image and the e2e suite"
fi

if [ ${#failed[@]} -gt 0 ]; then
    printf '\n%sFailed gates:%s\n' "$_C_RED" "$_C_OFF" >&2
    for f in "${failed[@]}"; do printf '  - %s\n' "$f" >&2; done
    summary "Check" 1
fi

# Nothing failed. Say what did not RUN, because a green that skipped two gates and
# a green that passed them are the same sentence otherwise -- and this script is
# Article XII's definition of "will CI pass".
if [ "$no_docker" -eq 1 ] || [ ${#incomplete[@]} -gt 0 ]; then
    printf '\n%sNot run:%s\n' "$_C_YELLOW" "$_C_OFF" >&2
    if [ "$no_docker" -eq 1 ]; then
        printf '  - Docker image, End-to-end tests -- they need a daemon\n' >&2
        if [ "$backend_is_a_gap" -eq 1 ]; then
            printf '  - every test that needs a database -- there is none here\n' >&2
            printf '    (set APP_TEST_DATABASE_URL to a Postgres you have to close that one)\n' >&2
        else
            printf '  - the backend gate ran in full, on the Postgres APP_TEST_DATABASE_URL names\n' >&2
        fi
    fi
    for f in ${incomplete[@]+"${incomplete[@]}"}; do printf '  - inside %s\n' "$f" >&2; done
    printf '\nThis is not the pull request condition. Run plain check.sh before pushing.\n' >&2
    # Asked LAST, never first: with Docker Desktop stopped `docker info` blocks
    # for tens of seconds, and this is a courtesy, not a prerequisite.
    if [ "$no_docker" -eq 1 ] && docker_usable; then
        warn "Docker works on this machine -- drop --no-docker for the whole gate"
    fi
    summary "Check" 4
fi
summary "Check" 0
