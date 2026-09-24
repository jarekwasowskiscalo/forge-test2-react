# Aurora Serverless v2 (PostgreSQL), and optionally a proxy in front of it.
#
# **`min_capacity = 0` is the whole point.** Between requests the cluster scales
# to nothing and the bill is storage alone. What it costs is a resume of roughly
# ten to fifteen seconds on the first request after a quiet period -- which is
# why the API function's timeout is thirty seconds and why production sets a
# non-zero floor instead.
#
# **The proxy is not a per-environment choice: `enable_proxy` REFUSES `true`.**
# The validation is on the variable (`variables.tf`), so `terraform validate`
# raises it -- and `infra/terraform/refusals/database-proxy/` is a root that exists
# to prove the refusal fires, asserted by `scripts/infra-check.sh`. The resources
# below stay, all under `count = var.enable_proxy ? 1 : 0`, because what is missing
# is two pieces of configuration rather than the resources.
#
# **Why nothing wants it yet.** It is billed by the hour whether or not anything
# connects, and this stack has a stricter substitute: with `pool_size = 1,
# max_overflow = 0` (app/db/session.py) the connection count IS the API function's
# concurrency, so a reserved-concurrency ceiling forbids the storm a proxy would
# merely queue.
#
# **Why it would not work if something did.** Two independent blockers, both found
# by reading rather than by running, and neither visible on dev, which never had a
# proxy:
#
#   - **Auth.** A proxy authenticates a client by the username inside one of its
#     secrets, and the single `auth` block below names the MASTER secret. `app_iam`
#     has no secret, so it could not log in at all -- and `endpoint` BECOMES the
#     proxy when the flag is on (`outputs.tf`), so the API function is routed at a
#     proxy that has no entry for it.
#   - **Network.** `modules/network` creates a self-referencing EGRESS rule on the
#     database group and no self-referencing INGRESS rule; the group's only ingress
#     admits the `lambda` group. Proxy-ENI to cluster-ENI is evaluated in both
#     directions, so the proxy would report every target unavailable with a
#     health-check message naming no cause. Fixing auth alone would not connect.
#
# A third was real and is fixed: the migration function was routed through the proxy
# too (its URL was built from the endpoint output) while presenting a password to an
# `iam_auth = "REQUIRED"` entry, and was refused. `cluster_endpoint` exists so that
# client goes straight to the cluster.
#
# **The arrangement to build, for the day a second long-lived client makes a proxy
# worth its bill.** Not the one this header used to recommend -- a second secret and
# `app_iam` taken out of `rds_iam` -- which rested on the premise that a proxy can
# only reach the database by password. That premise is stale: the pinned provider
# (`~> 6.0`, locked at 6.62.0) exposes `default_auth_scheme`, whose accepted values
# are `NONE` and `IAM_AUTH`, and end-to-end IAM authentication needs no Secrets
# Manager secret for the client at all. So:
#
#   - `default_auth_scheme = "IAM_AUTH"` on `aws_db_proxy`, and no `auth` block for
#     the application (`auth` is required only when the scheme is `NONE`);
#   - `app_iam` STAYS in `rds_iam`, and app/db/iam_auth.py needs no change;
#   - `aws_iam_role_policy.proxy_reads_the_secret` becomes an `rds-db:connect`
#     policy, and `outputs.tf`'s `iam_auth_resource_arn` needs its proxy form
#     checked against a live account;
#   - `modules/network` gains the self-referencing ingress rule.
#
# One caveat to settle ON an account rather than by reading: the same AWS page that
# documents `IAM_AUTH` also still says a proxy "always connects to the database using
# password authentication through Secrets Manager". The documentation contradicts
# itself, which is the other reason this is refused rather than half-built.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# The master password. Generated here and never typed by anybody: it exists so
# the cluster can be created and so the migration function can perform DDL, and
# the API function never sees it at all (it authenticates with an IAM token).
#
# `!` and `/` and `@` and space are excluded because RDS refuses them in a master
# password -- a rule that surfaces as a create failure several minutes into an
# apply, which is a slow way to learn it.
resource "random_password" "master" {
  length           = 40
  special          = true
  override_special = "-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "master" {
  name        = "${var.name}/database/master"
  description = "Master credentials for ${var.name}. Read by people, not by the runtime."

  # Days, not immediate: a secret deleted by a mistaken `terraform destroy` on
  # the wrong environment is recoverable inside this window and gone after it.
  recovery_window_in_days = var.secret_recovery_days

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "master" {
  secret_id = aws_secretsmanager_secret.master.id
  secret_string = jsonencode({
    username = var.master_username
    password = random_password.master.result
    engine   = "postgres"
    host     = aws_rds_cluster.this.endpoint
    port     = var.port
    dbname   = var.database_name
  })
}

resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

resource "aws_rds_cluster" "this" {
  cluster_identifier = var.name
  engine             = "aurora-postgresql"
  # `provisioned`, not `serverless`: Serverless **v2** is a capacity type of a
  # provisioned cluster. `engine_mode = "serverless"` is v1, which is a different
  # and older product that does not scale to zero.
  engine_mode    = "provisioned"
  engine_version = var.engine_version

  database_name   = var.database_name
  master_username = var.master_username
  master_password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.security_group_id]
  port                   = var.port

  # What makes `app/db/iam_auth.py` work at all. Off by default, and its absence
  # shows up as an authentication failure that names nothing.
  iam_database_authentication_enabled = true

  storage_encrypted = true

  backup_retention_period = var.backup_retention_days
  # A final snapshot on destroy for anything that is not dev. Dev is torn down
  # and rebuilt on purpose, and a snapshot per teardown is a slowly growing bill
  # for data nobody will read.
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name}-final"
  # Deletion protection follows the same line as the snapshot: on where losing
  # the data would matter.
  deletion_protection = !var.skip_final_snapshot

  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
    # Only meaningful at `min_capacity = 0`, and this is the knob that decides
    # how often anybody meets the resume delay. Shorter saves more and pauses
    # more often; the default here is an hour.
    seconds_until_auto_pause = var.min_capacity == 0 ? var.seconds_until_auto_pause : null
  }

  tags = var.tags

  lifecycle {
    # The password is rotated by rotating the secret, not by re-running an apply
    # -- and an apply that quietly reset it would lock out anything holding the
    # previous value.
    ignore_changes = [master_password]
  }
}

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "${var.name}-writer"
  cluster_identifier = aws_rds_cluster.this.id
  # The literal instance class for Serverless v2. Any other value silently makes
  # this a provisioned instance with a fixed hourly cost.
  instance_class = "db.serverless"
  engine         = aws_rds_cluster.this.engine
  engine_version = aws_rds_cluster.this.engine_version

  # No public address, ever: this cluster is reachable from inside the VPC and
  # from nowhere else, which is the reason the network module needs no gateway.
  publicly_accessible = false

  tags = var.tags
}

