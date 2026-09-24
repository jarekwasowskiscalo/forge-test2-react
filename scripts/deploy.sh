#!/usr/bin/env bash
# A release, in the order the steps have to happen in.
#
# The order is the whole content of this script, and only one direction of it is
# safe: **the schema goes first**. New code against an old schema asks for a
# column that does not exist and fails on every request; old code against a new
# schema ignores a column it does not know about and carries on. So migrate,
# then roll.
#
#   1. build      the Lambda package and the SPA, from this working tree
#   2. apply      the infrastructure, which PUBLISHES a new version of the API
#                 function that nothing routes to yet
#   3. migrate    invoke the migration function and wait for it
#   4. roll       move the alias onto the published version. **The new code goes
#                 live here, and only here**
#   5. sync       the SPA to S3, hashed assets first and index.html last, and
#                 nothing deleted -- the previous release's bundles stay
#   6. invalidate index.html at the edge
#   7. smoke      ask every read-only endpoint the contract declares, through
#                 CloudFront, then record the version that served
#
# Step 4 is what makes step 3's position mean anything. Until it existed, the
# apply in step 2 called UpdateFunctionCode and the new code was serving before
# the migration ran -- the window this header claims to prevent, left open by the
# script that claims it. `infra/terraform/modules/api/main.tf` holds the other
# half: `publish = true` and an alias Terraform creates and never moves.
#
# Steps 4 and 5 have their own ordering rule, for the same reason: index.html
# names the hashed bundles, so uploading it before them serves a page that
# references files that are not there yet.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: deploy.sh <stage|prod> [--skip-build] [--yes]
       deploy.sh <stage|prod> --rollback [--yes]

Builds, applies, migrates and publishes -- in that order, which is the only
order that does not have a window where the code and the schema disagree.

  --skip-build   reuse whatever is in .sdd/build. For a re-run after a failure
                 in a later step; never for a first deploy.
  --yes          the caller has already decided. Required off a terminal, which
                 in practice means required in GitHub Actions.
  --rollback     move the alias back to the last version that actually served and
                 stop. Builds nothing, applies nothing, migrates nothing.

**What --rollback does and does not undo.** It moves one pointer: the alias stops
serving the version it is on and serves the last one that served this environment
and passed its smoke. That is the whole operation, and it takes seconds because the
old version was never deleted.

**"Served" is read from a register, not inferred from the version number.** Every
apply publishes a version, and one that never served -- because the migration failed,
or because somebody ran `infra.sh apply` on its own -- sits above the alias looking
exactly like a release. So a deploy records what served after its smoke passes, and a
rollback reads that record. When it cannot name a target it refuses and says why; it
never falls back to arithmetic.

It does NOT revert the schema, and that is deliberate rather than missing. This
script's whole shape rests on migrating before rolling, precisely because old code
against a new schema ignores a column it does not know about and carries on --
which is what makes rolling the code back safe on its own. A migration run
backwards on a live database is a far more dangerous operation than the one it
would be undoing; if a revision has to go, it goes forward, in a new revision.

It also does not revert the SPA. `index.html` in S3 is overwritten by each deploy,
so the browser keeps the newer shell while the API serves the older version. The
hashed bundles that shell names are still there -- publication is additive -- so the
newer screen loads; whether it gets along with the older API is the contract's
question, and that is what makes this survivable rather than lucky. It is still a
real limit, and it is the reason a rollback is followed by a fix rather than treated
as one.

The overwritten shell is not lost, and that is a separate fact from this script. The
bucket is versioned and keeps the last ten noncurrent versions of a key, so the
previous `index.html` can be recovered by hand from S3. Nothing here does it: object
history is not an automatic rollback, and a `--rollback` that quietly restored a shell
would be undoing a thing it cannot smoke-test. See infra/terraform/modules/web/main.tf.

**Deployments come from GitHub Actions.** Not out of preference: the deployment
role's trust policy names GitHub's OIDC provider and nothing else, so a
workstation has no credentials to do this with. Set SDD_DEPLOY_BREAK_GLASS=1 to
run it anyway, for the day CI itself is the thing that is down.

