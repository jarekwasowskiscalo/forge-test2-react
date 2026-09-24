#!/usr/bin/env bash
# A branch's own copy of the application: put one up, take one down.
#
# A preview is a Lambda, a public Function URL, and a database on the cluster that
# `infra/terraform/preview/shared/` created once. It is NOT a copy of the account:
# no VPC, no cluster, no bucket, no distribution. That is what makes it ninety
# seconds to raise and half a minute to drop, and what keeps the account inside
# its five-VPC quota with any number of branches live.
#
# **The branch NAME is the whole identity chain.** name -> slug -> state key ->
# resource names -> database name, each step deterministic. So a teardown needs
# only the name, which both the `pull_request` and the `delete` webhook payloads
# still carry after the branch itself is gone.
#
# Deployments come from GitHub Actions (`.github/workflows/preview.yml` and
# `preview-teardown.yml`); this script is what they run, and what a person runs to
# read the same steps.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: preview.sh slug [<branch>]
       preview.sh up   [<branch>]
       preview.sh down [<branch>]

  slug   print the identifier this branch's preview uses, and stop. Everything
         else is derived from it, so this is the thing to check first.
  up     build the preview package, apply the stack, create-and-migrate the
         branch's database, print the URL.
  down   destroy the stack, then drop the branch's database. In that order: the
         functions holding connections go first.

With no <branch>, the current one (or GITHUB_REF_NAME in Actions).

The slug is the branch name reduced to something legal three times over -- as an
AWS resource name, as a Terraform state key, and with hyphens turned to
underscores as a PostgreSQL identifier. It always ends in six hex characters of
the full name's hash, so two branches whose readable parts collide still get
separate stacks.

`up` and `down` need the AWS CLI and credentials, taken from the environment
exactly as the CLI takes them. `slug` needs neither.
TEXT
}

COMMAND="${1:-}"
case "$COMMAND" in
    -h|--help|"") usage; exit 0 ;;
    slug|up|down) shift ;;
    *) usage >&2; die "unknown command: $COMMAND" ;;
esac

# --------------------------------------------------------------------------- #
# Identity
# --------------------------------------------------------------------------- #

#: The readable half of a slug. Twenty characters, because the whole name has to
#: fit inside Lambda's 64: `sdd-guestbook` (13) + `-preview-` (9) + the slug (27)
#: + `-migrate` (8) leaves seven to spare.
SLUG_READABLE_MAX=20

sha256_hex() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 | cut -d' ' -f1
    else
        die "no sha256sum and no shasum. One of them decides which preview this is."
    fi
}

#: branch -> slug, deterministically and with no toolchain.
#:
#: The hash is appended ALWAYS, not only when the readable part was truncated.
#: Without that, `feat/x` and `feat-x` reduce to the same string and would share a
#: state key -- which does not conflict or warn: the second apply reads the
#: first's state and takes its stack over.
compute_slug() {
    local ref="$1" readable hash
    [ -n "$ref" ] || die "no branch name to make a slug from."

    readable=$(
        printf '%s' "$ref" |
            tr '[:upper:]' '[:lower:]' |
            sed -e 's/[^a-z0-9]/-/g' -e 's/--*/-/g' -e 's/^-*//' -e 's/-*$//' |
            cut -c "1-$SLUG_READABLE_MAX" |
            sed -e 's/-*$//'
    )
    # A branch of nothing but punctuation still needs a name, and `-9a3f1c` is not
    # one: the slug must begin with a letter or a digit.
    [ -n "$readable" ] || readable="branch"

    hash=$(printf '%s' "$ref" | sha256_hex | cut -c1-6)
    printf '%s-%s' "$readable" "$hash"
}

resolve_branch() {
    if [ -n "${1:-}" ]; then
        printf '%s' "$1"
        return 0
    fi
    if [ -n "${GITHUB_REF_NAME:-}" ]; then
        printf '%s' "$GITHUB_REF_NAME"
        return 0
    fi
    git rev-parse --abbrev-ref HEAD 2>/dev/null ||
        die "not in a git checkout and no branch given. Pass one."
}

BRANCH=$(resolve_branch "${1:-}")
SLUG="${PREVIEW_SLUG:-$(compute_slug "$BRANCH")}"
#: The same reduction the Terraform root performs, and the name
#: `app/lambda_handler.py` refuses to act without the `preview_` prefix of.
DATABASE="preview_$(printf '%s' "$SLUG" | tr '-' '_')"

if [ "$COMMAND" = "slug" ]; then
    printf '%s\n' "$SLUG"
    exit 0
fi

export PREVIEW_SLUG="$SLUG"
export PREVIEW_BRANCH="$BRANCH"

command -v aws >/dev/null 2>&1 ||
    die "the AWS CLI is not on PATH. https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"

#: What the shared preview layer published. Read from SSM rather than from that
#: root's Terraform state: the state object holds the cluster's master password in
#: cleartext, and this script has no business being able to read it.
shared_parameter() {
    aws ssm get-parameter --name "/sdd-guestbook/preview/$1" --query 'Parameter.Value' --output text
}

# --------------------------------------------------------------------------- #
# up
# --------------------------------------------------------------------------- #

