output "url" {
  description = "The Function URL, with its trailing slash. Where a reviewer clicks."
  value       = aws_lambda_function_url.api.function_url
}

output "api_function_name" {
  value = aws_lambda_function.api.function_name
}

output "migrate_function_name" {
  description = "Invoked once after the apply: it creates this branch's database, then migrates it."
  value       = aws_lambda_function.migrate.function_name
}

output "database_name" {
  description = "This branch's database on the shared cluster."
  value       = var.database_name
}
