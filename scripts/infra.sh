#!/usr/bin/env bash
# Terraform, with the environment named first and the destructive verbs guarded.
#
# Article XII: the script is the interface. A raw `terraform apply` in
# infra/terraform/envs/prod works and is exactly the shape of the mistake this
# wraps -- one `cd` into the wrong directory and the wrong environment is
# changed, with the confirmation prompt looking identical either way.
#
# Terraform is PINNED (`TERRAFORM_VERSION` in _lib.sh) and run through Docker
# when the pinned version is not on PATH, the same arrangement hygiene.sh uses
# for shellcheck and actionlint. The pin matters more here than for a linter:
# two Terraform versions write two state formats, and the newer one locks the
# older out of the state for everybody.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: infra.sh <stage|prod> <command> [terraform arguments...]
       infra.sh <bootstrap|preview-shared> <command> [terraform arguments...]
       PREVIEW_SLUG=<slug> infra.sh preview-branch <command> [terraform arguments...]

  init        Download providers and configure the remote state backend.
  fmt         Rewrite every .tf file into canonical form, over the WHOLE tree
              (modules included) whatever environment is named. Checks nothing.
  validate    Parse and type-check, with no credentials and no state.
  plan        What an apply WOULD do. Reads state, changes nothing.
  apply       Make it so. Asks first on stage and prod.
  destroy     Take it down. Asks first everywhere, twice on prod.
  output      What this environment exposes: its URL, its bucket, its functions.

  --yes       The caller has already answered the question this script would ask.
              For apply and destroy, from a pipeline. It is read here and never
              reaches Terraform, so `-auto-approve` stays out of shell history.
              It cannot reach `prod destroy`, which a person types or nobody does.

Two roots are not environments and are applied once per account:

  bootstrap        the state bucket and the roles GitHub Actions assumes. It keeps
                   its state LOCALLY -- the bucket that holds every other state
                   cannot hold its own.
  preview-shared   the network and the database cluster every per-branch preview
                   borrows. It replaced `dev`.

  preview-branch   ONE branch's preview. Applied many times over one root, so its
                   state key is not written down -- it comes from PREVIEW_SLUG,
                   which `scripts/preview.sh` computes from the branch name. Use
                   that script rather than this: it also builds the right package
                   and runs the migration afterwards.

plan and apply need the Lambda package, so they build it first unless
.sdd/build/lambda.zip is already current. Nothing here uploads anything: use
deploy.sh, which does the whole release in the right order.

Credentials come from the environment exactly as the AWS CLI takes them
(AWS_PROFILE, AWS_ACCESS_KEY_ID, SSO, an assumed role). This script sets none
and stores none.
TEXT
}

case "${1:-}" in
    -h|--help|"") usage; exit 0 ;;
esac

ENVIRONMENT="$1"; shift
COMMAND="${1:-}"; shift || true

case "$ENVIRONMENT" in
    stage|prod)     ROOT="infra/terraform/envs/$ENVIRONMENT" ;;
    bootstrap)      ROOT="infra/terraform/bootstrap" ;;
    preview-shared) ROOT="infra/terraform/preview/shared" ;;
    preview-branch) ROOT="infra/terraform/preview/branch" ;;
    *)
        usage >&2
        die "unknown environment: $ENVIRONMENT. The long-lived environments are stage and prod,
    plus the two per-account roots bootstrap and preview-shared. 'dev' is gone: a branch
    gets a preview instead (scripts/preview.sh).
    A further environment is a directory under infra/terraform/envs/ and a key in its
    backend.tf, not a flag."
        ;;
esac

[ -n "$COMMAND" ] || { usage >&2; die "no command. See the list above."; }

#: `fmt` is the one command that is not about a root: canonical form is a property
#: of a FILE, and infra-check.sh checks every file including the modules. Pointing
#: people at `infra.sh <env> fmt` while it could only reach that one directory is
#: how a "fix it with this" message came to not fix it. Set here, before
#: resolve_terraform bakes the path into the container's working directory.
if [ "$COMMAND" = "fmt" ]; then
    ROOT="infra/terraform"
