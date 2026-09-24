output "url" {
  description = "Where this environment answers."
  value       = module.stack.url
}

output "web_bucket" {
  value = module.stack.web_bucket
}

output "distribution_id" {
  value = module.stack.distribution_id
}

output "api_function_name" {
  value = module.stack.api_function_name
}

output "migrate_function_name" {
  value = module.stack.migrate_function_name
}

output "api_alias_name" {
  value = module.stack.api_alias_name
}

output "api_published_version" {
  value = module.stack.api_published_version
}

output "database_master_secret_arn" {
  value = module.stack.database_master_secret_arn
}

output "release_manifest_parameter" {
  value = module.stack.release_manifest_parameter
}