if [ "$COMMAND" = "up" ]; then
    step "Preview $SLUG (branch $BRANCH)"

    #: `<version>+<sha>` rather than the bare version. On a preview the useful
    #: answer to "what is this" is the commit; the semver names a release that has
    #: not happened.
    if [ -z "${APP_VERSION:-}" ]; then
        version=$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)
        sha=$(git rev-parse --short=7 HEAD 2>/dev/null || printf 'unknown')
        APP_VERSION="${version}+${sha}"
        export APP_VERSION
    fi
    info "reporting itself as $APP_VERSION"

    "$REPO_ROOT/scripts/package.sh" --preview
    "$REPO_ROOT/scripts/infra.sh" preview-branch apply --yes

    step "Reading what the preview exposes"
    outputs=$("$REPO_ROOT/scripts/infra.sh" preview-branch output -json 2>/dev/null)
    read_output() {
        printf '%s' "$outputs" | uv run python -c "import json,sys; print(json.load(sys.stdin)['$1']['value'])"
    }
    URL=$(read_output url)
    # A Function URL comes back with a trailing slash today. Normalised rather than
    # relied upon: without this, `${URL}api/health` becomes `...on.awsapi/health`
    # the day it does not, and the smoke below fails for a reason nobody would
    # guess from the message.
    URL="${URL%/}"
    MIGRATE_FUNCTION=$(read_output migrate_function_name)

    # The database does not exist yet: the migration function creates it, because
    # Terraform runs on a runner and the cluster has no address reachable from
    # outside the VPC. First invocation of a preview does both, every later one
    # finds the database already there and only migrates.
    step "Creating and migrating $DATABASE"
    migration_output=$(mktemp)
    trap 'rm -f "$migration_output"' EXIT
    aws lambda invoke \
        --function-name "$MIGRATE_FUNCTION" \
        --cli-binary-format raw-in-base64-out \
        --payload '{}' \
        --cli-read-timeout 360 \
        "$migration_output" >/dev/null

    # A raising Lambda still answers 200, so the payload is what says whether it
    # worked. Same check `deploy.sh` makes, for the same reason.
    if grep -q '"errorMessage"' "$migration_output"; then
        warn "$(cat "$migration_output")"
        die "the migration failed. The preview is up but its database is not ready."
    fi
    ok "$(cat "$migration_output")"

    step "Smoking $URL"
    for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
        if curl -fsS --max-time 30 "$URL/api/health" >/dev/null 2>&1; then
            ok "$URL"

        # A new environment with an empty guest book is a screen nobody can judge,
        # and a preview exists to be looked at. `seed.sh` refuses production and
        # skips a guest book that already has entries, so a re-raised preview is
        # a single GET and a printed line.
        #
        # Not fatal: the preview is up, and a corpus that did not arrive is a
        # thing to notice rather than a thing to roll back.
            step "Seeding from the seed corpus"
            "$REPO_ROOT/scripts/seed.sh" --base-url "$URL/api" ||
                warn "the seed corpus did not go in; the preview itself is up"

            printf '%s\n' "$URL"
            summary "Preview up ($SLUG)" 0
        fi
        info "attempt $attempt: not answering yet (the cluster may be waking)"
        sleep 10
    done
    die "the preview did not answer at $URL/api/health.
    Logs: aws logs tail /aws/lambda/sdd-guestbook-preview-$SLUG-api --since 5m"
fi

# --------------------------------------------------------------------------- #
# down
# --------------------------------------------------------------------------- #

step "Removing preview $SLUG (branch $BRANCH)"

# The stack first. Its functions are what hold connections to the database, and a
# database with a session attached refuses to be dropped.
#
# `destroy` needs no package: `modules/preview_app` guards its `source_code_hash`
# with `fileexists`, precisely so a teardown from a fresh checkout works.
"$REPO_ROOT/scripts/infra.sh" preview-branch destroy --yes

# Then the database, through the function that outlives every preview. Terraform
# never created it, so Terraform cannot remove it.
#
# Best effort: a teardown that already ran, or a preview that never got as far as
# a database, must still end green. That is not laxity -- a merge with
# auto-delete-branch fires both `pull_request: closed` and `delete`, so the second
# run finds nothing and must say so quietly.
step "Dropping $DATABASE"
if maintenance=$(shared_parameter maintenance_function_name 2>/dev/null) && [ -n "$maintenance" ]; then
    drop_output=$(mktemp)
    trap 'rm -f "$drop_output"' EXIT
    if aws lambda invoke \
        --function-name "$maintenance" \
        --cli-binary-format raw-in-base64-out \
        --payload "{\"action\":\"drop\",\"database\":\"$DATABASE\"}" \
        --cli-read-timeout 360 \
        "$drop_output" >/dev/null 2>&1 && ! grep -q '"errorMessage"' "$drop_output"; then
        ok "$(cat "$drop_output")"
    else
        warn "could not drop $DATABASE: $(cat "$drop_output" 2>/dev/null)"
        warn "an orphaned empty database costs storage alone; the maintenance function can be invoked again"
    fi
else
    warn "the shared preview layer published no maintenance function -- $DATABASE was left in place"
fi

summary "Preview down ($SLUG)" 0
