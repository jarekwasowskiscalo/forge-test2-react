#!/usr/bin/env bash
# Known vulnerabilities in the dependencies this repository ships and builds with.
#
# This gate exists because of the one class of drift nothing here was watching. The
# weekly `schedule` in ci.yml was added precisely to catch "a moved base image, a
# yanked wheel, a runner image change" -- change that no commit of ours causes -- and
# a security advisory published against a dependency we have not touched is exactly
# that shape. It was the only member of the class with no gate: 17 gates, a tested
# parity between CI and check.sh, a weekly drift run, and nothing that ever asked
# whether a dependency had become dangerous overnight.
#
# ONE SECTION PER ECOSYSTEM, and every ecosystem this repository executes gets one.
# It used to read a single tree -- frontend/package-lock.json -- and report the
# verdict under an unqualified name, so a green "Dependency audit" was published by a
# repository whose uv.lock had never been the subject of a single advisory query. The
# gap was already load-bearing: ci.yml's `deps` filter counts pyproject.toml and
# uv.lock as dependency manifests, so a backend dependency change made this gate
# BLOCKING over a tree it did not read. A label may be as wide as its measurement and
# no wider; widening the measurement is the half worth having.
#
# Each section ends in one of three statements, and the summary keeps them apart:
# CHECKED (with the lockfile it resolved), a NAMED GAP (its tool is absent), or
# COVERED BY ANOTHER MECHANISM (with that mechanism named, and a cheap look to confirm
# it is still there -- a coverage line that asserts nothing is the sin this file was
# repaired for, one level up).
#
# HIGH and above fails, for npm. Below that reports and passes, and that is a decision
# rather than laziness: this template's own moderate advisories are two React Router
# open redirects reachable only through a `to=` that takes user input, and every
# navigation target in `frontend/src/` is the route constant. A gate that fails on an
# advisory nobody can reach is a gate people learn to pass with `--force`, and `npm
# audit fix --force` is a major version bump applied by a machine at 3am on a Monday.
#
# TWO ASYMMETRIES, NAMED RATHER THAN LEFT TO BE FOUND. `uv audit` exposes no severity
# threshold, so --level governs npm alone and ANY Python advisory fails the gate. And
# `uv audit` is still flagged experimental by uv itself: it prints that warning on
# every run, and its output shape may move under a version bump this repository pins.
#
# Absent tooling is a NAMED GAP (exit 4), never a pass: a gate that quietly does not
# run reads on a dashboard exactly like one that found nothing.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: audit.sh [--level <low|moderate|high|critical>]

  (no argument)  fail on a high or critical npm advisory; report the rest
  --level        the severity that fails the FRONTEND section (default: high).
                 `uv audit` has no threshold to set, so ANY Python advisory fails.

The ecosystems, and what each line of the report says:

  Frontend (npm)       npm audit over frontend/package-lock.json
  Backend (Python)     uv audit over uv.lock
  Base images          no scanner here: pinned by digest, Dependabot proposes the
                       bump, tests/tooling/test_container_pins.py holds the pin
  Terraform providers  no scanner here: locked per root, Dependabot proposes
  GitHub Actions       no scanner here: pinned to commits, Dependabot proposes,
                       tests/fitness/test_action_pins.py holds the pins

Reads the lockfiles only -- no install, no network write, nothing modified.

Exit codes:
  0  every ecosystem was answered and none carries an advisory that fails it
  1  an advisory fails its section, or a mechanism a coverage line claims is gone
  4  an ecosystem's tool is absent, so it was not audited (a NAMED GAP, not a pass)

Run by check.sh as one of its gates, and by CI's `audit` job as the same script.
TEXT
}

level="high"
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --level) shift; level="${1:-}"; [ -n "$level" ] || die "--level needs a value" ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

case "$level" in
    low|moderate|high|critical) ;;
    *) die "unknown level: $level (low, moderate, high, critical)" ;;
esac

problems=0
#: Ecosystems that could not be audited, named. A gap is not a pass and not a
#: failure, and keeping the three apart is the whole point of exit 4.
gaps=()

# --- Frontend (npm) ----------------------------------------------------------------

step "Frontend dependencies (npm audit over frontend/package-lock.json, fails at ${level})"
if ! command -v npm >/dev/null 2>&1; then
    warn "npm is not on PATH -- the frontend dependencies were not audited"
    gaps+=("frontend (npm)")
elif [ ! -f frontend/package-lock.json ]; then
    warn "frontend/package-lock.json is missing -- there is no resolved tree to audit"
    gaps+=("frontend (npm)")
else
    # Printed in full BEFORE the verdict, and printed even when the section passes. A
    # moderate advisory that never reaches a screen is an advisory nobody decides
    # about, which is how "known and argued" turns into "unknown" three months later.
    (cd frontend && npm audit) || true

    if (cd frontend && npm audit --audit-level="$level" >/dev/null 2>&1); then
        ok "no ${level}-or-worse advisory in frontend/package-lock.json"
    else
        fail "npm audit reports a ${level}-or-worse advisory -- see the report above"
        printf '\n%s\n' "Fix without a major bump:  cd frontend && npm audit fix" >&2
        printf '%s\n' "If the advisory is genuinely unreachable here, say so in a dated row" >&2
        printf '%s\n' "in spec/changes/EXEMPTIONS.md rather than lowering --level." >&2
        problems=1
    fi
fi

# --- Backend (Python) --------------------------------------------------------------

step "Backend dependencies (uv audit over uv.lock)"
if ! command -v uv >/dev/null 2>&1; then
    warn "uv is not on PATH -- the backend dependencies were not audited"
    gaps+=("backend (Python)")
