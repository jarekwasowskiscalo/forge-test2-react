variable "name" {
  type = string
}

variable "api_endpoint" {
  description = "The HTTP API's domain name, without a scheme."
  type        = string
}

variable "aliases" {
  description = "Custom domains. Empty means the distribution's own *.cloudfront.net name."
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = <<-TEXT
    Certificate for `aliases`, and it MUST live in us-east-1 whatever region the
    rest of this stack is in -- CloudFront reads certificates from there and
    nowhere else. Null means the default CloudFront certificate.
  TEXT
  type        = string
  default     = null
}

variable "price_class" {
  description = "PriceClass_100 is Europe and North America, and is the cheapest."
  type        = string
  default     = "PriceClass_100"
}

variable "force_destroy" {
  description = "Let `terraform destroy` empty the bucket. True only where teardown is expected."
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
