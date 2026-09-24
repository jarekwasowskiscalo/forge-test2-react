# One environment, whole. The composite the three environment directories call.
#
# It exists so `envs/stage` and `envs/prod` are each about twenty
# lines of DIFFERENCES rather than three copies of the same wiring. A copy is
# what drifts: the environment that stops matching is always the one nobody
# deploys often enough to notice.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

locals {
  name = "${var.project}-${var.environment}"

  tags = merge(var.tags, {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

module "network" {
  source = "../../modules/network"

  name       = local.name
  cidr_block = var.vpc_cidr
  tags       = local.tags
}

module "database" {
  source = "../../modules/database"

  name              = local.name
  subnet_ids        = module.network.private_subnet_ids
  security_group_id = module.network.database_security_group_id

  min_capacity             = var.database_min_capacity
  max_capacity             = var.database_max_capacity
  seconds_until_auto_pause = var.database_seconds_until_auto_pause
  enable_proxy             = var.database_enable_proxy
  backup_retention_days    = var.database_backup_retention_days
  skip_final_snapshot      = var.disposable
  secret_recovery_days     = var.database_secret_recovery_days

  tags = local.tags
}

module "api" {
  source = "../../modules/api"

  name        = local.name
  environment = var.environment
  app_version = var.app_version

  package_path      = var.package_path
  subnet_ids        = module.network.private_subnet_ids
  security_group_id = module.network.lambda_security_group_id

  database_endpoint              = module.database.endpoint
  database_cluster_endpoint      = module.database.cluster_endpoint
  database_port                  = module.database.port
  database_name                  = module.database.database_name
  master_username                = module.database.master_username
  master_password                = module.database.master_password
  database_iam_auth_resource_arn = module.database.iam_auth_resource_arn

  timeout_seconds      = var.api_timeout_seconds
  memory_mb            = var.api_memory_mb
  reserved_concurrency = var.api_reserved_concurrency
  log_retention_days   = var.log_retention_days

  tags = local.tags
}

module "web" {
  source = "../../modules/web"

  name                = local.name
  api_endpoint        = module.api.endpoint
  aliases             = var.domain_aliases
  acm_certificate_arn = var.acm_certificate_arn
  force_destroy       = var.disposable

  tags = local.tags
}

# The register of what actually served this environment.
#
# **Terraform owns that it exists; the deploy owns what is in it** -- the same split,
# for the same reason, as the API alias's `ignore_changes = [function_version]`: a
# value that changes on every release cannot be state Terraform reconciles, and a
# resource that only ever appears when a script happens to write it is not declared
# anywhere anybody reads.
#
# `scripts/deploy.sh` appends an entry after a smoke passes, and `--rollback` reads it
# to answer "which version last SERVED", which nothing on the account could answer
# before: `publish = true` mints a version on every apply, so the numbers above the
# alias are indistinguishable from releases and most of them never served anything.
#
# SSM rather than the site bucket: every key in that bucket is reachable through
# CloudFront, and this document names commits. Standard tier, so 4 KB --
# `scripts/release_manifest.py` trims to fit rather than being refused by the API.
resource "aws_ssm_parameter" "releases" {
  name  = "/${var.project}/${var.environment}/releases"
  type  = "String"
  value = "[]"
  tags  = local.tags

  lifecycle {
    ignore_changes = [value]
  }
}
