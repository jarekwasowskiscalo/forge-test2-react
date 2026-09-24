# prod. The only environment with a capacity floor -- 0.5 ACU buys away the ten-second resume that a first visitor would otherwise meet.
#
# Everything shared lives in ../../modules/stack; what is here is only what makes
# this environment different from the other two.

module "stack" {
  source = "../../modules/stack"

  environment  = "prod"
  package_path = var.package_path
  app_version  = var.app_version
  vpc_cidr     = "10.44.0.0/16"
  disposable   = false

  database_min_capacity          = 0.5
  database_max_capacity          = 8
  database_enable_proxy          = false
  database_backup_retention_days = 14

  api_reserved_concurrency = 40

  log_retention_days = 30
}
