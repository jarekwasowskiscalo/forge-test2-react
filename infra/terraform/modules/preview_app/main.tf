# One branch's copy of the application. Everything a preview creates and nothing
# else -- fifteen resources, all of them fast to create and fast to delete.
#
# **What is deliberately absent is the point.** No VPC, no subnets, no security
# groups, no cluster, no secret, no S3 bucket, no CloudFront distribution. Those
# live once in `infra/terraform/preview/shared/`, and a copy-pasted
# `module "stack"` call here would look entirely reasonable in review while
# costing a VPC and an Aurora cluster per branch -- which the account's five-VPC
# quota stops at the second live preview.
# `tests/fitness/test_infra_layout.py` asserts the absence, because an absence is
# the one kind of mistake a diff does not show.
#
# **The entrypoint is a Lambda Function URL, not an API Gateway.** Two resources
# instead of six, created in one call with no propagation wait, deleted as
# quickly, and with no request charge and no access-log bill. It also imposes no
# 29-second ceiling, which matters precisely here: a preview's first visitor of
# the day waits for a cluster at `min_capacity = 0` to resume.
#
# **Do not put a CDN in front of this URL.** That is the arrangement
# `modules/api/main.tf` rejects for the environments: CloudFront's origin access
# control signs the request without its body, so every read passes and the first
# write fails -- through the CDN only, which is the worst way to find out. A
# preview has no CloudFront and needs none; this note is for whoever later thinks
# it would be an improvement.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

locals {
  # The same user the environments use, for the same reason: it owns nothing, and
  # an IAM token is what it authenticates with.
  app_username = "app_iam"

  # No password: `app/db/iam_auth.py` signs one per connection. Against this
  # branch's own database.
  api_database_url = "postgresql+psycopg://${local.app_username}@${var.database_endpoint}:${var.database_port}/${var.database_name}"

  # Against the CLUSTER's database, not this branch's -- the branch's does not
  # exist yet, and creating it is the first thing this function does.
  migrate_database_url = "postgresql+psycopg://${var.master_username}:${urlencode(var.master_password)}@${var.database_endpoint}:${var.database_port}/${var.maintenance_database}"
}

# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${var.name}-api"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "api_vpc" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# The only thing this function may do besides run: present a signed token as its
# database password. Scoped to one user on one cluster.
data "aws_iam_policy_document" "api_connects" {
  statement {
    effect    = "Allow"
    actions   = ["rds-db:connect"]
    resources = ["${var.database_iam_auth_resource_arn}/${local.app_username}"]
  }
}

resource "aws_iam_role_policy" "api_connects" {
  name   = "connect-as-${local.app_username}"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api_connects.json
}

# The migration function gets no `rds-db:connect`: it authenticates with the
# master password, which it is handed directly.
resource "aws_iam_role" "migrate" {
  name               = "${var.name}-migrate"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "migrate_vpc" {
  role       = aws_iam_role.migrate.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# --------------------------------------------------------------------------- #
# Functions
# --------------------------------------------------------------------------- #

# Declared rather than left to Lambda's implicit creation, so the retention is
# three days rather than forever. A preview that lived a week must not leave logs
# that live longer than the branch did.
resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${var.name}-api"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "migrate" {
  name              = "/aws/lambda/${var.name}-migrate"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_lambda_function" "api" {
  function_name = "${var.name}-api"
  role          = aws_iam_role.api.arn
  handler       = "app.lambda_handler.handler"
  runtime       = "python3.14"
  architectures = ["arm64"]

  filename = var.package_path
  # Guarded, because a teardown runs unattended from a fresh checkout that has no
  # package -- and a destroy that fails on a missing file leaves a live stack
  # nobody is watching. The environments are not guarded this way: a destroy there
  # is a rare, interactive act where a missing artefact is worth stopping for.
  source_code_hash = fileexists(var.package_path) ? filebase64sha256(var.package_path) : null

  timeout     = var.timeout_seconds
  memory_size = var.memory_mb

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL = local.api_database_url
      DB_IAM_AUTH  = "1"
      APP_ENV      = "preview"
      APP_VERSION  = var.app_version
    }
  }

  depends_on = [aws_cloudwatch_log_group.api]
  tags       = var.tags
}

resource "aws_lambda_function" "migrate" {
  function_name = "${var.name}-migrate"
  role          = aws_iam_role.migrate.arn
  handler       = "app.lambda_handler.migrate"
  runtime       = "python3.14"
  architectures = ["arm64"]

  filename         = var.package_path
  source_code_hash = fileexists(var.package_path) ? filebase64sha256(var.package_path) : null

  # Long, because the first invocation waits for a cluster that may have been
  # asleep for a week, then creates a database, then applies every revision.
  timeout     = 300
  memory_size = var.memory_mb

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL = local.migrate_database_url
      # The two variables that make this a preview rather than an environment.
      # `PREVIEW_DATABASE` switches on the create-then-migrate path in
      # `app/lambda_handler.py`; with it absent the code is exactly what stage and
      # prod run.
      PREVIEW_DATABASE = var.database_name
      DB_IAM_USER      = local.app_username
      APP_ENV          = "preview"
      APP_VERSION      = var.app_version
    }
  }

  depends_on = [aws_cloudwatch_log_group.migrate]
  tags       = var.tags
}

# --------------------------------------------------------------------------- #
# The way in
# --------------------------------------------------------------------------- #

# Public and unauthenticated, and that is a decision rather than an oversight.
# `AWS_IAM` authorization would make the URL unopenable in a browser, which is the
# one thing a preview is for. The mitigations are that it is short-lived, that it
# holds only a branch's throwaway database, and that the application refuses
# indexing (see the response header below).
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"
}

# Written explicitly rather than relied upon. The AWS console adds this statement
# for you; the provider's behaviour is the thing to check on a first apply, and a
# distinct statement id makes a duplicate say so plainly instead of colliding.
resource "aws_lambda_permission" "function_url" {
  statement_id           = "AllowPreviewFunctionUrlInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.api.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
