# ============================================================================
# Development Environment Configuration
# ============================================================================

environment = "development"
aws_region  = "ap-southeast-2"

# S3 Configuration
s3_bucket_name = "tra-frontend-dev"

# CloudFront Configuration
cloudfront_price_class = "PriceClass_100"  # US, Canada, Europe, Asia

# Domain Configuration (optional)
domain_name         = ""  # Leave empty to use CloudFront domain
create_certificate  = false
certificate_arn     = ""

# Route53 Configuration (optional)
create_route53  = false
hosted_zone_id  = ""

# Additional Tags
tags = {
  CostCenter = "Development"
  Team       = "Engineering"
}
