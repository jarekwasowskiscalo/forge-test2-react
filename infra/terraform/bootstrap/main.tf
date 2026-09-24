# What has to exist before Terraform can keep state remotely, plus the role the
# deployment workflow assumes.
#
# **Applied once per AWS account, with LOCAL state**, which is the chicken and
# egg every remote backend has: the bucket that holds the state cannot itself be
# tracked in a state that lives in it. The resulting `terraform.tfstate` in this
# directory is gitignored -- it holds no secret, and re-creating these three
# resources by hand from the console is a five-minute job if it is ever lost.
#
# Nothing here is per-environment. Every root shares one bucket and is separated by
# the `key` in its own `backend.tf` -- except `preview/branch/`, which has one key
# per branch and therefore names none of them.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #

resource "aws_s3_bucket" "state" {
  bucket = var.state_bucket_name

  # No `force_destroy`: this bucket holds the only record of what exists in the
  # account. A `terraform destroy` that emptied it would leave every environment
  # running and unmanageable.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    # The recovery path for a corrupted or truncated state file, and the reason
    # it is worth having a bucket rather than a local file at all.
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Locking is the bucket's own, through `use_lockfile = true` in each backend
# block -- S3 conditional writes, supported since Terraform 1.10. The DynamoDB
# table this used to need is gone: one fewer resource, one fewer bill, and one
# fewer thing to forget when adding an environment.

# --------------------------------------------------------------------------- #
# The role GitHub Actions assumes
# --------------------------------------------------------------------------- #

# OIDC, so no long-lived access key exists anywhere -- not in the repository's
# secrets, not on a laptop, not in a password manager. GitHub presents a signed
# token describing the workflow, and this trust policy decides whether that
# description is one this account accepts.
resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  # GitHub's intermediate CA thumbprint. AWS stopped verifying it for this
  # provider in 2023 and still requires the field; the value is here because it
  # must be, not because anything checks it.
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "deploy_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # **The condition that does the work.** Without a `sub` condition this role is
    # assumable from any workflow in any repository on GitHub. The subjects are
    # listed rather than wildcarded to `repo:owner/name:*`, so a fork or a pull
    # request from one cannot reach it.
    #
    # **Environments only. The `ref:` claims are gone and their absence is the
    # point.** When a job declares an `environment:`, GitHub's `sub` is
    # `repo:O/R:environment:NAME` and no ref claim is presented at all -- so
    # `ref:refs/heads/main` and `ref:refs/tags/v*` could never have been what
    # authorised a deployment. What they COULD have done is let some future job on
    # the trunk take an AdministratorAccess role without passing an environment
    # gate, which is exactly the gate a required reviewer lives on.
    # `tests/fitness/test_deploy_surface.py` keeps this list equal to the set of
    # environments the workflows actually declare.
    #
    # `dev` is gone with the environment; a branch gets a preview instead.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repository}:environment:preview",
        "repo:${var.github_repository}:environment:stage",
        "repo:${var.github_repository}:environment:prod",
      ]
    }
  }
}

resource "aws_iam_role" "deploy" {
  name               = var.deploy_role_name
  description        = "Assumed by this repository's deployment workflow through OIDC."
  assume_role_policy = data.aws_iam_policy_document.deploy_assume.json
}

# **Broad on purpose, and said out loud.** This role creates VPCs, databases,
# functions, buckets and distributions, which is most of what an account can do.
# Narrowing it to the exact set is worthwhile and is a change with its own
# review: written wrong, a too-narrow policy fails in the middle of an apply and
# leaves an environment half-built, which is worse than either extreme.
#
# What keeps it safe today is the trust policy above -- who may assume it -- not
# this document. If that trade is not acceptable for your account, replace this
# attachment with a scoped policy before the first apply.
resource "aws_iam_role_policy_attachment" "deploy" {
  role       = aws_iam_role.deploy.name
  policy_arn = var.deploy_policy_arn
}

# --------------------------------------------------------------------------- #
# The role a preview assumes
# --------------------------------------------------------------------------- #

