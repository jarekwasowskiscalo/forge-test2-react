output "endpoint" {
  description = "Host only, without the scheme: CloudFront wants a domain name."
  value       = replace(aws_apigatewayv2_api.this.api_endpoint, "https://", "")
}

output "api_function_name" {
  value = aws_lambda_function.api.function_name
}

output "migrate_function_name" {
  description = "Invoked by scripts/deploy.sh before the code rolls."
  value       = aws_lambda_function.migrate.function_name
}

output "api_alias_name" {
  description = "The alias the gateway routes to. scripts/deploy.sh moves it after the migration."
  value       = aws_lambda_alias.api.name
}

output "api_published_version" {
  description = <<-TEXT
    The version this apply published. Nothing routes to it until `deploy.sh` moves
    the alias, which it does only once the migration has succeeded -- so between an
    apply and that moment the previous version is still serving, over the schema it
    was built for.
  TEXT
  value       = aws_lambda_function.api.version
}
