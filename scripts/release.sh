#!/usr/bin/env bash
# Cut a release: compute the next version, tag a reviewed commit, push the tag.
#
# **The tag is what deploys production**, so everything here is about making the
# tag mean exactly one commit that a person chose. The bump is an argument rather
# than something inferred from commit messages: this repository's rule is that
# every deployment is asked for (`.github/workflows/deploy.yml`), and a release
# that computed its own significance from the word at the front of a commit would
# be deciding rather than being asked.
#
# **It writes no version and makes no commit**, and that is the whole shape of it.
# A release commit would have to reach `main`, which the branch ruleset refuses to
# everybody -- `bypass_actors` is empty and `current_user_can_bypass` is `never` --
# so the only release that can exist is one that tags a commit already merged
# through a pull request. The version reaches the running application as
# `APP_VERSION` instead, which both readers already prefer over `pyproject.toml`
# (`app/core/build_info.py`, `scripts/infra.sh`). Nothing writes `pyproject.toml`,
# so `uv.lock` cannot drift out of step with it.
#
# Refuses more than it does: a dirty tree, a HEAD that is not the trunk, a tag that
# already exists, a previous tag it cannot parse -- and, before it publishes
# anything, a HEAD that is not the pushed trunk, a `CI passed` that is not green on
# it, and a lockfile that is out of date. Each of those is a release that would have
# to be undone, and a tag is the one thing here that is awkward to take back.
#
# Run by `.github/workflows/release.yml`. A person can run it, and then has to
# push the result themselves -- see --no-push.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

#: The aggregate verdict on a commit, named once. `.github/workflows/ci.yml` calls
#: the job `CI passed`, and the branch ruleset requires that exact context.
CI_CHECK="CI passed"

usage() {
    cat <<'TEXT'
usage: release.sh <patch|minor|major> [--dry-run] [--no-push]

  patch    a fix. vX.Y.Z -> vX.Y.Z+1
  minor    a feature. vX.Y.Z -> vX.Y+1.0
  major    a break. vX.Y.Z -> vX+1.0.0

  --dry-run  print what it would do and change nothing at all
  --no-push  tag locally; push nothing, and ask GitHub nothing

What it does, in order:

  1. find the last vX.Y.Z tag (v0.0.0 if there is none) and compute the next
  2. refuse if the tree is dirty, HEAD is not the trunk, or the tag exists
  3. refuse, before tagging, if this is going to push and any of these is false:
     the lockfile is up to date, HEAD is exactly the pushed trunk, and the
     `CI passed` check on HEAD is green
  4. tag HEAD with the commits since the last release
  5. push that one tag ref, and nothing else

It writes no version into pyproject.toml and makes no commit: the tag is the only
record of a version, and the application is told which one it is through
APP_VERSION. Nothing may push to the trunk, so a release tags a commit that got
there by being reviewed.

Pushing the tag is what asks production for a deployment -- gated by the required
reviewer on the `prod` GitHub Environment, which is enforced by GitHub and not by
this script.

The LAST line of stdout is the new version, and there is no closing banner --
`release.yml` reads that line and hands it to the production deploy as a git ref.
`infra.sh output` skips its banner for the same reason: when stdout is the result,
a summary line after it is the thing that gets parsed.
TEXT
}

BUMP="${1:-}"
case "$BUMP" in
    -h|--help|"") usage; exit 0 ;;
    patch|minor|major) shift ;;
    *) usage >&2; die "unknown bump: $BUMP. It is patch, minor or major -- somebody's decision." ;;
esac

dry_run=0
push=1
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) dry_run=1 ;;
        --no-push) push=0 ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

require_uv

# --------------------------------------------------------------------------- #
# What the next version is
# --------------------------------------------------------------------------- #

#: The highest release tag reachable from HEAD, or v0.0.0.
#
# `git describe --tags --abbrev=0` used to answer this, and it stopped being able
# to: with no release commit, two releases in a row put both tags on the SAME
# commit, and describe has no defined tie-break between them -- so the arithmetic
# could walk backwards. `--sort=-v:refname` orders by version rather than by when
# a tag was written, and `--count=1` does the limiting inside git, so there is no
# pipe for `pipefail` to turn a closed one into a failure.
#
# `--merged HEAD` matters as much: a tag on an abandoned branch is not a release
# this trunk ever had, and treating it as the base is how the arithmetic walks
# into a name that is already taken.
LAST=$(git for-each-ref --count=1 --sort=-v:refname \
    --format='%(refname:short)' --merged HEAD 'refs/tags/v[0-9]*')
[ -n "$LAST" ] || LAST='v0.0.0'
NEXT=$(uv run python scripts/release_version.py next "$BUMP" --last "$LAST")

step "Release: $LAST -> $NEXT ($BUMP)"

# --------------------------------------------------------------------------- #
# What would make it wrong
# --------------------------------------------------------------------------- #

# No `| sed ... || true` over the pair: that one token forgave "origin/HEAD is not
# set", which is an answer (fall back to main), and a git that failed, which is not.
# Both still fall back -- a release refuses below on a branch that is not the trunk
# -- but only by the status of the command that answered, not of `sed`.
TRUNK=""
if trunk_ref=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null); then
    TRUNK="${trunk_ref#origin/}"
fi
[ -n "$TRUNK" ] || TRUNK="main"
HEAD_BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$HEAD_BRANCH" = "$TRUNK" ] ||
    die "a release is cut from the trunk ($TRUNK), and this is $HEAD_BRANCH.
    Everything a release contains has to have been reviewed on the way in."

