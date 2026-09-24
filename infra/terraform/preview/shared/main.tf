# Everything every preview borrows, applied once per account.
#
# **A preview is a branch's copy of the application, not a copy of the account.**
# That distinction is this file. A full stack per branch would be a VPC, an Aurora
# cluster, an S3 bucket and a CloudFront distribution each -- fifteen to twenty
# minutes to create, as long again to destroy, a globally unique bucket name to
# collide on, and a five-VPC quota reached at the second live branch. So the
# expensive, slow, quota-bound half lives here and is created once; a branch gets
# a Lambda, a URL and a database on this cluster, which is seconds either way.
#
# It replaces `dev`, and took `dev`'s place in the VPC count rather than adding to
# it. Nothing here is per-branch: `infra/terraform/preview/branch/` is.
#
# **What a branch reads is a contract, not a state file.** The parameters at the
# bottom are the whole of what this layer promises. A `terraform_remote_state`
# data source would have been shorter and is deliberately not used: it reads the
# producing root's entire state object, which holds `random_password.master` in
# cleartext, so every branch runner would need read access to the one file that
# must not leak. Ten named parameters say exactly what was meant to be said -- and
# `aws ssm get-parameter` answers from a shell script, which the teardown path
# needs and `terraform_remote_state` cannot give it.

locals {
  name = "${var.project}-preview"

  #: The maintenance function's connection. Against the cluster, never a proxy,
  #: and against the cluster's own database rather than any branch's -- `CREATE
  #: DATABASE` and `DROP DATABASE` cannot be issued from inside the database they
  #: name.
  maintenance_database_url = join("", [
    "postgresql+psycopg://",
    module.database.master_username,
    ":",
    urlencode(module.database.master_password),
    "@",
    module.database.cluster_endpoint,
    ":",
    module.database.port,
    "/",
    module.database.database_name,
  ])
}

module "network" {
  source = "../../modules/network"

  name       = local.name
  cidr_block = var.vpc_cidr
}

module "database" {
  source = "../../modules/database"

  name              = local.name
  subnet_ids        = module.network.private_subnet_ids
  security_group_id = module.network.database_security_group_id

  min_capacity = 0
  max_capacity = 2
  #: Fifteen minutes rather than the hour a long-lived environment takes. A
  #: preview is used in bursts of minutes and the resume already fits inside the
  #: function's timeout, so the shorter pause is strictly cheaper.
  seconds_until_auto_pause = 900
  #: No proxy. It is billed by the hour whether or not anything connects, which is
  #: the wrong shape entirely for something that exists to be cheap -- and
  #: `modules/database/main.tf` records what a proxy would additionally require.
  enable_proxy          = false
  backup_retention_days = 1
  skip_final_snapshot   = true
  #: **Zero, and this is the knob that matters most here.** The master secret is
  #: named after this layer, so a non-zero window is that name still taken:
  #: destroying and re-creating the preview cluster inside the window fails on the
  #: secret rather than on anything the operator changed. This is the layer most
  #: likely to be rebuilt, which is why it is the one that must not squat on its
  #: own name.
  secret_recovery_days = 0
}

# --------------------------------------------------------------------------- #
# Maintenance
# --------------------------------------------------------------------------- #

# One function, outliving every preview, whose only job is to drop a branch's
# database when the branch is gone.
#
# It lives HERE rather than in the branch stack, and the reason is an ordering
# hazard rather than tidiness: at teardown the branch's own functions are being
# deleted by the same `terraform destroy` that would have to call one of them.
# A function that outlives the preview has no such ordering, and it doubles as the
# way to reclaim a database whose stack was destroyed by hand.

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

resource "aws_iam_role" "maintenance" {
  name               = "${local.name}-maintenance"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# The ENI the function needs to reach the cluster, and nothing else. It holds the
# master password in an environment variable, so it is given no permission to
# read a secret, write a log group it does not own, or touch any other service.
resource "aws_iam_role_policy_attachment" "maintenance_vpc" {
  role       = aws_iam_role.maintenance.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_cloudwatch_log_group" "maintenance" {
  name              = "/aws/lambda/${local.name}-maintenance"
  retention_in_days = 14
}

resource "aws_lambda_function" "maintenance" {
  function_name = "${local.name}-maintenance"
  role          = aws_iam_role.maintenance.arn
  handler       = "app.lambda_handler.preview_maintenance"
  runtime       = "python3.14"
  architectures = ["arm64"]

  filename         = var.package_path
  source_code_hash = filebase64sha256(var.package_path)

  # Long, because a first call after a quiet week waits for the cluster to resume
  # before it can drop anything.
  timeout     = 300
  memory_size = 512

  vpc_config {
    subnet_ids         = module.network.private_subnet_ids
    security_group_ids = [module.network.lambda_security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL = local.maintenance_database_url
      APP_ENV      = "preview"
      APP_VERSION  = var.app_version
    }
  }

  depends_on = [aws_cloudwatch_log_group.maintenance]
}

# --------------------------------------------------------------------------- #
# The contract a branch stack reads
# --------------------------------------------------------------------------- #

# Ten parameters, and the list is the promise. A branch root reads these and
# declares no network and no cluster of its own --
# `tests/fitness/test_infra_layout.py` holds it to that.
#
# No password is published here. The master secret's ARN is, and a branch resolves
# the value itself through Secrets Manager, so the secret has exactly one home.

resource "aws_ssm_parameter" "vpc_id" {
  name  = "/${var.project}/preview/vpc_id"
  type  = "String"
  value = module.network.vpc_id
}

resource "aws_ssm_parameter" "private_subnet_ids" {
  name  = "/${var.project}/preview/private_subnet_ids"
  type  = "StringList"
  value = join(",", module.network.private_subnet_ids)
}

resource "aws_ssm_parameter" "lambda_security_group_id" {
  name  = "/${var.project}/preview/lambda_security_group_id"
  type  = "String"
  value = module.network.lambda_security_group_id
}

resource "aws_ssm_parameter" "database_endpoint" {
  name  = "/${var.project}/preview/database/endpoint"
  type  = "String"
  value = module.database.cluster_endpoint
}

resource "aws_ssm_parameter" "database_port" {
  name  = "/${var.project}/preview/database/port"
  type  = "String"
  value = tostring(module.database.port)
}

# The database a branch's migration connects to in order to CREATE its own, and
# the maintenance function connects to in order to DROP it. Never a branch's.
resource "aws_ssm_parameter" "maintenance_database" {
  name  = "/${var.project}/preview/database/maintenance_database"
  type  = "String"
  value = module.database.database_name
}

resource "aws_ssm_parameter" "master_username" {
  name  = "/${var.project}/preview/database/master_username"
  type  = "String"
  value = module.database.master_username
}

resource "aws_ssm_parameter" "master_secret_arn" {
  name  = "/${var.project}/preview/database/master_secret_arn"
  type  = "String"
  value = module.database.master_secret_arn
}

resource "aws_ssm_parameter" "iam_auth_resource_arn" {
  name  = "/${var.project}/preview/database/iam_auth_resource_arn"
  type  = "String"
  value = module.database.iam_auth_resource_arn
}

resource "aws_ssm_parameter" "maintenance_function_name" {
  name  = "/${var.project}/preview/maintenance_function_name"
  type  = "String"
  value = aws_lambda_function.maintenance.function_name
}