# A second role for the `preview` environment, and the narrowing that matters is
# not on compute.
#
# Narrowing what a deployment may CREATE is the thing the comment above warns
# against: a policy written slightly wrong fails halfway through an apply. But
# **state isolation is trivially safe to narrow, and state is what actually
# matters** -- `sdd-guestbook/{stage,prod}/terraform.tfstate` contains the Aurora
# master password in cleartext, and a preview has no business reading either.
#
# A `Deny` is the right instrument here where an `Allow` list is not: a Deny
# cannot fail for a permission somebody forgot to grant, so it cannot leave a
# stack half-built. It only ever refuses things a preview should not be doing.
data "aws_iam_policy_document" "preview_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:environment:preview"]
    }
  }
}

resource "aws_iam_role" "preview" {
  name               = var.preview_role_name
  description        = "Assumed by this repository's per-branch preview workflows through OIDC."
  assume_role_policy = data.aws_iam_policy_document.preview_assume.json
}

resource "aws_iam_role_policy_attachment" "preview" {
  role       = aws_iam_role.preview.name
  policy_arn = var.deploy_policy_arn
}

data "aws_iam_policy_document" "preview_denies" {
  statement {
    sid     = "NotTheEnvironmentsState"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      "${aws_s3_bucket.state.arn}/sdd-guestbook/stage/*",
      "${aws_s3_bucket.state.arn}/sdd-guestbook/prod/*",
    ]
  }

  # A preview reads the shared preview cluster's master secret through the branch
  # root, so it cannot be denied Secrets Manager outright. It is denied the
  # environments' secrets by name -- which is the shape `modules/database` gives
  # them: `<project>-<environment>/database/master`.
  statement {
    sid     = "NotTheEnvironmentsSecrets"
    effect  = "Deny"
    actions = ["secretsmanager:*"]
    resources = [
      "arn:aws:secretsmanager:*:*:secret:sdd-guestbook-stage/*",
      "arn:aws:secretsmanager:*:*:secret:sdd-guestbook-prod/*",
    ]
  }
}

resource "aws_iam_role_policy" "preview_denies" {
  name   = "not-the-long-lived-environments"
  role   = aws_iam_role.preview.id
  policy = data.aws_iam_policy_document.preview_denies.json
}

# --------------------------------------------------------------------------- #
# The role a person assumes
# --------------------------------------------------------------------------- #

# **Read-only, and it is the only role a human can assume.** That is what makes
# "only GitHub deploys" a control rather than a convention: the two roles above
# trust GitHub's OIDC provider and nothing else, so no person has credentials to
# apply anything, whatever any script does or does not check.
#
# What it is for: `./scripts/infra.sh <env> plan`, which is the review artefact
# this whole arrangement is built around, and reading a state file to find out
# what exists.
#
# Break-glass is deliberately NOT here. It belongs in IAM, where an account admin
# attaching a policy to themselves for the duration leaves a CloudTrail record --
# not in a shell flag, which leaves none.
data "aws_iam_policy_document" "plan_assume" {
  count = length(var.plan_role_principals) > 0 ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = var.plan_role_principals
    }
  }
}

resource "aws_iam_role" "plan" {
  count              = length(var.plan_role_principals) > 0 ? 1 : 0
  name               = var.plan_role_name
  description        = "Assumed by people. Reads everything, changes nothing."
  assume_role_policy = data.aws_iam_policy_document.plan_assume[0].json
}

resource "aws_iam_role_policy_attachment" "plan_reads" {
  count      = length(var.plan_role_principals) > 0 ? 1 : 0
  role       = aws_iam_role.plan[0].name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# `ReadOnlyAccess` does not include the state bucket's objects, and a plan without
# state is not a plan. Read, never write: a person who could write state could
# make the next apply do anything.
data "aws_iam_policy_document" "plan_reads_state" {
  count = length(var.plan_role_principals) > 0 ? 1 : 0

  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
  }
}

resource "aws_iam_role_policy" "plan_reads_state" {
  count  = length(var.plan_role_principals) > 0 ? 1 : 0
  name   = "read-the-state"
  role   = aws_iam_role.plan[0].id
  policy = data.aws_iam_policy_document.plan_reads_state[0].json
}
