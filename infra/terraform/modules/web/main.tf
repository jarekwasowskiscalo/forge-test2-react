# The SPA on S3, and one CloudFront distribution in front of both halves.
#
# **One domain for the screen and the API, and that is the point.** The browser
# sees a single origin, so `/api/...` is same-origin exactly as it is when one
# process serves both -- no CORS configuration anywhere, which is the property
# this application has had since it was written and did not have to give up to
# become serverless (spec/design/architecture.md § Deployment).
#
# The bucket is private. It has no website endpoint and no public policy; the
# only thing that may read it is this distribution, proved by an origin access
# control signature. A "static website" bucket would be simpler and would also
# be a bucket anybody can read directly, bypassing every header set below.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

resource "aws_s3_bucket" "site" {
  bucket        = "${var.name}-web"
  force_destroy = var.force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id
  versioning_configuration {
    # On, because a bad deploy of the SPA is otherwise unrecoverable without a
    # rebuild -- and the objects are a few hundred kilobytes, so the cost of
    # keeping their history is nothing.
    status = "Enabled"
  }
}

# What ages the history out, and what it deliberately does NOT touch.
#
# Publication is additive -- `scripts/deploy.sh` stopped passing `--delete` to either
# sync, because the source directory holds one release and `--delete` was therefore
# erasing every bundle of every release before it. Three things then accumulate, and
# only two of them may be expired on a timer:
#
#   * NONCURRENT versions -- a key written again by a later deploy. Because the assets
#     are named by content hash, that is very nearly `index.html` alone, which is
#     rewritten on every release. Nothing serves them: CloudFront asks for the plain
#     key and gets the current version. `newer_noncurrent_versions` keeps the last ten
#     whatever their age, so a bucket nobody has deployed to for a quarter still has a
#     shell history -- which is the recovery the versioning block above was turned on
#     for.
#   * DELETE MARKERS left over from the deploys that ran while `--delete` was still
#     there. Each one hides a version of a bundle that is still in the bucket and can
#     never be served again. Nothing else would ever clear them.
#   * CURRENT objects -- each release's own hashed bundles, under distinct keys.
#     **These are not expired, and the absence of a rule is the decision.** Age does not
#     mean unreferenced: an environment that has not been redeployed for the window
#     would have the bundles of the release it is actually serving deleted underneath
#     it, which is the failure this whole change removes, only on a timer. Nothing but
#     the release manifest could say an asset is unreferenced, and a delete driven by it
#     would be the same irreversible operation being taken out. The control is a number
#     rather than a rule: a build of this application is a few hundred kilobytes, so a
#     hundred releases is tens of megabytes and cents a year. That is the sentence to
#     read before adding the expiry this paragraph argues against.
resource "aws_s3_bucket_lifecycle_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    id     = "expire-superseded-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days           = 30
      newer_noncurrent_versions = 10
    }
  }

  # A delete marker whose versions have all expired hides nothing any more. Its own
  # rule, because S3 refuses `expired_object_delete_marker` beside `days` or `date`.
  rule {
    id     = "clear-emptied-delete-markers"
    status = "Enabled"

    filter {}

    expiration {
      expired_object_delete_marker = true
    }
  }

  # An upload interrupted mid-flight leaves parts that are billed and that no listing
  # shows. Unrelated to the rule above and cheap to say once.
  rule {
    id     = "abort-interrupted-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.site]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${var.name}-s3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "site" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.site.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    # Scoped to THIS distribution, not to CloudFront in general. Without the
    # condition the policy would let anybody's distribution serve this bucket.
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }

  # `s3:ListBucket` is here to change a STATUS, not to grant a listing. Without
  # it S3 answers a missing key with 403 (it will not admit that a key it would
  # not have let you read is absent), and a missing hashed bundle then reads as
  # a permissions fault -- which is the wrong thing to go and look at.
  #
  # Nothing can reach an actual listing through this distribution: a listing is
  # `GET /?list-type=2`, and `Managed-CachingOptimized` forwards no query string
  # to the origin, so the parameter that makes it a listing never arrives.
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.site.arn]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = data.aws_iam_policy_document.site.json
}

# --------------------------------------------------------------------------- #
# Distribution
# --------------------------------------------------------------------------- #

# Managed policies, by name rather than by id: the ids are opaque and the names
# say what they do.
data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  # Everything the API needs -- method, path, query, body, headers, cookies --
  # minus `Host`, which must stay the origin's own or API Gateway rejects the
  # request with a 403 that names nothing.
  name = "Managed-AllViewerExceptHostHeader"
}

# The SPA fallback. It is a function and not a pair of `custom_error_response`
# blocks, and that is the whole point rather than a preference.
#
# `CustomErrorResponses` is a member of the DISTRIBUTION -- `CacheBehavior` has
# no equivalent field -- so the error form applied in front of both origins at
# once. It turned every 403 and 404 into `200 text/html`: the API's own refusals
# (`{"code": "guestbook_entry_not_found"}` became the shell), any 403 from API
# Gateway, and a hashed bundle the previous deploy had already deleted. The
# contract held in the application and stopped holding at the edge, which is the
# worst place for it to stop, because that is the only layer a browser sees.
#
# `function_association` IS a member of a behaviour, so this reaches the S3
# behaviour and nothing else. `/api/*` has its own behaviour below and never
# invokes it.
#
# The code lives in a file rather than in a heredoc because HCL interpolates
# `${...}` inside one, which is a trap laid for whoever next writes a template
# literal in there -- and because a file can be read by a test.
resource "aws_cloudfront_function" "spa_fallback" {
  name    = "${var.name}-spa-fallback"
  runtime = "cloudfront-js-2.0"
  comment = "Rewrite SPA navigation to /index.html, and nothing else"
  publish = true
  code    = file("${path.module}/spa-fallback.js")
}

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  comment             = var.name
  default_root_object = "index.html"
  price_class         = var.price_class
  aliases             = var.aliases

  origin {
    origin_id                = "s3"
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  origin {
    origin_id   = "api"
    domain_name = var.api_endpoint

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      # The gateway's own ceiling is 29 seconds and CloudFront's maximum read
      # timeout is 60; 30 leaves the gateway to be the one that gives up, which
      # is the layer with the useful error message.
      origin_read_timeout = 30
    }
  }

  default_cache_behavior {
    target_origin_id       = "s3"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
    compress               = true

    # The SPA fallback, on this behaviour alone. A viewer-request function runs
    # before the cache is consulted, so the key is the URI it leaves behind:
    # every deep link is cached as `/index.html`, and the one-path invalidation
    # after a deploy (`scripts/deploy.sh` step 6) therefore covers all of them.
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_fallback.arn
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "api"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    # Nothing about this API is cacheable at the edge: every read is a list that
    # a write may have just changed, and a cached POST is not a thing.
    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    compress                 = true
  }

  # No `custom_error_response` here, and that absence is a decision: the SPA
  # fallback is the function associated with the behaviour above. What the edge
  # is asked for now is that it does not touch a status or a body it did not
  # produce -- a refusal the application wrote arrives as the application wrote
  # it.

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate_arn == null
    acm_certificate_arn            = var.acm_certificate_arn
    ssl_support_method             = var.acm_certificate_arn == null ? null : "sni-only"
    minimum_protocol_version       = var.acm_certificate_arn == null ? "TLSv1" : "TLSv1.2_2021"
  }

  tags = var.tags
}
