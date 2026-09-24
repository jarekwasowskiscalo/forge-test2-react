variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "state_bucket_name" {
  description = <<-TEXT
    Globally unique, so it carries the account id or something else nobody else
    has. Whatever you choose goes into the `bucket` line of every environment's
    backend.tf -- a backend block cannot take a variable, which is why this is
    the one value that has to be copied by hand.
  TEXT
  type        = string
}

variable "github_repository" {
  description = "owner/name. Decides which workflows may assume the deploy role."
  type        = string
}

variable "deploy_role_name" {
  type    = string
  default = "sdd-guestbook-deploy"
}

variable "preview_role_name" {
  description = <<-TEXT
    The role the `preview` GitHub Environment assumes. Separate from the deploy
    role so a preview can be denied the long-lived environments' state and secrets
    -- see the Deny policy in main.tf.
  TEXT
  type        = string
  default     = "sdd-guestbook-preview"
}

variable "plan_role_name" {
  description = "The read-only role people assume in order to run `infra.sh <env> plan`."
  type        = string
  default     = "sdd-guestbook-plan"
}

variable "plan_role_principals" {
  description = <<-TEXT
    Who may assume the read-only role: SSO permission-set roles, IAM users, or an
    account root ARN. **Empty creates no role at all**, which is the right default
    for an account that has not decided yet -- a role trusting nobody is a resource
    that only looks like a control.

    Nothing here may be given write access. That no human-assumable role can apply
    anything is what makes "only GitHub deploys" true rather than merely stated.
  TEXT
  type        = list(string)
  default     = []
}

variable "deploy_policy_arn" {
  description = <<-TEXT
    What the deploy role may do. `AdministratorAccess` by default because this
    stack creates resources across a dozen services and a wrong guess fails
    mid-apply. Replace it with a scoped policy if that trade is not acceptable --
    see the comment above the attachment.
  TEXT
  type        = string
  default     = "arn:aws:iam::aws:policy/AdministratorAccess"
}

variable "create_oidc_provider" {
  description = <<-TEXT
    False if this account already has GitHub's OIDC provider -- there can be only
    one per account, and a second `terraform apply` that tried to create it fails
    with EntityAlreadyExists.
  TEXT
  type        = bool
  default     = true
}
