output "url" {
  description = "Where this preview answers. The Function URL, with no CDN in front of it."
  value       = module.app.url
}

output "database" {
  description = "This branch's database on the shared cluster. What the teardown drops."
  value       = module.app.database_name
}

output "migrate_function_name" {
  description = "Invoked by scripts/preview.sh after the apply: it creates the database, then migrates."
  value       = module.app.migrate_function_name
}
