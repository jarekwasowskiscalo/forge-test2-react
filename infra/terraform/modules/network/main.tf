# The smallest network that can hold a Lambda and an Aurora cluster.
#
# **There is no internet gateway, no NAT gateway and no interface endpoint**, and
# that is a decision rather than an omission. The function reaches exactly one
# thing -- the database -- and that thing is inside this VPC. A NAT gateway would
# cost about thirty dollars a month per environment to carry traffic nobody
# sends, and it is the single largest line on the bill of most small serverless
# stacks.
#
# What that costs in return: the function cannot call Secrets Manager, S3 or any
# other AWS API at runtime. `app/db/iam_auth.py` is what makes that affordable --
# an IAM auth token is signed locally, so authenticating to the database needs no
# route to anything.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block = var.cidr_block
  # Both on, because RDS Proxy and the Aurora endpoint are reached by DNS name
  # and resolve to private addresses. Without them the function fails to resolve
  # a hostname, which reads as a network problem rather than a VPC setting.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, { Name = var.name })
}

# Two subnets because Aurora demands a subnet group spanning at least two
# availability zones -- even for a single instance, and even in dev. One is not
# an option this module can offer.
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.cidr_block, 4, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, { Name = "${var.name}-private-${count.index}" })
}

# No route table of our own: the VPC's main route table has the local route and
# nothing else, which is exactly the reachability this network is supposed to
# have. Adding an empty one would be a resource that says nothing.

resource "aws_security_group" "lambda" {
  name        = "${var.name}-lambda"
  description = "The functions. Egress to the database and nowhere else."
  vpc_id      = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.name}-lambda" })
}

resource "aws_security_group" "database" {
  name        = "${var.name}-database"
  description = "Aurora and its proxy. Ingress from the functions only."
  vpc_id      = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.name}-database" })
}

# The two rules are separate resources rather than inline blocks, because inline
# blocks and separate rules cannot be mixed on one group -- and a group that
# starts inline has to be recreated to gain a rule later, which for a database
# security group means downtime for a syntax choice.
resource "aws_vpc_security_group_egress_rule" "lambda_to_database" {
  security_group_id            = aws_security_group.lambda.id
  referenced_security_group_id = aws_security_group.database.id
  from_port                    = var.database_port
  to_port                      = var.database_port
  ip_protocol                  = "tcp"
  description                  = "Postgres, to the database security group"
}

resource "aws_vpc_security_group_ingress_rule" "database_from_lambda" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.lambda.id
  from_port                    = var.database_port
  to_port                      = var.database_port
  ip_protocol                  = "tcp"
  description                  = "Postgres, from the functions"
}

# RDS Proxy sits in the same group and connects onward to the cluster, so the
# group has to allow itself -- in BOTH directions, and only one of them is here.
#
# This comment used to stop at "the group has to allow itself", above a rule that
# covers the egress half alone: the ENI-to-ENI hop is evaluated twice, and the
# group's only ingress rule (`database_from_lambda`) admits the functions and not
# the group. So the sentence promised a rule that does not exist, which is the
# expensive kind of comment -- whoever came to check would read it and stop looking.
#
# It is left half-done deliberately rather than completed here. `enable_proxy` now
# REFUSES `true` (`modules/database/variables.tf`), so no proxy can be created to
# be broken by the gap, and the missing `aws_vpc_security_group_ingress_rule` is one
# of the two things the header of `modules/database/main.tf` lists as required
# before the switch can open. Adding it now would be an ingress rule guarding
# nothing, and would take with it the only record of why the switch is shut.
resource "aws_vpc_security_group_egress_rule" "database_to_itself" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.database.id
  from_port                    = var.database_port
  to_port                      = var.database_port
  ip_protocol                  = "tcp"
  description                  = "The proxy reaching the cluster"
}