fi

#: `--yes` is this script's flag, not Terraform's. It comes out of the argument
#: list here so everything left in `tf_args` is exactly what the operator meant
#: Terraform itself to see.
assume_yes=0
tf_args=()
for arg in "$@"; do
    case "$arg" in
        --yes) assume_yes=1 ;;
        *)     tf_args+=("$arg") ;;
    esac
done

#: Where the Lambda package lands. Passed to Terraform as `package_path`, which
#: has no default on purpose: an apply must never deploy whatever happens to be
#: left in .sdd/build from another branch.
PACKAGE="$REPO_ROOT/.sdd/build/lambda.zip"

#: How Terraform is run: the pinned binary if this machine has it, the pinned
#: image otherwise. Written as an array so the two forms are one call site.
terraform_cmd=()
resolve_terraform() {
    # Captured, then compared, rather than `terraform version | head -1 | grep -q`: that
    # pipeline read a terraform which could not answer -- or one that `head` cut off
    # with SIGPIPE -- as "the wrong version", and the message below then named one.
    local tf_version="" tf_first=""
    if command -v terraform >/dev/null 2>&1; then
        tf_version="$(terraform version 2>/dev/null)" || tf_version=""
        tf_first="${tf_version%%$'\n'*}"
    fi
    if [[ "$tf_first" == *"v${TERRAFORM_VERSION}" ]]; then
        terraform_cmd=(terraform)
        return 0
    fi
    if command -v terraform >/dev/null 2>&1; then
        if [ -n "$tf_first" ]; then
            info "terraform on PATH is $tf_first, and this project pins v${TERRAFORM_VERSION}"
        else
            info "terraform on PATH did not answer \`terraform version\`, so the pinned image is used"
        fi
    fi
    docker_usable ||
        die "no Terraform v${TERRAFORM_VERSION} on PATH and $DOCKER_UNUSABLE_REASON.
    Install that exact version, or start Docker and this script will use the pinned image.
    The version is not a preference: state written by a newer Terraform cannot be read by an older one."
    info "using the pinned image hashicorp/terraform:${TERRAFORM_VERSION}"
    # The AWS variables are forwarded rather than the whole environment: a
    # container that inherited everything would also inherit DATABASE_URL, and
    # a Terraform run has no business seeing one.
    terraform_cmd=(
        docker run --rm -i
        -v "$REPO_ROOT:/repo" -w "/repo/$ROOT"
        -v "$HOME/.aws:/root/.aws:ro"
        -e AWS_PROFILE -e AWS_REGION -e AWS_DEFAULT_REGION
        -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN
        "hashicorp/terraform:${TERRAFORM_VERSION}"
    )
}

#: `${a[@]+"${a[@]}"}` rather than `"${a[@]}"`, everywhere an array can be empty.
#: bash 3.2 -- which is what macOS ships, and what the cross-platform CI leg runs --
#: treats the expansion of an EMPTY array under `set -u` as an unbound variable and
#: kills the script. The longer form expands to nothing instead of to an error.
run_terraform() {
    if [ "${terraform_cmd[0]}" = "terraform" ]; then
        (cd "$ROOT" && terraform "$@")
    else
        "${terraform_cmd[@]}" "$@"
    fi
}

#: One root is applied many times, and everything that follows from that is here.
#:
#: Its `backend.tf` carries no `key`, so `init` supplies one -- a state file per
#: branch, under a prefix that can be listed and expired by a bucket lifecycle
#: rule. `-reconfigure` because the same working directory is re-initialised
#: against a different key every time, and without it Terraform offers to migrate
#: the previous branch's state into this one's.
#:
#: The prefix is the literal the other roots' backend blocks carry, because a
#: backend block cannot take a variable and this one has to match them.
init_args=()
preview_vars=()
if [ "$ENVIRONMENT" = "preview-branch" ]; then
    [ -n "${PREVIEW_SLUG:-}" ] ||
        die "preview-branch needs PREVIEW_SLUG: it is the state key and half of every resource name.
    ./scripts/preview.sh computes one from a branch name; do not invent one."
    init_args=(
        -reconfigure
        -backend-config="key=sdd-guestbook/preview/${PREVIEW_SLUG}/terraform.tfstate"
    )
    preview_vars=(
        -var "slug=${PREVIEW_SLUG}"
        -var "branch=${PREVIEW_BRANCH:-}"
    )
