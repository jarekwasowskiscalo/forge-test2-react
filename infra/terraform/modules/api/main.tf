# The backend: two functions from one deployment package, behind one HTTP API.
#
# **Two functions, one zip.** `app.lambda_handler.handler` answers requests;
# `app.lambda_handler.migrate` applies migrations as a release step. They share a
# package because a migration built from a different commit than the code it
# prepares is the failure this arrangement makes unrepresentable -- and they are
# separate functions because they need different rights, different timeouts and
# different triggers.
#
# **The two authenticate differently, and that asymmetry is the design.** The API
# function holds no password at all: it signs an IAM token locally, so it needs
# no route to Secrets Manager and the VPC needs no NAT gateway. The migration
# function does hold the master credentials, because it performs DDL and because
# it is what grants the API's role its database login in the first place. One
# runs on every request; the other runs once per release, from a workflow.

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
  # The user the API function logs in as. Distinct from the master user on
  # purpose: it owns nothing, and `GRANT rds_iam` is what lets it authenticate
  # with a token at all.
  app_username = "app_iam"

  # `postgresql+psycopg://` and no password: `app/db/iam_auth.py` fills the
  # password in per connection. A URL with an empty password field is what
  # SQLAlchemy needs to parse a username out at all.
  api_database_url = "postgresql+psycopg://${local.app_username}@${var.database_endpoint}:${var.database_port}/${var.database_name}"

  # `database_cluster_endpoint`, not `database_endpoint`: this one carries a
  # password, and where a proxy exists the endpoint output IS the proxy, which
  # refuses a password against an `iam_auth = "REQUIRED"` entry.
  migrate_database_url = "postgresql+psycopg://${var.master_username}:${urlencode(var.master_password)}@${var.database_cluster_endpoint}:${var.database_port}/${var.database_name}"
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

resource "aws_iam_role" "migrate" {
  name               = "${var.name}-migrate"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

# The managed policy that lets a function in a VPC create and delete the network
# interfaces it needs. Without it the function is created successfully and every
# invocation times out with no log line at all, because it never gets far enough
# to write one.
resource "aws_iam_role_policy_attachment" "api_vpc" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "migrate_vpc" {
  role       = aws_iam_role.migrate.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "api_connects_with_a_token" {
  name = "rds-iam-connect"
  role = aws_iam_role.api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["rds-db:connect"]
      Resource = "${var.database_iam_auth_resource_arn}/${local.app_username}"
    }]
  })
}

# --------------------------------------------------------------------------- #
# Functions
# --------------------------------------------------------------------------- #

# Explicit log groups, so retention is a decision rather than "forever". Created
# here rather than left to Lambda: a group Lambda makes for itself has no
# retention and no tags, and setting either afterwards means importing it.
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
  # Graviton: cheaper per millisecond than x86 and, for a workload that is mostly
  # waiting on a database, no slower. `scripts/package.sh` resolves wheels for
  # this architecture, and the two must agree or the function cannot import
  # psycopg.
  architectures = ["arm64"]

  filename         = var.package_path
  source_code_hash = filebase64sha256(var.package_path)

  # **The half of the deployment order that Terraform owns.** An apply used to
  # call UpdateFunctionCode and the new code was serving immediately -- before the
  # migration, which is step 3 of `scripts/deploy.sh`. New code over an old schema
  # asks for a column that does not exist, which is the exact window that script's
  # header says it exists to prevent, and it existed anyway.
  #
  # Publishing makes each apply an immutable, numbered version that NOTHING routes
  # to yet. The alias below is what routes, and `deploy.sh` moves it after the
  # migration has succeeded.
  publish = true

  # Thirty seconds because the database may be asleep. At `min_capacity = 0`
  # Aurora takes ten to fifteen seconds to resume, and a function that timed out
  # at the default three would turn every first-visit-of-the-morning into an
  # error page.
  timeout     = var.timeout_seconds
  memory_size = var.memory_mb

  # What stands in for an RDS Proxy, and stands stricter. app/db/session.py holds
  # exactly one connection per execution environment, so this function's
  # concurrency IS its connection count against the cluster -- a ceiling here
  # forbids the storm a proxy would merely have queued, and costs nothing an hour.
  reserved_concurrent_executions = var.reserved_concurrency

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL = local.api_database_url
      DB_IAM_AUTH  = "1"
      APP_ENV      = var.environment
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
  source_code_hash = filebase64sha256(var.package_path)

  # Long, because this one waits for the cluster to resume AND then applies
  # however many revisions have accumulated. It runs once per release, so a
  # generous ceiling costs nothing.
  timeout     = 300
  memory_size = var.memory_mb

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL = local.migrate_database_url
      # The user it must create and grant `rds_iam` to, so the API function can
      # log in with a token. Doing it here rather than by hand keeps the whole
      # thing reachable: the cluster has no public address, so there is no `psql`
      # anybody could run against it from outside.
      DB_IAM_USER = local.app_username
      APP_ENV     = var.environment
      APP_VERSION = var.app_version
    }
  }

  depends_on = [aws_cloudwatch_log_group.migrate]
  tags       = var.tags
}