# --------------------------------------------------------------------------- #
# The proxy, where an environment asked for one
# --------------------------------------------------------------------------- #

resource "aws_iam_role" "proxy" {
  count = var.enable_proxy ? 1 : 0
  name  = "${var.name}-rds-proxy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "rds.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

# The proxy holds the master credentials so the functions do not have to. This is
# the one thing that reads the secret, and it reads it as a service rather than
# over a route the VPC would need.
resource "aws_iam_role_policy" "proxy_reads_the_secret" {
  count = var.enable_proxy ? 1 : 0
  name  = "read-master-secret"
  role  = aws_iam_role.proxy[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.master.arn
    }]
  })
}

resource "aws_db_proxy" "this" {
  count                  = var.enable_proxy ? 1 : 0
  name                   = var.name
  engine_family          = "POSTGRESQL"
  role_arn               = aws_iam_role.proxy[0].arn
  vpc_subnet_ids         = var.subnet_ids
  vpc_security_group_ids = [var.security_group_id]
  # TLS from the function to the proxy. Not optional here: the token this
  # authenticates with is a bearer credential, and a bearer credential on a
  # cleartext connection is a password in the clear with extra steps.
  require_tls = true

  auth {
    auth_scheme = "SECRETS"
    secret_arn  = aws_secretsmanager_secret.master.arn
    iam_auth    = "REQUIRED"
    description = "IAM in front, the master secret behind"
  }

  tags = var.tags
}

resource "aws_db_proxy_default_target_group" "this" {
  count         = var.enable_proxy ? 1 : 0
  db_proxy_name = aws_db_proxy.this[0].name

  connection_pool_config {
    # The number the proxy exists to hold down. Left at the default share of the
    # cluster's own maximum, because pinning it to a number here would go stale
    # the moment `max_capacity` moves.
    max_connections_percent = 90
  }
}

resource "aws_db_proxy_target" "this" {
  count                 = var.enable_proxy ? 1 : 0
  db_cluster_identifier = aws_rds_cluster.this.id
  db_proxy_name         = aws_db_proxy.this[0].name
  target_group_name     = aws_db_proxy_default_target_group.this[0].name
}