Needs the AWS CLI and credentials for the account this environment lives in,
taken from the environment exactly as the CLI takes them. Nothing is stored.

Prints the environment's URL at the end. Run `infra.sh <env> plan` first if you
want to see what the infrastructure step will change.
TEXT
}

case "${1:-}" in
    -h|--help|"") usage; exit 0 ;;
esac

ENVIRONMENT="$1"; shift
case "$ENVIRONMENT" in
    stage|prod) ;;
    *) usage >&2; die "unknown environment: $ENVIRONMENT. This releases to stage or prod.
    A branch gets a preview instead: scripts/preview.sh, or Actions -> Preview." ;;
esac

skip_build=0
assume_yes=0
rollback=0
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)    usage; exit 0 ;;
        --skip-build) skip_build=1 ;;
        --yes)        assume_yes=1 ;;
        --rollback)   rollback=1 ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

if [ "$rollback" -eq 1 ] && [ "$skip_build" -eq 1 ]; then
    die "--rollback builds nothing, so --skip-build has nothing to say about it."
fi

#: Both checks come BEFORE the AWS CLI check and before the build, so a refusal
#: costs a second rather than the five minutes a package takes -- and so they can
#: be exercised on a runner that has no AWS CLI at all.
if [ "${GITHUB_ACTIONS:-}" != "true" ] && [ "${SDD_DEPLOY_BREAK_GLASS:-}" != "1" ]; then
    die "deployments come from GitHub Actions: Actions -> Deploy -> Run workflow.
    The deployment role trusts GitHub's OIDC provider and nothing else, so this
    would fail on credentials a few minutes from now anyway.
    Break-glass, when CI is the thing that is down:
    SDD_DEPLOY_BREAK_GLASS=1 ./scripts/deploy.sh $ENVIRONMENT --yes"
fi

if [ "$assume_yes" -eq 0 ] && [ ! -t 0 ]; then
    die "nothing here can confirm the apply. Pass --yes if that is deliberate."
fi

command -v aws >/dev/null 2>&1 ||
    die "the AWS CLI is not on PATH. https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"

WEB_DIR="$REPO_ROOT/.sdd/build/web"

#: Read once, into named variables. `terraform output` is a round trip to S3 for
#: the state, and calling it six times is six round trips and six chances for one
#: of them to disagree with the others.
#:
#: A function rather than a block, because two paths need it and they need it at
#: different moments: a deploy reads AFTER the apply, since the apply is what
#: publishes the version it is about to roll to, while a rollback reads BEFORE
#: doing anything, because it applies nothing. Reading it early for both would
#: break the first deploy of an environment, where there is no state to read yet.
#:
#: No `tail -1`: `terraform output -json` is pretty-printed over many lines, and
#: `infra.sh output` prints nothing after it -- the summary banner every other
#: command ends with is deliberately skipped there, because a banner on stdout
#: after a JSON document is what made `json.load` read "Infra (dev output): OK".
outputs=""
read_outputs() {
    step "Reading what the infrastructure exposes"
    outputs=$("$REPO_ROOT/scripts/infra.sh" "$ENVIRONMENT" output -json 2>/dev/null)
    [ -n "$outputs" ] || die "$ENVIRONMENT exposes nothing. Has it ever been deployed?"
}
read_output() {
    printf '%s' "$outputs" | uv run python -c "import json,sys; print(json.load(sys.stdin)['$1']['value'])"
}

#: The same, for an output an environment may legitimately not have yet: one whose
#: state was written before the output existed. Prints nothing and succeeds, so the
#: caller can say what its absence means -- which is better than a KeyError traceback
#: out of Python in the middle of an incident.
read_output_if_present() {
    printf '%s' "$outputs" |
        uv run python -c "import json,sys; print(json.load(sys.stdin).get('$1',{}).get('value',''))"
}

#: The register of what actually served. Written by a deploy AFTER its smoke passed,
#: read by a rollback -- `scripts/release_manifest.py` holds the rules and says why an
#: alias's own history cannot answer the question. Empty when this environment has no
#: parameter yet, which the rules treat as "no record", not as "no releases".
read_manifest() {
    [ -n "$RELEASE_MANIFEST" ] || { printf ''; return 0; }
    aws ssm get-parameter --name "$RELEASE_MANIFEST" \
        --query 'Parameter.Value' --output text 2>/dev/null || printf ''
}

