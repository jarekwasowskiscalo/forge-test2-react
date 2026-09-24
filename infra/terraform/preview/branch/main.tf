# One branch's preview. Applied once per branch, against one state key per branch.
#
# This root **discovers** the shared layer rather than declaring anything: every
# `data` block below reads a parameter that `infra/terraform/preview/shared/`
# published. Nothing here creates a network, a cluster, a bucket or a
# distribution, and `tests/fitness/test_infra_layout.py` asserts that it never
# starts to -- an accidental `module "stack"` here would read as reasonable in
# review and cost a VPC per branch, which the account's quota stops at the second.

locals {
  name = "${var.project}-preview-${var.slug}"

  # A PostgreSQL identifier, from the same slug. Hyphens become underscores; the
  # `preview_` prefix is what `app/lambda_handler.py` refuses to act without, so
  # no branch can name the cluster's own database.
  database_name = "preview_${replace(var.slug, "-", "_")}"

  parameters = "/${var.project}/preview"
}

data "aws_ssm_parameter" "private_subnet_ids" {
  name = "${local.parameters}/private_subnet_ids"
}

data "aws_ssm_parameter" "lambda_security_group_id" {
  name = "${local.parameters}/lambda_security_group_id"
}

data "aws_ssm_parameter" "database_endpoint" {
  name = "${local.parameters}/database/endpoint"
}

data "aws_ssm_parameter" "database_port" {
  name = "${local.parameters}/database/port"
}

data "aws_ssm_parameter" "maintenance_database" {
  name = "${local.parameters}/database/maintenance_database"
}

data "aws_ssm_parameter" "master_username" {
  name = "${local.parameters}/database/master_username"
}

data "aws_ssm_parameter" "master_secret_arn" {
  name = "${local.parameters}/database/master_secret_arn"
}

data "aws_ssm_parameter" "iam_auth_resource_arn" {
  name = "${local.parameters}/database/iam_auth_resource_arn"
}

# The password itself, resolved here rather than published as a parameter. The
# secret has one home -- Secrets Manager -- and the shared layer publishes only
# where that home is.
data "aws_secretsmanager_secret_version" "master" {
  secret_id = data.aws_ssm_parameter.master_secret_arn.value
}

module "app" {
  source = "../../modules/preview_app"

  name         = local.name
  package_path = var.package_path
  app_version  = var.app_version

  subnet_ids        = split(",", data.aws_ssm_parameter.private_subnet_ids.value)
  security_group_id = data.aws_ssm_parameter.lambda_security_group_id.value

  database_endpoint    = data.aws_ssm_parameter.database_endpoint.value
  database_port        = tonumber(data.aws_ssm_parameter.database_port.value)
  database_name        = local.database_name
  maintenance_database = data.aws_ssm_parameter.maintenance_database.value

  master_username                = data.aws_ssm_parameter.master_username.value
  master_password                = jsondecode(data.aws_secretsmanager_secret_version.master.secret_string)["password"]
  database_iam_auth_resource_arn = data.aws_ssm_parameter.iam_auth_resource_arn.value

  tags = {
    Branch = var.branch
    Slug   = var.slug
  }
}
