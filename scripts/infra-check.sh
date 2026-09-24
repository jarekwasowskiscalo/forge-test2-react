#!/usr/bin/env bash
# The infrastructure, checked the way the application is: format and types.
#
# Three questions, no credentials and no state:
#   * is every .tf file in canonical form (`terraform fmt`)
#   * does every root parse and type-check (`terraform validate`)
#   * is every parameter this stack does NOT support still refused by name
#     (`terraform validate`, on a root that exists to fail)
#
# `validate` runs with `-backend=false`, so it never reaches S3 and never needs
# an AWS account. That is what makes this a gate on every pull request rather
# than something only a person with keys can run.
#
# What it deliberately does NOT do is `plan`. A plan reads live state and reports
# what would change in a real environment -- which is a question about an
# account, not about a commit, and answering it in CI would need credentials on
# every pull request including one from a fork.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: infra-check.sh [--no-docker]

  (no argument)  terraform fmt -check and terraform validate, every root, plus
                 the refusal roots, where validate is required to FAIL
  --no-docker    do not reach for the pinned image. Without a local Terraform of
                 the pinned version this then has nothing to run, so it records
                 a NAMED GAP and exits 4 (INCOMPLETE) rather than 0 or 1.

Run by check.sh as one of its gates, and by CI's `infra` job as the same script.
TEXT
}

no_docker=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --no-docker) no_docker=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

#: Every directory Terraform is ever pointed at and expected to ACCEPT. Modules are
#: not roots: they are called rather than initialised, and `validate` on one in
#: isolation reports missing variables that its caller supplies.
ROOTS=(bootstrap preview/shared preview/branch envs/stage envs/prod)

#: The roots that must be REJECTED, under infra/terraform/refusals/. Each one sets a
#: module parameter this stack declares unsupported, so `validate` PASSING is the
#: failure -- which is why they cannot share the loop above. They are deliberately
#: absent from ROOTS and from scripts/infra.sh: nothing here is ever planned or
#: applied. Each directory's own header says what it is for, and
#: tests/fitness/test_infra_layout.py holds this list against the tree.
#:
#: `<root>|<phrase>`, because the phrase is half the check and an associative array
#: would not survive the trip: macOS ships bash 3.2, which has none. Each phrase is
#: what that refusal must SAY, not merely that it happened -- a root that failed for
#: another reason (a typo, a module moved out from under it, a provider that would
#: not install) exits non-zero too, and reporting that as the barrier working is how
#: a barrier quietly stops existing.
REFUSALS=(
    "refusals/database-proxy|enable_proxy is not implemented"
)

# Captured, then compared: `terraform version | head -1 | grep -q` read a terraform that
# could not answer, or one `head` cut off with SIGPIPE, as "not the pinned version".
have_local=0
if command -v terraform >/dev/null 2>&1 &&
   tf_version="$(terraform version 2>/dev/null)" &&
   [[ "${tf_version%%$'\n'*}" == *"v${TERRAFORM_VERSION}" ]]; then
    have_local=1
fi

if [ "$have_local" -eq 0 ] && { [ "$no_docker" -eq 1 ] || ! docker_usable; }; then
    warn "no Terraform v${TERRAFORM_VERSION} and no usable Docker -- the infrastructure was not checked"
    summary "Infrastructure" 4
fi

run_tf() {
    local workdir="$1"; shift
    if [ "$have_local" -eq 1 ]; then
        (cd "$REPO_ROOT/infra/terraform/$workdir" && terraform "$@")
    else
        docker run --rm \
            -v "$REPO_ROOT/infra:/infra" -w "/infra/terraform/$workdir" \
            "hashicorp/terraform:${TERRAFORM_VERSION}" "$@"
    fi
}

step "terraform fmt -check"
# One call over the whole tree, including the modules: formatting is a property
# of a file, not of a root.
run_tf "." fmt -check -recursive -diff ||
    die "some .tf files are not in canonical form. Fix them with: ./scripts/infra.sh stage fmt"
ok "every .tf file is canonical"

for root in "${ROOTS[@]}"; do
    step "terraform validate ($root)"
    run_tf "$root" init -backend=false -input=false -no-color >/dev/null
    run_tf "$root" validate -no-color
done

# The negative half, and it only means anything after the loop above: those five
# roots all pass the same parameters with the supported values, so THEY are the
# proof that the barriers below refuse one value rather than every value.
for entry in ${REFUSALS[@]+"${REFUSALS[@]}"}; do
    root="${entry%%|*}"
    expected="${entry#*|}"
    step "terraform validate refuses $root"
    run_tf "$root" init -backend=false -input=false -no-color >/dev/null

    if output="$(run_tf "$root" validate -no-color 2>&1)"; then
        die "$root was ACCEPTED. It sets a parameter that is supposed to be refused, so the barrier on it is gone -- and the switch it guards produces a stack that cannot connect. Expected a refusal naming: $expected"
    fi
    # Squeezed to single spaces first: Terraform wraps an `error_message` to the
    # terminal width, so a match against a sentence would otherwise pass or fail
    # depending on how wide the window was.
    # Normalised into a variable and matched by the shell, not `printf | tr | grep -qF`:
    # grep quits at the first match, and the stage still writing then fails on EPIPE,
    # which `pipefail` reads as "the reason is not there".
    normalized="$(tr -s '[:space:]' ' ' <<<"$output")"
    if [[ "$normalized" != *"$expected"* ]]; then
        die "$root was refused, but for the wrong reason: nothing in the output named \"$expected\". Terraform said: $output"
    fi
    ok "$root is refused, and the message names the reason"
done

summary "Infrastructure" 0