#: Append one entry and write it back. **Never fatal**: on the deploy path the
#: release is already live and serving by the time this runs, so a register that did
#: not update is a thing to notice rather than a reason to fail a good deployment.
#: The next rollback will say the same thing, in its own words, by refusing.
record_release() {
    local version="$1" from="${2:-}" document digest
    if [ -z "$RELEASE_MANIFEST" ]; then
        warn "this environment exposes no release manifest, so nothing recorded what served.
    Apply the infrastructure once: the parameter and its output arrive with it."
        return 0
    fi
    # **The number is not enough to identify a build.** Replace the function -- a
    # rename, a region, a `terraform destroy` -- and versions restart at 1, so an entry
    # saying "5" would then name entirely different code. The digest is what makes
    # "version 5" checkable at rollback time rather than merely findable.
    digest=$(aws lambda get-function-configuration \
        --function-name "$API_FUNCTION" --qualifier "$version" \
        --output text --query 'CodeSha256' 2>/dev/null) || digest=""

    document=$(read_manifest | uv run python "$REPO_ROOT/scripts/release_manifest.py" append \
        --version "$version" \
        --digest "$digest" \
        --commit "${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)}" \
        --environment "$ENVIRONMENT" \
        ${from:+--rolled-back-from "$from"}) || {
        warn "the release manifest could not be composed; nothing was recorded"
        return 0
    }
    # Non-fatal, and this is the second reason: Parameter Store bounds how many
    # versions of one parameter it keeps, and a long-lived environment can meet that
    # ceiling. A deployment that is live and has passed its smoke must not be reported
    # red by its own bookkeeping -- the rollback refuses instead, which is the safe way
    # round.
    aws ssm put-parameter --name "$RELEASE_MANIFEST" --type String --overwrite \
        --value "$document" --output text >/dev/null 2>&1 ||
        warn "version $version is serving, but $RELEASE_MANIFEST could not be written.
    A rollback will refuse until a deploy records one, which is the safe direction."
    return 0
}

#: Ask the URL until it answers, or give up. Shared by the deploy and the
#: rollback: both change what serves, and neither is finished until a request
#: through CloudFront comes back.
#:
#: Retried, because at min_capacity 0 the first request wakes the database and
#: that takes ten to fifteen seconds.
#:
#: The BODY is read, not discarded, and that is the repair: this used to be
#: `curl -fsS ... >/dev/null`, which asked only whether something answered. The
#: edge was the something. Two `custom_error_response` blocks turned every 403
#: and 404 in front of either origin into `200 text/html` carrying the shell, so
#: an environment whose API was answering nothing at all passed this gate --
#: the one gate whose whole job is to notice. The blocks are gone
#: (`infra/terraform/modules/web/main.tf`); the check stays honest on its own
#: anyway, because a gate that only works while the layer below it is correct is
#: not a gate.
#:
#: `status` is what is looked for because `contracts/openapi/health.yaml` freezes
#: it, and no HTML shell has it.
wait_for_health() {
    local attempt=0 body
    until [ "$attempt" -ge 12 ]; do
        if body=$(curl -fsS --max-time 30 "$1/api/health" 2>/dev/null); then
            case "$body" in
                *'"status"'*) return 0 ;;
            esac
            # Not retried. A wrong answer is not a slow one, and twelve more
            # attempts would only make the log longer before saying the same
            # thing two minutes later.
            warn "$1/api/health answered without the health document -- it came back with: ${body:0:120}"
            return 1
        fi
        attempt=$((attempt + 1))
        info "not yet ($attempt/12) -- the database may be waking up"
        sleep 10
    done
    return 1
}

