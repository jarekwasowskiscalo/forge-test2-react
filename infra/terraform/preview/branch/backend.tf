# Remote state, and NO KEY -- which is the one thing to understand about this root.
#
# It is applied once per branch, so it has one state per branch rather than one
# state. The key is supplied at init:
#
#     terraform init -reconfigure \
#       -backend-config="key=sdd-guestbook/preview/<slug>/terraform.tfstate"
#
# `scripts/preview.sh` is what does that; nobody should be typing it.
#
# **A literal key here would not fail.** Every preview would quietly share one
# state file, and the second branch to deploy would read the first one's state,
# conclude its resources already exist under other names, and take the stack over.
# `tests/fitness/test_infra_layout.py` asserts this absence for that reason.
#
# The upside of a key rather than a Terraform workspace: a stale preview is then
# an ordinary S3 object under `sdd-guestbook/preview/`, which can be listed,
# expired by a bucket lifecycle rule, or deleted without Terraform. A workspace
# refuses to be deleted while its state is non-empty, so a half-failed destroy
# leaves something the next run has to reason about.
terraform {
  backend "s3" {
    bucket       = "test-jw-app-sdd-cc-1"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