fi

#: Where Terraform will find the package -- which depends on WHO runs Terraform.
#: The pinned image sees the repository mounted at /repo; the host binary sees it
#: where it is. One literal for both used to be the container's path, so the
#: host branch handed `filebase64sha256()` a file that did not exist.
#: A preview takes the OTHER zip -- the one that carries the SPA, because a
#: preview has no CloudFront distribution to serve it from.
package_var() {
    local name="lambda.zip"
    if [ "$ENVIRONMENT" = "preview-branch" ]; then
        name="lambda-preview.zip"
    fi
    if [ "${terraform_cmd[0]}" = "terraform" ]; then
        printf 'package_path=%s/.sdd/build/%s' "$REPO_ROOT" "$name"
    else
        printf 'package_path=/repo/.sdd/build/%s' "$name"
    fi
}

#: Before anything reads `terraform_cmd`, which `package_var` below does. It used
#: to be called just above the `case`, after `root_vars` had already asked which
#: Terraform was chosen -- so every command against dev, stage or prod died on
#: `terraform_cmd[0]: unbound variable` before it did anything. Only `bootstrap`
#: escaped it, by being the one environment that builds no `-var` list at all.
resolve_terraform

#: The release this deployment will report at /api/health. Read from
#: pyproject.toml with no toolchain, because this script answers --help on a bare
#: runner and must not need one. An APP_VERSION already in the environment wins:
#: that is how a preview says `<version>+<sha>`, where a bare semver would name a
#: release that has not happened.
app_version() {
    if [ -n "${APP_VERSION:-}" ]; then
        printf '%s' "$APP_VERSION"
        return 0
    fi
    grep -m1 '^version = ' "$REPO_ROOT/pyproject.toml" | cut -d'"' -f2
}

#: The environment roots declare `package_path` and `app_version`; `bootstrap`
#: declares neither, and Terraform refuses a `-var` for a variable the root never
#: declared. So both are passed for environments only -- bootstrap creates the
#: state bucket and the deploy role, and has no function to give a zip or a
#: version to.
root_vars=()
if [ "$ENVIRONMENT" != "bootstrap" ]; then
    root_vars=(-var "$(package_var)" -var "app_version=$(app_version)")
    root_vars+=(${preview_vars[@]+"${preview_vars[@]}"})
fi

#: A yes/no the operator has to type in full. The question belongs to a person;
#: `--yes` is how a caller that was triggered on purpose says it has already been
#: answered. `-auto-approve` is still not offered directly, so it stays out of
#: shell history -- what a pipeline passes is an intent, not a Terraform flag.
confirm() {
    local question="$1" expected="$2" answer
    #: Without this, `read` on a closed stdin returns 1 and `set -e` kills the
    #: shell BEFORE `die` can print anything. That is how a deployment from
    #: GitHub Actions failed with exit 1 and not one word saying why.
    [ -t 0 ] || die "there is nobody here to answer that, and this script will not guess.
    A caller that meant it says so: infra.sh $ENVIRONMENT $COMMAND --yes"
    printf '\n%s%s%s\n' "$_C_BOLD" "$question" "$_C_OFF" >&2
    printf 'Type %s to continue: ' "$expected" >&2
    read -r answer
    [ "$answer" = "$expected" ] || die "answer was not $expected -- nothing was done."
}

ensure_package() {
    if [ "$ENVIRONMENT" = "preview-branch" ]; then
        [ -f "$REPO_ROOT/.sdd/build/lambda-preview.zip" ] && return 0
        step "No preview package yet -- building one"
        "$REPO_ROOT/scripts/package.sh" --preview
        return 0
    fi
    [ -f "$PACKAGE" ] && return 0
    step "No Lambda package yet -- building one"
    "$REPO_ROOT/scripts/package.sh" --lambda
}

