variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "project" {
  description = "Prefixes every name here and in every branch stack that borrows this layer."
  type        = string
  default     = "sdd-guestbook"
}

variable "vpc_cidr" {
  description = <<-TEXT
    One network for every preview there will ever be. It took the range `dev` used
    to hold, which is how the account stays inside its five-VPC quota: a VPC per
    branch reaches the limit at the second concurrent preview, and the limit is
    per region rather than per project.
  TEXT
  type        = string
  default     = "10.45.0.0/16"
}

variable "package_path" {
  description = <<-TEXT
    The Lambda zip, for the maintenance function. The production zip, not the
    preview one: this function serves no HTTP and has no use for the SPA.
  TEXT
  type        = string
}

variable "app_version" {
  description = "The release this layer was last applied from. Reported in the maintenance function's logs."
  type        = string
}
