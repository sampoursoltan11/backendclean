# ============================================================================
# TRA Frontend Infrastructure - Main Configuration
# ============================================================================
# This is the main entry point for Terraform infrastructure deployment
# It orchestrates all resources needed for the TRA frontend system

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state (recommended for team environments)
  # backend "s3" {
  #   bucket         = "tra-terraform-state"
  #   key            = "tra-frontend/terraform.tfstate"
  #   region         = "ap-southeast-2"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TRA-System"
      Component   = "Frontend"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "backendclean"
    }
  }
}

# CloudFront requires ACM certificates in us-east-1
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "TRA-System"
      Component   = "Frontend"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "backendclean"
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# Modules
# ============================================================================

# S3 Bucket for static website hosting
module "s3" {
  source = "./modules/s3"

  bucket_name = var.s3_bucket_name
  environment = var.environment
}

# CloudFront CDN for global content delivery
module "cloudfront" {
  source = "./modules/cloudfront"

  environment       = var.environment
  s3_bucket_id      = module.s3.bucket_id
  s3_bucket_domain  = module.s3.bucket_regional_domain_name
  s3_bucket_arn     = module.s3.bucket_arn
  domain_name       = var.domain_name
  create_certificate = var.create_certificate
  certificate_arn   = var.certificate_arn
  price_class       = var.cloudfront_price_class
}

# Route53 DNS configuration (optional)
module "route53" {
  source = "./modules/route53"
  count  = var.create_route53 ? 1 : 0

  domain_name              = var.domain_name
  hosted_zone_id          = var.hosted_zone_id
  cloudfront_domain_name  = module.cloudfront.cloudfront_domain_name
  cloudfront_zone_id      = module.cloudfront.cloudfront_zone_id
  environment             = var.environment
}

# IAM policies for deployment
module "iam" {
  source = "./modules/iam"

  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
  cloudfront_distribution_arn = module.cloudfront.distribution_arn
}

# ============================================================================
# S3 Bucket Policy (after CloudFront creation)
# ============================================================================

data "aws_iam_policy_document" "s3_cloudfront_access" {
  statement {
    sid    = "AllowCloudFrontOAC"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${module.s3.bucket_arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [module.cloudfront.distribution_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = module.s3.bucket_id
  policy = data.aws_iam_policy_document.s3_cloudfront_access.json
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  common_tags = {
    Project     = var.project_name
    Component   = "Frontend"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}
