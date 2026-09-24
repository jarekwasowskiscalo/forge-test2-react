# This account's bootstrap values. Applied once per AWS account, by
# `./scripts/infra.sh bootstrap apply`. The form to copy for a different account
# is `terraform.tfvars.example` beside this file.
#
# **Committed on purpose.** Neither value is a secret -- the bucket name is
# already a literal in four `backend.tf` files and the repository is the git
# remote -- and an account whose settings are written down is an account whose
# next operator does not have to guess. What IS gitignored is the state this
# directory writes locally, and `*.tfvars.local` for anything that genuinely
# should not be here.

# Globally unique across all of S3. This exact string is also the `bucket` line
# of all FOUR backend blocks: envs/stage, envs/prod, preview/shared and
# preview/branch. A backend takes no variables, so it is copied by hand.
state_bucket_name = "test-jw-app-sdd-cc-1"

# owner/name. Decides which workflows may assume the deploy role, and it is the
# ONLY thing standing between that role and any workflow on GitHub.
#
# **The AWS side has not caught up yet.** This value moved to the Scalo
# organisation on 2026-09-10 with the rest of the repository; the trust policy
# already in the account still names the repository it was applied with. Until
# `./scripts/infra.sh bootstrap apply` runs against this file, a deploy from
# here is refused by STS -- which is the safe direction for the two to disagree
# in, and the reason the value moved rather than waiting for the apply.
github_repository = "Scalo-Sales-Engineering-Consulting/forge_template_python_react"

# Set to false if this account already has GitHub's OIDC provider. There can be
# only one per account, and a second apply that tries to create it fails with
# EntityAlreadyExists.
# create_oidc_provider = true
