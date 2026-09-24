# Remote state, one key -- this root is applied once per account.
#
# The bucket is created by `infra/terraform/bootstrap/` and its name is copied in
# here by hand, as it is into every other backend block: a backend takes no
# variables. `infra/terraform/preview/branch/` is the one root whose key is NOT
# here, because it has one state per branch rather than one state.
terraform {
  backend "s3" {
    bucket       = "test-jw-app-sdd-cc-1"
    key          = "sdd-guestbook/preview/shared/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
