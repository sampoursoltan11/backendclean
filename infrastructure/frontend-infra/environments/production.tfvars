# ============================================================================
# Production Environment Configuration
# ============================================================================

environment = "production"
aws_region  = "ap-southeast-2"

# S3 Configuration
s3_bucket_name = "tra-frontend-prod"

# CloudFront Configuration
cloudfront_price_class = "PriceClass_All"  # Global distribution for production

# Domain Configuration (optional - configure for custom domain)
domain_name         = ""  # e.g., "tra.yourcompany.com"
create_certificate  = false
certificate_arn     = ""  # ARN of ACM certificate in us-east-1

# Route53 Configuration (optional - enable for custom domain)
create_route53  = false
hosted_zone_id  = ""  # Route53 hosted zone ID

# Additional Tags
tags = {
  CostCenter  = "Production"
  Team        = "Engineering"
  Criticality = "High"
}
