output "endpoint" {
  description = <<-TEXT
    What the functions connect to: the proxy where there is one, the cluster's
    writer endpoint otherwise. One output rather than two, so nothing downstream
    has to know which arrangement this environment chose.
  TEXT
  value       = var.enable_proxy ? aws_db_proxy.this[0].endpoint : aws_rds_cluster.this.endpoint
}

output "cluster_endpoint" {
  description = <<-TEXT
    The cluster's own writer endpoint, whatever this environment chose. For the
    client that must NOT go through the proxy: the migration function, which
    authenticates with the master password. A proxy entry is matched by the
    username inside one of its secrets and the migration's client is the one that
    performs DDL, which a proxy pins a session for anyway.
  TEXT
  value       = aws_rds_cluster.this.endpoint
}

output "port" {
  value = var.port
}

output "database_name" {
  value = aws_rds_cluster.this.database_name
}

output "master_username" {
  value = var.master_username
}

output "master_secret_arn" {
  value = aws_secretsmanager_secret.master.arn
}

output "master_password" {
  description = "Passed to the migration function, which needs DDL rights. Never to the API."
  value       = random_password.master.result
  sensitive   = true
}

output "iam_auth_resource_arn" {
  description = <<-TEXT
    What an `rds-db:connect` policy is written against, with the database user
    left as a wildcard for the caller to fill in.

    The identifier differs by arrangement and getting it wrong produces a policy
    that grants nothing while looking correct: with a proxy it is the PROXY's
    resource id, without one it is the CLUSTER's.
  TEXT
  value = var.enable_proxy ? (
    "arn:aws:rds-db:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:dbuser:${split("/", aws_db_proxy.this[0].arn)[1]}"
    ) : (
    "arn:aws:rds-db:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.this.cluster_resource_id}"
  )
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
