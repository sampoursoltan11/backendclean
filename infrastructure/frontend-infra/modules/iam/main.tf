# ============================================================================
# IAM Module - Deployment Permissions
# ============================================================================
# Creates IAM user and policies for CI/CD deployment

# ============================================================================
# IAM User for Deployment
# ============================================================================

resource "aws_iam_user" "deployment" {
  name = "tra-frontend-deploy-${var.environment}"

  tags = {
    Name        = "tra-frontend-deploy-${var.environment}"
    Environment = var.environment
    Purpose     = "Frontend Deployment"
  }
}

# ============================================================================
# IAM Policy for S3 Access
# ============================================================================

data "aws_iam_policy_document" "s3_deployment" {
  statement {
    sid    = "S3BucketAccess"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads"
    ]

    resources = [
      var.s3_bucket_arn
    ]
  }

  statement {
    sid    = "S3ObjectAccess"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:PutObjectAcl",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]

    resources = [
      "${var.s3_bucket_arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_deployment" {
  name        = "tra-frontend-s3-deploy-${var.environment}"
  description = "Policy for deploying frontend to S3"
  policy      = data.aws_iam_policy_document.s3_deployment.json
}

resource "aws_iam_user_policy_attachment" "s3_deployment" {
  user       = aws_iam_user.deployment.name
  policy_arn = aws_iam_policy.s3_deployment.arn
}

# ============================================================================
# IAM Policy for CloudFront Invalidation
# ============================================================================

data "aws_iam_policy_document" "cloudfront_invalidation" {
  statement {
    sid    = "CloudFrontInvalidation"
    effect = "Allow"

    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
      "cloudfront:ListInvalidations"
    ]

    resources = [
      var.cloudfront_distribution_arn
    ]
  }

  statement {
    sid    = "CloudFrontDistributionRead"
    effect = "Allow"

    actions = [
      "cloudfront:GetDistribution",
      "cloudfront:GetDistributionConfig"
    ]

    resources = [
      var.cloudfront_distribution_arn
    ]
  }
}

resource "aws_iam_policy" "cloudfront_invalidation" {
  name        = "tra-frontend-cloudfront-deploy-${var.environment}"
  description = "Policy for CloudFront cache invalidation"
  policy      = data.aws_iam_policy_document.cloudfront_invalidation.json
}

resource "aws_iam_user_policy_attachment" "cloudfront_invalidation" {
  user       = aws_iam_user.deployment.name
  policy_arn = aws_iam_policy.cloudfront_invalidation.arn
}

# ============================================================================
# IAM Access Key (Optional - for programmatic access)
# ============================================================================

resource "aws_iam_access_key" "deployment" {
  count = var.create_access_key ? 1 : 0
  user  = aws_iam_user.deployment.name
}
