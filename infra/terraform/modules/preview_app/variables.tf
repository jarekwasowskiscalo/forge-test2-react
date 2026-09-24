variable "name" {
  description = "Prefix for every resource here. Carries the project and the branch slug."
  type        = string
}

variable "package_path" {
  description = <<-TEXT
    The PREVIEW zip -- the one that carries `app/static`. A preview serves the SPA
    from the function itself, so this is the one artefact in the project where the
    two halves travel together. `scripts/package.sh --preview` builds it.
  TEXT
  type        = string
}

variable "app_version" {
  description = "Reported at /api/health. For a preview, `<version>+<sha>`: the commit is the useful answer."
  type        = string
}

variable "subnet_ids" {
  description = "The shared preview layer's private subnets. Not created here."
  type        = list(string)
}

variable "security_group_id" {
  description = "The shared preview layer's Lambda security group. Not created here."
  type        = string
}

variable "database_endpoint" {
  description = "The shared preview cluster. Every branch's database lives on it."
  type        = string
}

variable "database_port" {
  type = number
}

variable "database_name" {
  description = <<-TEXT
    This branch's own database on the shared cluster, `preview_<slug>`. It does not
    exist when this module is applied: the migration function creates it on first
    invocation, because Terraform runs on a GitHub runner and the cluster has no
    address reachable from outside the VPC.
  TEXT
  type        = string
}

variable "maintenance_database" {
  description = <<-TEXT
    The cluster's own database, which the migration function connects to in order
    to CREATE the one above -- `CREATE DATABASE` cannot be issued from inside the
    database it names.
  TEXT
  type        = string
}

variable "master_username" {
  type = string
}

variable "master_password" {
  type      = string
  sensitive = true
}

variable "database_iam_auth_resource_arn" {
  description = "From the shared layer. The API function's user is appended to it here."
  type        = string
}

variable "log_retention_days" {
  description = "Three days. A preview outlives its own logs' usefulness by about that much."
  type        = number
  default     = 3
}

variable "timeout_seconds" {
  description = <<-TEXT
    Must exceed the shared cluster's resume time. A Function URL imposes no ceiling
    of its own, unlike API Gateway's hard 29 seconds -- which is one of the reasons
    a preview uses one.
  TEXT
  type        = number
  default     = 30
}

variable "memory_mb" {
  type    = number
  default = 512
}

variable "tags" {
  type    = map(string)
  default = {}
}
