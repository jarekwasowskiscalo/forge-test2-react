output "vpc_id" {
  value = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "Both of them. Aurora needs two AZs; the functions use the same pair."
  value       = aws_subnet.private[*].id
}

output "lambda_security_group_id" {
  value = aws_security_group.lambda.id
}

output "database_security_group_id" {
  value = aws_security_group.database.id
}
