output "url" {
  description = "Where this environment answers."
  value       = module.web.url
}

output "web_bucket" {
  value = module.web.bucket
}

output "distribution_id" {
  value = module.web.distribution_id
}

output "api_function_name" {
  value = module.api.api_function_name
}

output "migrate_function_name" {
  value = module.api.migrate_function_name
}

output "api_alias_name" {
  value = module.api.api_alias_name
}

output "api_published_version" {
  description = "Published by the apply, routed to only after the migration."
  value       = module.api.api_published_version
}

output "database_master_secret_arn" {
  description = "For a person who needs to reach the database. Not read by the runtime."
  value       = module.database.master_secret_arn
}

output "release_manifest_parameter" {
  description = "Where the record of what served lives. Written by a deploy, read by a rollback."
  value       = aws_ssm_parameter.releases.name
}
