#!/usr/bin/env bash
# Repository hygiene: the checks that are about the commit, not about the code.
#
# Each one is something that reached the repository once and was found by a human
# days later -- a generated file tracked in git, a script committed without its
# exec bit, a script nobody could ask what it does, a workflow file that parsed
# as YAML and was rejected by GitHub at load time.
#
# It was a function inside check.sh until the SDD gate needed to run the same
# eight gates check.sh runs and could not call a bash function from outside. Two
# things came free with the extraction: hygiene is now runnable on its own in
# about fifteen seconds, which is what you want after touching scripts/, and it
# verifies about itself everything it verifies about the others.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: hygiene.sh [--no-docker]

Checks, in order:
  - nothing tracked by git matches .gitignore, and no known generated path is
    tracked at all
  - the tracked files are stored with the line endings .gitattributes declares
    (a non-destructive renormalize; skipped with a warning on a dirty tree)
  - start.sh mentions every mode flag (--development, --dev, --container,
    --port, --no-seed)
  - every .sh is committed with the executable bit, as git records it
  - every task script is listed in help.sh, and answers --help
  - the shell scripts pass shellcheck, at the pinned version
  - .github/workflows/*.yml passes actionlint at the pinned version, and the
    literal copy of that pin in ci.yml agrees with _lib.sh

  --no-docker  do not probe for Docker. The two linters below are pinned
               THROUGH Docker, and without it -- and without a local binary --
               this script fails, so on a stock machine with no daemon it could
               never be green. Under this flag an unrunnable linter is recorded
               as a NAMED GAP and the script exits 4 (INCOMPLETE) rather than 0
               or 1. It also skips two `docker info` calls, which with Docker
               Desktop stopped block for tens of seconds.

Run by check.sh as its first gate; CI's `quality` and `scripts` jobs run the
same checks as inline steps -- deliberately, so the `--help` step there proves
itself on a runner with no toolchain at all.
TEXT
}

no_docker=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --no-docker) no_docker=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

problems=0
#: Checks that could not run, named. A gap is not a pass and not a failure, and
#: keeping the three apart is the whole point of exit 4.
gaps=()

# A generated file tracked in git goes stale and carries host paths.
tracked_ignored="$(git ls-files --cached --ignored --exclude-standard)"
if [ -n "$tracked_ignored" ]; then
    warn "tracked but matching .gitignore:"
    while IFS= read -r offender; do warn "  $offender"; done <<<"$tracked_ignored"
    problems=1
fi
for path in .coverage openapi.json app/static frontend/dist; do
    # `--cached` and not `--error-unmatch`: same question, no stderr on a miss, so
    # a clean tree does not print an error about the file it is happy about.
    if [ -n "$(git ls-files --cached -- "$path")" ]; then
        warn "$path is generated and must not be committed"
        problems=1
    fi
done

# Committed LF is what keeps the shell scripts runnable after a checkout under
# `core.autocrlf=true`; ci.yml proves the same thing on every push. CI can
# simply `git add --renormalize .`, because its checkout is pristine and the job
# ends; here the same command would stage the developer's index, so the check
# undoes itself with `git reset` -- non-destructive, never a mutated staging
# area. It runs only when the tree is clean (index AND worktree): renormalize
# implies `git add -u`, so on a dirty tree every content-edited file would land
# in the capture and be reported as a line-ending offender it is not. A dirty
# tree gets a warning, not a failure -- CI holds the gate on the state that
# matters, the commit.
if git diff --quiet && git diff --cached --quiet; then
    git add --renormalize .
    renormalized="$(git diff --cached --name-only)"
    git reset -q
    if [ -n "$renormalized" ]; then
        warn "stored with line endings that do not match .gitattributes:"
        while IFS= read -r offender; do warn "  $offender"; done <<<"$renormalized"
        problems=1
    fi
else
    warn "uncommitted changes -- the line-endings check was skipped (it needs a clean tree; CI runs it on every push)"
fi

# Every script is documented, so a new script is not invisible, and
# answers --help before doing anything -- which is what `start.sh` failed to do:
# it ran `uv sync` first, so asking it what it does needed a toolchain to already
# be installed.
#
# The glob is scripts/*.sh and matches only shell scripts. The bare Python files
# beside them are not tasks somebody types, and a `.sh` wrapper around each would be
# a second copy that can drift -- so they are exempt from all three loops above.
#
# The reason used to be stated as "libraries a shell script calls", with the files
# listed by name. Both halves went stale: the list named four while there were more,
# and `ci_summary.py` is called by a WORKFLOW rather than by a script -- the same way
# `dump_openapi.py` already was. What the exemption really turns on is whether a file
# is a task with a `--help` a person asks for, and none of these is.
# The checks below began as CI steps that were pure text and git, with no local
# equivalent. Article XII makes check.sh the definition of "will CI pass", so a step
# that only CI can run is a step that makes the sentence a little bit false -- which
# is why they live here now and CI calls this script.
# Every mode this script advertises is still reachable. `start.sh` is the one that
# has silently lost a flag before, and the modes below are the ones every other
# script, skill and document names it by. Whole-word match, because a substring
# test passed a script that had dropped the short alias entirely.
for flag in --development --dev --container --port --no-seed; do
    grep -qw -- "$flag" scripts/start.sh || { warn "start.sh lost $flag"; problems=1; }
done

# Exec bits, as git records them -- not as this filesystem reports them. The
# commit is what every other checkout is made from; this working tree is not.
for sh in scripts/*.sh; do
    mode="$(git ls-files -s "$sh" | cut -d' ' -f1)"
    [ -n "$mode" ] || continue
    [ "$mode" = "100755" ] || { warn "$sh is committed as $mode, not 100755"; problems=1; }
done

# A script nobody can find is a script nobody uses, and the next person goes back
# to copying commands out of the README -- which is the failure this whole
# directory exists to prevent. Only `_lib.sh` is skipped: it is sourced, never
# run. `_install-docker.sh` is internal too, but it is executable, so it answers
# `--help` like the rest -- the version that skipped every `_`-prefixed name let
# a `--help` that installed Docker go unnoticed (2026-09-08 audit).
for sh in scripts/*.sh; do
    name="${sh##*/}"
    case "$name" in _lib.sh) continue ;; esac
    grep -q -- "$name" scripts/help.sh || { warn "$name is missing from help.sh"; problems=1; }
    "$sh" --help >/dev/null 2>&1 || { warn "$name does not answer --help"; problems=1; }