#: Three read-only questions, asked through CloudFront after anything changes what
#: serves. Deliberately NOT the black box under `e2e/`: that suite empties the
#: target's world before every scenario, through a DIRECT database connection
#: (`e2e/harness/database.py`), so it cannot reach an environment whose database
#: lives in a VPC -- and pointing it at one that it could reach would erase it.
#: Read-only is what makes this safe to run on production, which is exactly where
#: a smoke is worth the most.
#:
#: `/api/health` alone was the whole smoke, and it answers without touching either
#: half of what a deploy actually changed: it reads no row, so it says nothing
#: about the database, and it is served by the function rather than by the edge, so
#: it says nothing about the SPA. Each question below is one of those halves.
post_deploy_smoke() {
    local url="$1"

    step "Asking $url/api/health"
    wait_for_health "$url" || return 1
    ok "the API is answering"

    # The shell, through the distribution. The invalidation in step 6 covers
    # `index.html` and nothing else, so a stale shell here is the most likely way
    # for a deploy to look green and serve the previous release.
    step "Asking $url for the application shell"
    local shell_body
    shell_body=$(curl -fsS --max-time 30 "$url/" 2>/dev/null) || {
        warn "$url/ did not answer -- the API is up, so this is the bucket or the edge"
        return 1
    }
    case "$shell_body" in
        *"<div id=\"root\""*|*"<script"*) ok "the shell is being served" ;;
        *) warn "$url/ answered with something that is not the application shell"; return 1 ;;
    esac

    # The real reads, which are the cheapest questions that reach the database
    # THROUGH the application. **What to ask is read out of the contract rather than
    # written here**, by `scripts/smoke_contract.py`: this block used to carry its own
    # copy -- `/api/entries?limit=1`, and a field `matching` -- and both had been wrong
    # since the day they were typed. A copy is the thing that can drift, so there is
    # no copy any more.
    #
    # `/api/health` is asked twice -- once above as a retry loop, once here against
    # its contract -- and that is deliberate: `wait_for_health` waits, this judges.
    # The contract freezes `environment` and `version` in that body precisely so
    # somebody can ask which release answered, and nothing was checking they arrive.
    local plan path query keys body status
    plan=$(uv run python "$REPO_ROOT/scripts/smoke_contract.py" operations) || {
        warn "contracts/openapi/ could not be read, so this smoke has no question to ask"
        return 1
    }
    # A smoke with nothing to ask passes everything. That is the shape of the defect
    # this whole block replaces, so it is a failure rather than a quiet success.
    [ -n "$plan" ] || {
        warn "contracts/openapi/ declares no read-only endpoint, so nothing here was checked"
        return 1
    }

    while IFS=$'\t' read -r path query keys; do
        [ -n "$path" ] || continue
        step "Asking $url$path$query for the envelope the contract promises"

        # `-w` rather than `-f`: the status and the media type are what tell the three
        # failures apart, and `-f` discards the body, which is the evidence. Three
        # sentences because they are repaired in three different places -- and none of
        # them narrates a cause. The sentence that was here before said "the list
        # endpoint did not answer with the contract's envelope" for a request that had
        # gone to a path nobody serves, and an operator who believed it went looking in
        # the application.
        if ! body=$(curl -sS --max-time 30 -w '\n%{http_code}\n%{content_type}' \
            "$url$path$query" 2>/dev/null); then
            warn "$url$path$query did not answer at all -- nothing came back from the edge"
            return 1
        fi
        media="${body##*$'\n'}"
        body="${body%$'\n'*}"
        status="${body##*$'\n'}"
        body="${body%$'\n'*}"
        if [ "$status" != "200" ]; then
            warn "$url$path$query answered $status, and the contract documents a 200.
    A 404 here is this deployment saying it does not serve that path."
            return 1
        fi
        printf '%s' "$body" |
            uv run python "$REPO_ROOT/scripts/smoke_contract.py" envelope \
                --required "$keys" --media-type "$media" || {
            warn "$url$path$query is not answering what contracts/openapi/ promises"
            return 1
        }
        ok "$path answers with ${keys//,/, }"
    done <<<"$plan"
    return 0
}

# --------------------------------------------------------------------------- #
# --rollback -- one pointer, moved back, and nothing else
# --------------------------------------------------------------------------- #