if ! git diff --quiet || ! git diff --cached --quiet; then
    die "the working tree has changes. A release tag has to name a commit that exists,
    not one plus whatever happens to be lying around."
fi

! git rev-parse -q --verify "refs/tags/$NEXT" >/dev/null ||
    die "$NEXT already exists. A tag is not moved: pick the next bump up, or work out
    why the last release did not finish."

# --------------------------------------------------------------------------- #
# Doing it
# --------------------------------------------------------------------------- #

#: The tag's message. `git show <tag>` then answers "what is in this release"
#: offline, which the GitHub Release page cannot.
NOTES=$(git log --no-merges --pretty='- %s (%h)' "${LAST}..HEAD" 2>/dev/null || printf -- '- the first release\n')
[ -n "$NOTES" ] || NOTES="- no commits since $LAST"

if [ "$dry_run" -eq 1 ]; then
    info "would tag HEAD as $NEXT and push that one ref; nothing else would change"
    printf '%s\n' "$NOTES" >&2
    printf '%s\n' "$NEXT"
    exit 0
fi

# What has to be true before anything is published, and it is checked BEFORE the
# tag exists rather than before the push. A refused run that had already tagged
# would leave `$NEXT` behind locally, and the next attempt would die on "already
# exists" -- a refusal that has to be cleaned up by hand is one people learn to
# route around.
#
# Only on the push path. `--no-push` and `--dry-run` publish nothing, and making
# them need the network and a GitHub login would cost a person the one way of
# asking "what would this release be called" from a train.
if [ "$push" -eq 1 ]; then
    step "Checking that $NEXT may be published"

    # First, because it is local, instant and needs no network at all.
    #
    # It is not redundant with the green `CI passed` below, and the difference is
    # the point: that verdict is the server's opinion, read over a wire, of a
    # collection of jobs. This is the property itself, asked here -- the release
    # has to be reproducible from its own commit, and `uv sync --locked` on a
    # clean machine is what "reproducible" means.
    uv lock --check >/dev/null 2>&1 ||
        die "uv.lock is not up to date with pyproject.toml. A release has to be
    reproducible from the commit it names, and this one is not. Fix the lockfile in
    a pull request -- the trunk is the only thing a release may tag."

    # The trunk as the SERVER has it, not as this checkout believes it. A commit
    # that is only here has been through no pull request and no ruleset, and a tag
    # on it is a release of something nobody reviewed.
    git fetch --quiet origin "$TRUNK" ||
        die "could not fetch origin/$TRUNK. A release names the reviewed trunk, so
    this check is not one to skip."
    HEAD_SHA=$(git rev-parse HEAD)
    TRUNK_SHA=$(git rev-parse FETCH_HEAD)
    [ "$HEAD_SHA" = "$TRUNK_SHA" ] ||
        die "HEAD is $(git rev-parse --short HEAD), and origin/$TRUNK is $(git rev-parse --short FETCH_HEAD).
    A release tags the commit the trunk actually carries: pull, or push what is
    missing through a pull request."

    # And whether that commit is green. This is the step a person used to do by
    # reading the checks page before dispatching the workflow
    # (docs/runbooks/release-to-production.md), which is exactly the kind of rule
    # that holds until the one time somebody is in a hurry.
    require_gh
    VERDICT=$(CI_CHECK="$CI_CHECK" gh api "repos/{owner}/{repo}/commits/$HEAD_SHA/check-runs" \
        --jq '[.check_runs[] | select(.name == env.CI_CHECK) | "\(.status)/\(.conclusion)"] | first // "absent"') ||
        die "could not ask GitHub about $CI_CHECK on $HEAD_SHA. A release is not cut on
    an unread verdict -- check \`gh auth status\` and the network."
    [ "$VERDICT" = "completed/success" ] ||
        die "$CI_CHECK on $(git rev-parse --short HEAD) is $VERDICT, not completed/success.
    A release cut from a red trunk deploys a red trunk."
fi

# Identified as the bot when CI runs this, and left to a person's own config when
# a person does. `git tag -a` records a tagger, and git refuses to write one with
# no identity at all -- which on a runner is a failure five steps after the cause.
if [ -n "${GITHUB_ACTIONS:-}" ]; then
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
fi

step "Tagging $(git rev-parse --short HEAD) as $NEXT"
git tag -a "$NEXT" -m "$NEXT

$NOTES"

if [ "$push" -eq 1 ]; then
    step "Pushing $NEXT"
    # ONE ref, named in full. The branch is not pushed because it cannot be: the
    # ruleset covers `~DEFAULT_BRANCH` and nothing covers `refs/tags/*`, so a tag
    # is the only thing this may publish -- and a single ref cannot be half
    # pushed, which is the guarantee `--follow-tags` was wrongly credited with.
    git push origin "refs/tags/$NEXT"
else
    warn "--no-push: $NEXT is local. Nothing is released until it is pushed."
fi

# No `summary` banner. `summary` exits, and the version has to be printed after
# everything else -- `release.yml` reads the last line of stdout and gives it to
# `checkout` as a ref. The banner went to stdout when this was written, which is why
# `infra.sh output` skips its own; it goes to stderr now, and the rule stands anyway:
# this is the second place in the repository where stdout is the result.
ok "released $NEXT" >&2
printf '%s\n' "$NEXT"
