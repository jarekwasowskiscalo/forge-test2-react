variable "project" {
  description = "Prefixes every name. One value for every environment and every preview."
  type        = string
  default     = "sdd-guestbook"
}

variable "environment" {
  description = <<-TEXT
    stage or prod. The second half of every resource name.

    A per-branch preview does NOT come through this module -- it calls
    `modules/preview_app`, which creates no network, cluster, bucket or
    distribution. That is why this list is short and stays short.
  TEXT
  type        = string

  validation {
    condition     = contains(["stage", "prod"], var.environment)
    error_message = "The long-lived environments are stage and prod. A third one needs a directory under envs/ first; a disposable one is a preview (infra/terraform/preview/)."
  }
}

variable "app_version" {
  description = "The release this deployment carries. Reaches the app as APP_VERSION."
  type        = string
}

variable "package_path" {
  description = "The Lambda zip, from scripts/package.sh."
  type        = string
}

variable "vpc_cidr" {
  description = "Different per environment, so two of them could be peered later without renumbering."
  type        = string
}

variable "disposable" {
  description = <<-TEXT
    Whether this environment is meant to be destroyed and rebuilt. It decides two
    things that both go one way on a throwaway environment and the other way on
    one holding anything real: whether `terraform destroy` may empty the web
    bucket, and whether the database takes a final snapshot and refuses deletion.
  TEXT
  type        = bool
}

variable "database_min_capacity" {
  description = "0 pauses the cluster between requests; production sets a floor to avoid the resume."
  type        = number
  default     = 0
}

variable "database_max_capacity" {
  type    = number
  default = 2
}

variable "database_seconds_until_auto_pause" {
  type    = number
  default = 3600
}

variable "database_enable_proxy" {
  description = <<-TEXT
    Passed straight to `modules/database`, which **refuses anything but `false`**:
    the proxy is not implemented, and that module's `enable_proxy` carries the
    validation and the reason. Named here so an environment can see the switch
    exists and read why it is shut, rather than discover both at `validate` time.
  TEXT
  type        = bool
  default     = false
}

variable "database_backup_retention_days" {
  type    = number
  default = 1
}

variable "database_secret_recovery_days" {
  description = <<-TEXT
    Days a deleted master secret stays recoverable. It was not reachable from an
    environment at all until now, which mattered because the secret's name carries
    the environment: a non-zero window is a name still taken, so destroying an
    environment and rebuilding it inside that window fails on the secret rather
    than on anything the operator changed. 7 for anything holding real data, 0 for
    anything meant to be rebuilt.
  TEXT
  type        = number
  default     = 7
}

variable "api_timeout_seconds" {
  type    = number
  default = 30
}

variable "api_reserved_concurrency" {
  description = "The connection ceiling that replaces an RDS Proxy. null is unreserved."
  type        = number
  default     = null
}

variable "api_memory_mb" {
  type    = number
  default = 512
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "domain_aliases" {
  description = "Custom domains for the distribution. Empty uses the CloudFront name."
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "Must be in us-east-1, whatever region this stack is in."
  type        = string
  default     = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