if [ "$rollback" -eq 1 ]; then
    command -v aws >/dev/null 2>&1 ||
        die "the AWS CLI is not on PATH."
    read_outputs
    API_FUNCTION=$(read_output api_function_name)
    API_ALIAS=$(read_output api_alias_name)
    URL=$(read_output url)
    RELEASE_MANIFEST=$(read_output_if_present release_manifest_parameter)

    current=$(aws lambda get-alias \
        --function-name "$API_FUNCTION" --name "$API_ALIAS" \
        --output text --query 'FunctionVersion')
    if [ -z "$current" ] || [ "$current" = "None" ]; then
        die "$API_ALIAS points at no version. There is nothing to roll back from."
    fi

    # **The target comes from the register of what served, not from arithmetic.**
    # Choosing the highest published version below the alias is what this used to do,
    # and it cannot tell a release from an apply: `publish = true` mints a version on
    # every apply, and anything that stops between the apply and the alias move leaves
    # one that nothing ever routed to. The register is written after a smoke passes,
    # so an entry in it means "this version served this environment and answered the
    # contract" -- and `release_manifest.py` refuses, in a sentence, rather than
    # guessing when it cannot say that about anything.
    #
    # **A refusal here is a real cost during an incident**, because the old behaviour
    # always moved a pointer -- badly, but it moved one. So the refusal carries the way
    # to do it by hand, the way the break-glass refusal above carries its variable: a
    # person who knows which version they want must not be stopped by this script.
    previous=$(read_manifest |
        uv run python "$REPO_ROOT/scripts/release_manifest.py" target --current "$current") ||
        die "$API_FUNCTION cannot be rolled back, and the alias has NOT been moved.
    $API_ALIAS still serves version $current.
    To choose by hand, knowing what you are choosing:
    aws lambda list-versions-by-function --function-name $API_FUNCTION
    aws lambda update-alias --function-name $API_FUNCTION --name $API_ALIAS --function-version N"

    # The register says it served; the account says whether that is still the same
    # build. Existence is the weaker question and not the one that bites: replace the
    # function and version numbers restart at 1, so a recorded "5" would name different
    # code entirely. The digest is compared when the entry carries one -- entries
    # written before this script did are read, not refused.
    expected=$(read_manifest |
        uv run python "$REPO_ROOT/scripts/release_manifest.py" digest --version "$previous")
    found=$(aws lambda get-function-configuration \
        --function-name "$API_FUNCTION" --qualifier "$previous" \
        --output text --query 'CodeSha256' 2>/dev/null) || found=""
    [ -n "$found" ] ||
        die "the release manifest names version $previous as the last one that served,
    and $API_FUNCTION has no such version any more. The alias has NOT been moved."
    if [ -n "$expected" ] && [ "$expected" != "$found" ]; then
        die "version $previous exists, and it is not the build the manifest recorded --
    the function has been replaced since, so its version numbers mean something else now.
    The alias has NOT been moved. Choose by hand:
    aws lambda list-versions-by-function --function-name $API_FUNCTION"
    fi

    warn "rolling $API_FUNCTION from version $current back to $previous"
    warn "the schema stays where it is, and so does the SPA -- see --help"
    if [ "$assume_yes" -eq 0 ]; then
        [ -t 0 ] || die "nothing here can confirm the rollback. Pass --yes if that is deliberate."
        printf 'Roll %s back to version %s? [y/N] ' "$ENVIRONMENT" "$previous"
        read -r answer
        case "$answer" in [yY]*) ;; *) die "nothing was changed." ;; esac
    fi

    step "Rolling $API_FUNCTION back to version $previous"
    aws lambda update-alias \
        --function-name "$API_FUNCTION" \
        --name "$API_ALIAS" \
        --function-version "$previous" \
        --output text --query 'FunctionVersion' >/dev/null
    ok "$API_ALIAS now serves version $previous"

    # **The smoke asks the questions of the tree you are standing on, not of version
    # $previous.** It reads `contracts/openapi/` out of this checkout, so if the trunk
    # has since added an endpoint, the older version is asked for something it never
    # promised -- and that is not a failed rollback. The message says so, because
    # during an incident the wrong reading of this line costs minutes.
    post_deploy_smoke "$URL" ||
        die "rolled back to version $previous, and the smoke still does not pass.
    The version this rolled away from is $current. Two readings, and they look alike:
    the older version is broken, or this checkout's contract is newer than it and asks
    for something it never served. Check which endpoint failed above. Start with:
    aws logs tail /aws/lambda/$API_FUNCTION --since 5m"
    ok "$URL is serving version $previous"

    # The rollback records itself, and records what it rolled AWAY from. That second
    # half is what stops the next rollback of the same incident from walking forward
    # into the release this one was called to escape -- the trap the old numeric
    # choice tried to avoid with a comment and could not.
    record_release "$previous" "$current"
    summary "Rollback ($ENVIRONMENT)" 0
