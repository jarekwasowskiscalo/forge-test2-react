variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "app_version" {
  description = <<-TEXT
    The release this deployment carries, reported by /api/health. Passed in by
    scripts/infra.sh, so a plan and its apply cannot disagree about which version
    they are talking about. It is APP_VERSION when the caller sets one -- a release
    passes its tag through deploy.yml -- and otherwise the version in
    pyproject.toml, which names the package rather than any release.
  TEXT
  type        = string
}

variable "package_path" {
  description = <<-TEXT
    The Lambda zip. Passed in by scripts/deploy.sh rather than defaulted, so an
    apply cannot quietly deploy whatever happens to be left in .sdd/build from
    an earlier branch.
  TEXT
  type        = string
}
