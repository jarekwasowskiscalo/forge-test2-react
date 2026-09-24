variable "name" {
  description = "Prefix for every resource this module creates. Carries the environment."
  type        = string
}

variable "cidr_block" {
  description = "The VPC's address range. Private, and never peered by this stack."
  type        = string
  default     = "10.42.0.0/16"
}

variable "database_port" {
  description = "The one port that may cross these security groups."
  type        = number
  default     = 5432
}

variable "tags" {
  description = "Applied to everything, so a bill can be read by environment."
  type        = map(string)
  default     = {}
}
