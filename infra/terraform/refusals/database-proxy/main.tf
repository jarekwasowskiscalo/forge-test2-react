# A root that exists to be REFUSED, and the only kind in this tree that does.
#
# `modules/database` offers `enable_proxy` and rejects every value but `false`,
# because the proxy is not implemented: the single `auth` block names the master
# secret while the API function connects as `app_iam` by an IAM token, and the
# database security group has no self-referencing ingress rule. Both are written
# out in the header of `modules/database/main.tf`.
#
# A barrier nothing exercises is a barrier that gets deleted by whoever finds it
# inconvenient. So this root sets the value the module must refuse, and
# `scripts/infra-check.sh` runs `terraform validate` here and fails if it PASSES.
# The other half -- that `false` stays legal -- is proven by the five real roots
# the same script validates first.
#
# Three things are true of this directory and of nothing else under
# infra/terraform/:
#
#   - it is NOT in `ROOTS` in scripts/infra-check.sh. `validate` succeeding is the
#     bug here, so it cannot share a loop with roots where `validate` failing is;
#   - it is NOT reachable from scripts/infra.sh. Article XII says the script is the
#     interface, and this is not something anybody plans or applies -- it has no
#     `backend.tf` and no state, and an `apply` of it could not get past `validate`
#     anyway;
#   - it has no variables and no outputs. Every value below is a literal, because a
#     fixture that could be configured is a fixture that can be configured wrong.
#
# tests/fitness/test_infra_layout.py holds all three as assertions, so none of them
# is merely a claim in this comment.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

module "database" {
  source = "../../modules/database"

  #: Syntactically valid and deliberately fictional. `validate` reaches the
  #: variable validation without contacting AWS, so nothing here is ever looked up.
  name              = "refusal-check"
  subnet_ids        = ["subnet-0000000000000000a", "subnet-0000000000000000b"]
  security_group_id = "sg-0000000000000000a"

  #: The whole point of the file.
  enable_proxy = true
}
