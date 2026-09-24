# Remote state, one key per environment.
#
# The bucket is created once per account by `infra/terraform/bootstrap/`, which
# keeps its own state locally -- the usual chicken and egg, solved the usual way
# and written down so nobody has to rediscover it.
#
# **There is no lock table.** Locking is `use_lockfile = true` below -- S3
# conditional writes -- and the DynamoDB table this comment used to name was
# removed with the reasoning at `infra/terraform/bootstrap/main.tf`. A runbook
# written from this sentence sent its reader looking for a table nobody creates.
#
# **Values here are placeholders.** A state backend cannot take variables, so the
# bucket name is literal and you fill it in once from the bootstrap output.
terraform {
  backend "s3" {
    bucket       = "test-jw-app-sdd-cc-1"
    key          = "sdd-guestbook/stage/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
