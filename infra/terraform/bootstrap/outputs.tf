output "state_bucket" {
  description = <<-TEXT
    Copy this into the `bucket` line of EVERY backend.tf: envs/stage, envs/prod,
    preview/shared and preview/branch. A backend block takes no variables, so this
    is the one value that has to travel by hand.
  TEXT
  value       = aws_s3_bucket.state.bucket
}

output "deploy_role_arn" {
  description = "Set this as the AWS_DEPLOY_ROLE_ARN repository variable in GitHub."
  value       = aws_iam_role.deploy.arn
}

output "preview_role_arn" {
  description = <<-TEXT
    Set this as AWS_DEPLOY_ROLE_ARN on the `preview` GitHub Environment, which
    overrides the repository-level variable of the same name. One name and one
    expression in every workflow; GitHub resolves which role from the job's
    `environment:`.
  TEXT
  value       = aws_iam_role.preview.arn
}

output "plan_role_arn" {
  description = "The read-only role people assume. Empty when plan_role_principals named nobody."
  value       = try(aws_iam_role.plan[0].arn, "")
}
