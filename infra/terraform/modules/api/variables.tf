variable "name" {
  type = string
}

variable "environment" {
  description = "stage or prod. Reaches the application as APP_ENV, and /api/health reports it."
  type        = string
}

variable "app_version" {
  description = <<-TEXT
    The release this deployment carries, as `/api/health` will report it. Supplied
    by scripts/infra.sh so a plan and the apply that follows it agree, and so a
    preview can say `<version>+<sha>` where a semver alone would name the wrong
    thing. No default, for the same reason `package_path` has none: a value this
    one guesses is a wrong answer on a screen somebody trusts.
  TEXT
  type        = string
}

variable "package_path" {
  description = "The zip scripts/package.sh built. Its hash is what decides a redeploy."
  type        = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "database_endpoint" {
  type = string
}

variable "database_cluster_endpoint" {
  description = <<-TEXT
    The cluster itself, never the proxy. Only the migration function uses it: it
    authenticates with the master password, and a proxy entry is matched by the
    username in its secret -- so a password against an `iam_auth = "REQUIRED"`
    entry is refused, which is what used to make stage unable to migrate at all.
  TEXT
  type        = string
}

variable "database_port" {
  type = number
}

variable "database_name" {
  type = string
}

variable "master_username" {
  type = string
}

variable "master_password" {
  type      = string
  sensitive = true
}

variable "database_iam_auth_resource_arn" {
  description = "From the database module. The user is appended to it here."
  type        = string
}

variable "timeout_seconds" {
  description = "Must exceed the database's resume time, or a cold morning is an error page."
  type        = number
  default     = 30
}

variable "reserved_concurrency" {
  description = <<-TEXT
    How many copies of the API function may run at once, and therefore how many
    connections it can open. `null` leaves it on the account's shared pool, which
    is right where nothing else shares the cluster. Set it where a connection
    ceiling matters, keeping it well under the cluster's max_connections at its
    floor capacity -- and remember AWS refuses to leave an account fewer than 100
    unreserved executions in total.
  TEXT
  type        = number
  default     = null
}

variable "memory_mb" {
  description = "Also buys CPU share, which is what a cold start actually waits on."
  type        = number
  default     = 512
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "tags" {
  type    = map(string)
  default = {}
}
