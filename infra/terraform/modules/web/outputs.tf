output "bucket" {
  description = "Where scripts/deploy.sh syncs the built SPA."
  value       = aws_s3_bucket.site.bucket
}

output "distribution_id" {
  description = "What an invalidation is issued against after a deploy."
  value       = aws_cloudfront_distribution.this.id
}

output "domain_name" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "url" {
  description = "Where the application answers. The one address a person needs."
  value       = length(var.aliases) > 0 ? "https://${var.aliases[0]}" : "https://${aws_cloudfront_distribution.this.domain_name}"
}