elif [ ! -f uv.lock ]; then
    warn "uv.lock is missing -- there is no resolved tree to audit"
    gaps+=("backend (Python)")
else
    # --frozen reads the lock as committed and never rewrites it: CI runs
    # `uv sync --locked` in the same repository, and an audit that re-resolved would
    # be answering about a tree no job installs.
    rc=0
    uv audit --frozen || rc=$?
    if [ "$rc" -eq 0 ]; then
        ok "no known vulnerability in uv.lock"
    else
        fail "uv audit reports a vulnerability in uv.lock -- see the report above"
        printf '\n%s\n' "Fix:  uv lock --upgrade-package <name>  (then commit uv.lock)" >&2
        printf '%s\n' "If the advisory is genuinely unreachable here, say so in a dated row" >&2
        printf '%s\n' "in spec/changes/EXEMPTIONS.md rather than dropping the section." >&2
        problems=1
    fi
fi

# --- The three with no advisory scanner --------------------------------------------
#
# Not silence and not a gap: each is covered by a mechanism that freezes WHICH bytes
# run, plus a proposer that keeps the frozen value from going stale. What is missing
# is an advisory query over the frozen artefact, and saying so is the point. The cheap
# checks below are not a second copy of the tests they name -- they are this report
# refusing to publish a coverage claim it has not looked at.

step "Base images (no advisory scanner here)"
if ! grep -qE '^FROM[^@]*@sha256:' Dockerfile; then
    fail "a Dockerfile base carries no digest -- the coverage claim below is false"
    problems=1
elif ! grep -q 'package-ecosystem: docker' .github/dependabot.yml; then
    fail "nothing proposes the base-image bump the digest freezes"
    problems=1
else
    info "pinned by digest in Dockerfile; Dependabot's docker ecosystem proposes the bump;"
    info "tests/tooling/test_container_pins.py holds the pin. NOT advisory-scanned."
fi

step "Terraform providers (no advisory scanner here)"
# The roots have ONE home, scripts/infra-check.sh, and this reads it rather than
# keeping a second list: a root added there is covered here without anybody
# remembering this file.
roots_line="$(grep -E '^ROOTS=\(' scripts/infra-check.sh || true)"
if [ -z "$roots_line" ]; then
    warn "scripts/infra-check.sh no longer declares ROOTS=( ... ) -- the roots were not checked"
    gaps+=("Terraform providers")
else
    roots_line="${roots_line#ROOTS=(}"
    read -r -a roots <<<"${roots_line%)}"
    unlocked=()
    for root in "${roots[@]}"; do
        [ -f "infra/terraform/$root/.terraform.lock.hcl" ] || unlocked+=("$root")
    done
    if [ ${#unlocked[@]} -gt 0 ]; then
        fail "these Terraform roots have no provider lock: ${unlocked[*]}"
        problems=1
    elif ! grep -q 'package-ecosystem: terraform' .github/dependabot.yml; then
        fail "nothing proposes the provider bump the lock freezes"
        problems=1
    else
        info "locked in .terraform.lock.hcl across ${#roots[@]} roots; Dependabot's terraform"
        info "ecosystem proposes the bump. NOT advisory-scanned."
    fi
fi

step "GitHub Actions (no advisory scanner here)"
# `@main` on the process's own two composite actions is a decision argued in ci.yml
# and declared in tests/fitness/test_action_pins.py; everything else is a commit.
#
# Read first, judged second, and never as one pipeline: a `grep -r` that could not read
# the workflows used to feed an empty stream to the filters, and "nothing left after
# filtering" is exactly what a clean tree looks like -- a failed read reported as full
# coverage. One `grep -v` with three patterns then answers 0 (a moving tag is left),
# 1 (nothing is) or 2 (it could not tell), and each of the three is named.
read_status=0
uses_lines="$(grep -rhE '^\s*(- )?uses: ' .github/workflows/*.yml)" || read_status=$?
if [ "$read_status" -gt 1 ]; then
    moving=2
elif [ "$read_status" -eq 1 ]; then
    moving=1
elif grep -qvE -e '@[0-9a-f]{40} #' -e 'uses: \./' \
    -e 'claude-marketplace/\.github/actions/sdd-(specs|tests)@main' <<<"$uses_lines"; then
    moving=0
else
    moving=$?
fi
if [ "$moving" -eq 0 ]; then
    fail "a workflow step runs a moving tag -- the coverage claim below is false"
    problems=1
elif [ "$moving" -ne 1 ]; then
    fail "the workflows under .github/workflows/ could not be read, so no pin was checked"
    problems=1
elif ! grep -q 'package-ecosystem: github-actions' .github/dependabot.yml; then
    fail "nothing proposes the action bump the commit pin freezes"
    problems=1
else
    info "pinned to 40-character commits with the tag beside them; Dependabot's"
    info "github-actions ecosystem proposes the bump; tests/fitness/test_action_pins.py"
    info "holds the pins and names the two references that may move. NOT advisory-scanned."
fi

# --- The verdict -------------------------------------------------------------------

# A gap only speaks when nothing actually failed: a real advisory is the louder fact
# and must not be downgraded to "incomplete" by a toolchain that also happened to be
# missing an ecosystem's scanner.
if [ "$problems" -eq 0 ] && [ ${#gaps[@]} -gt 0 ]; then
    warn "not audited: ${gaps[*]}"
    summary "Dependency audit" 4
fi
summary "Dependency audit" "$problems"