done

# Pinned, and through Docker, for the same reason actionlint is: an unpinned
# linter is not one gate, it is one gate per machine. Locally I had 0.11 and CI
# had 0.9; 0.9 reported 56 findings 0.11 does not, under a code 0.11 does not
# even define. "shellcheck clean" has to mean the same thing in both places or it
# means nothing.
if [ "$no_docker" -eq 0 ] && docker info >/dev/null 2>&1; then
    docker run --rm -v "$REPO_ROOT:/mnt" -w /mnt \
        "koalaman/shellcheck:$SHELLCHECK_VERSION" -x scripts/*.sh || problems=1
elif command -v shellcheck >/dev/null 2>&1; then
    warn "using the local shellcheck ($(shellcheck --version | awk '/version:/{print $2}')),"
    warn "not the pinned $SHELLCHECK_VERSION -- start Docker for the version CI runs"
    shellcheck -x scripts/*.sh || problems=1
elif [ "$no_docker" -eq 1 ]; then
    warn "--no-docker and no local shellcheck -- the scripts were not linted"
    gaps+=("shellcheck")
else
    warn "neither Docker nor shellcheck is available -- the scripts were not linted"
    problems=1
fi

# The workflow file is code, and YAML being well-formed says nothing about
# whether GitHub will accept it: `join(needs.*.result, " ")` parses as YAML and
# is rejected at load time, because an Actions expression takes only
# single-quoted strings. That shipped once, and the whole workflow -- every gate
# in it -- was dead until someone read the Actions tab.
#
# Docker rather than "skip if not installed", because Docker is already a hard
# prerequisite here and the image is small. A gate that quietly does not run is
# the thing this script exists to prevent.
#
# Pinned, for the reason the linter above is pinned: an unpinned linter is one
# gate per machine, and `latest` moves under everyone at once. A local binary
# is accepted with a warning when its version differs, exactly as the block
# above accepts a local linter. (No comment line here may open with the word
# "shellcheck" -- that spelling starts a directive, and an unparseable
# directive is a parse error.)
if command -v actionlint >/dev/null 2>&1; then
    local_actionlint="$(actionlint --version 2>/dev/null | head -1)"
    if [ "$local_actionlint" != "$ACTIONLINT_VERSION" ]; then
        warn "using the local actionlint ($local_actionlint), not the pinned $ACTIONLINT_VERSION"
    fi
    actionlint || problems=1
# `docker_usable`, the shared helper, rather than a bare `docker info`: the same
# question asked in one place, so "is there a usable Docker" has one answer here
# and in every other script.
elif [ "$no_docker" -eq 0 ] && docker_usable; then
    docker run --rm -v "$REPO_ROOT:/repo" --workdir /repo \
        "rhysd/actionlint:$ACTIONLINT_VERSION" || problems=1
elif [ "$no_docker" -eq 1 ]; then
    warn "--no-docker and no local actionlint -- the workflow file was not checked"
    gaps+=("actionlint")
else
    warn "neither actionlint nor Docker is available -- the workflow file was not checked"
    problems=1
fi

# The pin is duplicated in ci.yml, because an Actions step cannot source this
# library. Two copies of one fact drift; this grep is what makes the drift a
# red run instead of a quiet fork of "actionlint clean" into two meanings.
if ! grep -q "rhysd/actionlint:$ACTIONLINT_VERSION" .github/workflows/ci.yml; then
    warn "ci.yml runs a different actionlint than ACTIONLINT_VERSION=$ACTIONLINT_VERSION in _lib.sh -- update the two together"
    problems=1
fi

# A gap only speaks when nothing actually failed: a real problem is the louder
# fact and must not be downgraded to "incomplete" by a linter that also happened
# to be missing.
if [ "$problems" -eq 0 ] && [ ${#gaps[@]} -gt 0 ]; then
    warn "not run: ${gaps[*]}"
    summary "Repository hygiene" 4
fi
summary "Repository hygiene" "$problems"
