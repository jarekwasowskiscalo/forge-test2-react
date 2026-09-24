# What a person needs after applying this. The machine-readable contract is the
# SSM parameters in main.tf, which is what a branch stack actually reads -- these
# are for the operator standing in front of the first apply.

output "vpc_id" {
  value = module.network.vpc_id
}

output "database_endpoint" {
  description = "The cluster every preview database lives on. Private: reachable from inside the VPC only."
  value       = module.database.cluster_endpoint
}

output "maintenance_function_name" {
  description = "What scripts/preview.sh invokes to drop a branch's database."
  value       = aws_lambda_function.maintenance.function_name
}

output "database_master_secret_arn" {
  description = "For a person who needs to reach the cluster. Not read by the runtime."
  value       = module.database.master_secret_arn
}