case "$COMMAND" in
    fmt)
        step "terraform fmt (every root and every module)"
        run_terraform fmt -recursive ${tf_args[@]+"${tf_args[@]}"}
        ;;

    validate)
        # `-backend=false` so this needs no credentials and no state: it is a
        # syntax and type check, and CI runs it on every pull request.
        step "terraform validate ($ENVIRONMENT)"
        run_terraform init -backend=false -input=false >/dev/null
        run_terraform validate ${tf_args[@]+"${tf_args[@]}"}
        ;;

    init)
        step "terraform init ($ENVIRONMENT)"
        run_terraform init -input=false ${init_args[@]+"${init_args[@]}"} ${tf_args[@]+"${tf_args[@]}"}
        ;;

    plan)
        [ "$ENVIRONMENT" = "bootstrap" ] || ensure_package
        step "terraform plan ($ENVIRONMENT)"
        run_terraform init -input=false ${init_args[@]+"${init_args[@]}"} >/dev/null
        run_terraform plan -input=false ${root_vars[@]+"${root_vars[@]}"} ${tf_args[@]+"${tf_args[@]}"}
        ;;

    apply)
        [ "$ENVIRONMENT" = "bootstrap" ] || ensure_package
        #: Exactly one thing asks. With --yes this script has its answer and
        #: Terraform must not ask again; without it the question is a person's, so
        #: `-input=false` comes OFF and Terraform puts its own plan up for
        #: approval. Nothing else can prompt: every variable is passed with -var
        #: or has a default.
        approval=()
        if [ "$assume_yes" -eq 1 ]; then
            approval=(-input=false -auto-approve)
        else
            case "$ENVIRONMENT" in
                stage|prod) confirm "About to change $ENVIRONMENT. Run 'infra.sh $ENVIRONMENT plan' first if you have not." "$ENVIRONMENT" ;;
            esac
        fi
        step "terraform apply ($ENVIRONMENT)"
        run_terraform init -input=false ${init_args[@]+"${init_args[@]}"} >/dev/null
        run_terraform apply ${approval[@]+"${approval[@]}"} ${root_vars[@]+"${root_vars[@]}"} ${tf_args[@]+"${tf_args[@]}"}
        ;;

    destroy)
        approval=()
        if [ "$ENVIRONMENT" = "prod" ]; then
            #: `--yes` answers for the other environments and must not be able to
            #: reach this one, which is why the check is here rather than inside
            #: `confirm`: production is destroyed by a person or by nobody.
            [ -t 0 ] || die "production is not destroyed by a pipeline. Somebody types this one."
            confirm "About to DESTROY $ENVIRONMENT. This deletes the database." "$ENVIRONMENT"
            # Twice, because prod holds the data whose loss is not recoverable by
            # re-running anything. The second question is not ceremony: the first
            # one is answered by muscle memory.
            confirm "This is PRODUCTION. Say so." "destroy production"
        elif [ "$assume_yes" -eq 1 ]; then
            approval=(-input=false -auto-approve)
        else
            confirm "About to DESTROY $ENVIRONMENT. This deletes the database." "$ENVIRONMENT"
        fi
        step "terraform destroy ($ENVIRONMENT)"
        run_terraform init -input=false ${init_args[@]+"${init_args[@]}"} >/dev/null
        run_terraform destroy ${approval[@]+"${approval[@]}"} ${root_vars[@]+"${root_vars[@]}"} ${tf_args[@]+"${tf_args[@]}"}
        ;;

    output)
        # No summary banner after this one: its stdout IS the result, and
        # `deploy.sh` feeds it to `json.load`. A banner after a JSON document
        # turned every read into a parse error of "Infra (dev output): OK".
        run_terraform init -input=false ${init_args[@]+"${init_args[@]}"} >/dev/null
        run_terraform output ${tf_args[@]+"${tf_args[@]}"}
        exit $?
        ;;

    *)
        usage >&2
        die "unknown command: $COMMAND"
        ;;
esac

summary "Infra ($ENVIRONMENT $COMMAND)" 0
