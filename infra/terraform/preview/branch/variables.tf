variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "project" {
  description = "Must match the shared layer's, since it locates that layer's parameters."
  type        = string
  default     = "sdd-guestbook"
}

variable "slug" {
  description = <<-TEXT
    This branch, reduced to something that is legal as an AWS resource name, as a
    Terraform state key and (with hyphens turned to underscores) as a PostgreSQL
    identifier. Produced by `scripts/preview.sh slug`, which ends it with six hex
    characters of the full ref's hash -- so two branches whose readable parts
    collide still get separate stacks.

    Validated here as well as there, because a slug that reached a resource name
    or a `CREATE DATABASE` unchecked would be the one place in this project where
    a branch name becomes a statement.
  TEXT
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,25}[a-z0-9])?$", var.slug))
    error_message = "A slug is 1-27 lowercase letters, digits and hyphens, starting and ending with one of the first two. scripts/preview.sh produces one; do not write one by hand."
  }
}

variable "package_path" {
  description = "The PREVIEW zip, which carries the SPA. scripts/package.sh --preview builds it."
  type        = string
}

variable "app_version" {
  description = "Reported at /api/health. `<version>+<sha>` for a preview."
  type        = string
}

variable "branch" {
  description = <<-TEXT
    The branch this preview was built from, in full. Carried as a tag rather than
    as a name, because a name has to be short and legal and a tag has to be true.
  TEXT
  type        = string
  default     = ""
}
