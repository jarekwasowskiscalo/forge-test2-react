# stage. Production's shape at production's prices minus the floor -- so what production stands on is exercised somewhere before production.
#
# Everything shared lives in ../../modules/stack; what is here is only what makes
# this environment different from the other two.

module "stack" {
  source = "../../modules/stack"

  environment  = "stage"
  package_path = var.package_path
  app_version  = var.app_version
  vpc_cidr     = "10.43.0.0/16"
  disposable   = false

  database_min_capacity          = 0
  database_max_capacity          = 4
  database_enable_proxy          = false
  database_backup_retention_days = 7

  api_reserved_concurrency = 20

  log_retention_days = 14
}