fi

# --------------------------------------------------------------------------- #
# 1. Build
# --------------------------------------------------------------------------- #

if [ "$skip_build" -eq 0 ]; then
    "$REPO_ROOT/scripts/package.sh"
else
    warn "--skip-build: deploying whatever is already in .sdd/build"
    [ -d "$WEB_DIR" ] || die "there is no build to reuse. Drop --skip-build."
fi

# --------------------------------------------------------------------------- #
# 2. Infrastructure
# --------------------------------------------------------------------------- #

#: `--yes` rather than `-auto-approve`: the flag says who decided, and infra.sh
#: turns that into the Terraform flag. Passing `-auto-approve` from here left
#: infra.sh's own question standing in front of it, and that question read a
#: closed stdin and killed the shell before anything could say so.
infra_args=()
if [ "$assume_yes" -eq 1 ]; then
    infra_args=(--yes)
fi
"$REPO_ROOT/scripts/infra.sh" "$ENVIRONMENT" apply ${infra_args[@]+"${infra_args[@]}"}

read_outputs
BUCKET=$(read_output web_bucket)
DISTRIBUTION=$(read_output distribution_id)
MIGRATE_FUNCTION=$(read_output migrate_function_name)
API_FUNCTION=$(read_output api_function_name)
API_ALIAS=$(read_output api_alias_name)
API_VERSION=$(read_output api_published_version)
URL=$(read_output url)
RELEASE_MANIFEST=$(read_output_if_present release_manifest_parameter)
info "$URL"

# --------------------------------------------------------------------------- #
# 3. Migrate -- before the code that needs it starts serving
# --------------------------------------------------------------------------- #

step "Applying migrations ($MIGRATE_FUNCTION)"
migration_output=$(mktemp)
trap 'rm -f "$migration_output"' EXIT
# `--cli-binary-format` because the CLI v2 otherwise expects base64 for a
# payload, and an empty JSON object is what this function takes.
aws lambda invoke \
    --function-name "$MIGRATE_FUNCTION" \
    --cli-binary-format raw-in-base64-out \
    --payload '{}' \
    --cli-read-timeout 360 \
    "$migration_output" >/dev/null

# **A Lambda that raises still returns HTTP 200.** The failure is in the payload,
# under `errorMessage`, and a deploy that only checked the exit code of `aws
# lambda invoke` would call a failed migration a success and then roll the code
# that needs it.
if grep -q '"errorMessage"' "$migration_output"; then
    printf '\n' >&2
    cat "$migration_output" >&2
    printf '\n' >&2
    die "the migration failed. The code has NOT been rolled; the previous version is still serving."
fi
ok "migrations applied"

# --------------------------------------------------------------------------- #
# 4. Roll -- the new code goes live HERE
# --------------------------------------------------------------------------- #

# The migration has succeeded, so the schema is ahead of both versions and the new
# one may now serve. One API call, atomic from a caller's point of view: requests
# in flight finish on the old version and the next one lands on the new.
#
# The migrate function is deliberately NOT behind an alias. It has to be the new
# code -- it is the thing applying the new revisions -- so it runs $LATEST, which
# is what the apply just uploaded.
step "Rolling $API_FUNCTION to version $API_VERSION"
aws lambda update-alias \
    --function-name "$API_FUNCTION" \
    --name "$API_ALIAS" \
    --function-version "$API_VERSION" \
    --output text --query 'FunctionVersion' >/dev/null
ok "$API_ALIAS now serves version $API_VERSION"

# --------------------------------------------------------------------------- #
# 5. Publish the SPA -- hashed assets first, the shell last
# --------------------------------------------------------------------------- #