# The thing the gateway actually routes to, and the reason the order in
# `scripts/deploy.sh` is now true rather than merely stated.
#
# **Terraform creates it and then leaves it alone.** `ignore_changes` is not a
# workaround here, it is the design: moving the alias is a step in a sequence
# (apply, migrate, THEN roll), and Terraform has no way to express "create this
# version but do not route to it yet" other than by not owning where it points.
# `deploy.sh` moves it with `aws lambda update-alias`, once.
#
# What this buys, concretely: if the migration fails, the alias never moves, the
# previous version is still serving, and it is serving over the schema it was
# built for. That sentence is in `deploy.sh`'s failure message and was not true
# until this resource existed.
resource "aws_lambda_alias" "api" {
  name             = "live"
  description      = "What the gateway routes to. Moved by scripts/deploy.sh after the migration."
  function_name    = aws_lambda_function.api.function_name
  function_version = aws_lambda_function.api.version

  lifecycle {
    ignore_changes = [function_version]
  }
}

# --------------------------------------------------------------------------- #
# HTTP API
# --------------------------------------------------------------------------- #

# An HTTP API rather than a Lambda function URL, and the reason is specific:
# CloudFront's origin access control signs requests to a function URL WITHOUT the
# body. This application POSTs, PATCHes and DELETEs with bodies, so that
# arrangement works for every read and fails on the first write -- through the
# CDN only, which is the hardest place to notice it. An HTTP API has no such
# gap and costs about a dollar per million requests.
resource "aws_apigatewayv2_api" "this" {
  name          = var.name
  protocol_type = "HTTP"

  # No CORS configuration, deliberately. The browser reaches this through the
  # same CloudFront domain that serves the SPA, so every request is same-origin
  # -- which is the property spec/design/architecture.md § Deployment moved here from the single-process
  # arrangement rather than giving up.

  tags = var.tags
}

resource "aws_apigatewayv2_integration" "api" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  # The alias, not the function: `aws_lambda_function.invoke_arn` resolves to
  # $LATEST, which is whatever the last apply uploaded -- the version this whole
  # arrangement exists to stop serving before its migration has run.
  integration_uri        = aws_lambda_alias.api.invoke_arn
  payload_format_version = "2.0"
  # Slightly under the function's own timeout, so a slow request is reported by
  # the gateway as a gateway timeout rather than being cut off mid-response.
  timeout_milliseconds = min(var.timeout_seconds * 1000, 29000)
}

resource "aws_apigatewayv2_route" "everything" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    # Deliberately structural: method, path, status, latency. No query string and
    # no body -- Article XI of the constitution keeps personal data out of
    # artefacts, and an access log is an artefact that is kept for weeks.
    format = jsonencode({
      requestId   = "$context.requestId"
      httpMethod  = "$context.httpMethod"
      routeKey    = "$context.routeKey"
      status      = "$context.status"
      latency     = "$context.responseLatency"
      integration = "$context.integrationErrorMessage"
    })
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/aws/apigateway/${var.name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_lambda_permission" "gateway" {
  statement_id  = "AllowInvokeFromHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  # Scoped to the alias, because that is what is invoked. Without the qualifier the
  # permission is on the unqualified function and the gateway's call to `live` is
  # refused -- as a 500 from the integration, which reads like the application.
  qualifier  = aws_lambda_alias.api.name
  principal  = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
