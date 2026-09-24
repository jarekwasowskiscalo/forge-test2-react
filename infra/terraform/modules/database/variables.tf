variable "name" {
  description = "Prefix for every resource this module creates. Carries the environment."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets, at least two AZs. Aurora refuses fewer."
  type        = list(string)
}

variable "security_group_id" {
  description = "The database security group from the network module."
  type        = string
}

variable "engine_version" {
  description = "Aurora PostgreSQL version. Pinned, so an apply never moves it by surprise."
  type        = string
  default     = "16.6"
}

variable "database_name" {
  type    = string
  default = "app"
}

variable "master_username" {
  description = "Owns the schema. Used by the migration function and by nobody else."
  type        = string
  default     = "app_master"
}

variable "port" {
  type    = number
  default = 5432
}

variable "min_capacity" {
  description = <<-TEXT
    Aurora capacity units the cluster never drops below. 0 means it pauses and
    costs storage alone, at the price of a resume of roughly 10-15 seconds on the
    first request after a quiet period. Production sets 0.5 to buy that away.
  TEXT
  type        = number
  default     = 0
}

variable "max_capacity" {
  description = "The ceiling. Also the ceiling on what a runaway query can cost."
  type        = number
  default     = 2
}

variable "seconds_until_auto_pause" {
  description = "How long idle before scaling to zero. Only used when min_capacity is 0."
  type        = number
  default     = 3600
}

variable "enable_proxy" {
  description = <<-TEXT
    Put RDS Proxy in front of the cluster. **Not implemented: the only accepted
    value is `false`**, and the validation below says why.

    It reads like a cost decision and is not one yet. The proxy resources exist
    (they are all under `count = var.enable_proxy ? 1 : 0`) and two things they
    need do not, so `true` produces a stack whose API function cannot connect at
    all -- see the header of `main.tf` for both, and for the shape that would
    work. Until that shape is built, a parameter that validated and then failed
    on a real account would be worse than no parameter.
  TEXT
  type        = bool
  default     = false

  #: Refused here rather than by a `precondition` on `aws_db_proxy`, and the
  #: difference is which gate catches it: a variable validation is evaluated
  #: before any provider is initialised, so `terraform validate` raises it --
  #: which is the ONLY Terraform that CI runs (`scripts/infra-check.sh`, and
  #: `.github/workflows/ci.yml` deliberately does no `plan`). A precondition
  #: would wait for an apply, on an account, with nobody watching the gate.
  #:
  #: `infra/terraform/refusals/database-proxy/` is the root that proves this
  #: fires, and the same script asserts it.
  validation {
    condition     = var.enable_proxy == false
    error_message = "enable_proxy is not implemented. The proxy's single auth block names the master secret while the API function connects as app_iam by an IAM token, and the database security group has no self-referencing INGRESS rule, so the proxy could reach no target. Both are named in the header of modules/database/main.tf, with the arrangement that would work."
  }
}

variable "backup_retention_days" {
  type    = number
  default = 1
}

variable "skip_final_snapshot" {
  description = "True for an environment that is meant to be thrown away and rebuilt."
  type        = bool
  default     = true
}

variable "secret_recovery_days" {
  description = "Window in which a deleted secret can be recovered. 0 deletes immediately."
  type        = number
  default     = 7
}

variable "tags" {
  type    = map(string)
  default = {}
}