step "Uploading the hashed assets"
# A year, immutable: every filename under assets/ carries a content hash, so a
# changed file is a changed URL and a cached response can never go stale. This is
# the same header app/main.py sets when it serves them itself.
#
# **Additive, and `--delete` is gone from both syncs deliberately.** `package.sh`
# empties `.sdd/build/web` before it builds, so the source directory holds exactly
# one release -- which made `--delete` remove every bundle of every release before
# it, permanently. Versioning does not undo that: `sync` writes a delete marker, the
# distribution asks for the plain key, and the answer is a 404. The shell that names
# it is still in a browser somewhere, so what that browser gets is a module that
# fails to load: a blank screen, from a deploy that reported itself green.
#
# What the old keys buy: a browser that already loaded the previous shell keeps
# working while a deploy lands, and an alias rolled back still has bundles to serve.
#
# What it costs, named rather than discovered: a root-level file somebody removes
# from the build stays in the bucket, served at its old URL. That is the price of
# never deleting something an older shell may still name, and it is the cheaper
# side of the trade.
# What ages them out is `aws_s3_bucket_lifecycle_configuration` in
# `infra/terraform/modules/web/main.tf`, which says why it touches noncurrent
# versions only.
aws s3 sync "$WEB_DIR/assets" "s3://$BUCKET/assets" \
    --cache-control "public, max-age=31536000, immutable" \
    --only-show-errors

step "Uploading the shell"
# `index.html` keeps a stable URL, so it must never be cached. Uploaded LAST, after
# the bundles it names are already there -- that ordering is what protects the
# direction "forward"; keeping the bundles is what protects the direction "back".
aws s3 sync "$WEB_DIR" "s3://$BUCKET" \
    --exclude "assets/*" \
    --cache-control "no-cache" \
    --only-show-errors

# --------------------------------------------------------------------------- #
# 6. Invalidate -- only the shell
# --------------------------------------------------------------------------- #

step "Invalidating /index.html at the edge"
# Only the shell, not `/*`. The assets are immutable by name and invalidating
# them would be paying to discard a cache that cannot be wrong -- and the first
# thousand paths a month are free, which `/*` spends in one deploy.
invalidation=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION" \
    --paths "/index.html" "/" \
    --query 'Invalidation.Id' --output text)
info "invalidation $invalidation"

# --------------------------------------------------------------------------- #
# 7. Smoke -- through CloudFront, not against the origin
# --------------------------------------------------------------------------- #

step "Asking $URL/api/health"
# Through the distribution deliberately: the origin answering proves the
# function works, and this deploy also changed routing, cache behaviours and a
# bucket policy. The question is whether a browser can reach it.
#
# `wait_for_health` rather than a loop written out here: the rollback path asks
# the same question in the same way, and two copies of a retry loop drift into
# two different definitions of "up".
post_deploy_smoke "$URL" ||
    die "deployed, and the smoke did not pass.
    The infrastructure applied and the migration succeeded, so this is the
    application, the bucket or the routing. Start with: aws logs tail /aws/lambda/$API_FUNCTION --since 5m
    To put the previous version back: ./scripts/deploy.sh $ENVIRONMENT --rollback --yes"

# **Here, and only here.** The entry means "version $API_VERSION served $ENVIRONMENT and
# answered the contract", which is the sentence a rollback needs and the one an alias's
# version history cannot supply: every apply publishes a version, and most of the ones
# above the alias never served anything.
record_release "$API_VERSION"

# A new environment with an empty guest book is a screen nobody can judge.
# `seed.sh` refuses production and skips a guest book that already has entries,
# so on every deploy after the first this is a single GET and a printed line.
#
# Through the script rather than the Python it wraps: one definition of "seed an
# environment", shared with `preview.sh` and `start.sh` (article XII).
#
# Not fatal: the deployment succeeded, and a corpus that did not arrive is a thing
# to notice rather than a thing to roll back.
step "Seeding from the seed corpus, if this environment is new"
"$REPO_ROOT/scripts/seed.sh" --base-url "$URL/api" ||
    warn "the seed corpus did not go in; the deployment itself is fine"

summary "Deploy ($ENVIRONMENT)" 0
