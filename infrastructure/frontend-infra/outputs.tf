# ============================================================================
# TRA Frontend Infrastructure - Outputs
# ============================================================================

# ============================================================================
# S3 Outputs
# ============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the frontend"
  value       = module.s3.bucket_name
}

output "s3_bucket_id" {
  description = "ID of the S3 bucket"
  value       = module.s3.bucket_id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "s3_website_endpoint" {
  description = "S3 website endpoint URL"
  value       = module.s3.website_endpoint
}

# ============================================================================
# CloudFront Outputs
# ============================================================================

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = module.cloudfront.distribution_arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.cloudfront.cloudfront_domain_name
}

output "cloudfront_url" {
  description = "Full HTTPS URL of the CloudFront distribution"
  value       = "https://${module.cloudfront.cloudfront_domain_name}"
}

# ============================================================================
# Route53 Outputs
# ============================================================================

output "domain_name" {
  description = "Custom domain name (if configured)"
  value       = var.create_route53 ? var.domain_name : ""
}

output "frontend_url" {
  description = "Primary URL to access the frontend"
  value       = var.create_route53 ? "https://${var.domain_name}" : "https://${module.cloudfront.cloudfront_domain_name}"
}

# ============================================================================
# IAM Outputs
# ============================================================================

output "deployment_user_name" {
  description = "IAM user name for CI/CD deployments"
  value       = module.iam.deployment_user_name
}

output "deployment_user_arn" {
  description = "IAM user ARN for CI/CD deployments"
  value       = module.iam.deployment_user_arn
}

# ============================================================================
# Environment Configuration Output
# ============================================================================

output "frontend_config" {
  description = "Complete frontend configuration for deployment"
  value = {
    s3_bucket_name           = module.s3.bucket_name
    cloudfront_distribution_id = module.cloudfront.distribution_id
    cloudfront_url           = "https://${module.cloudfront.cloudfront_domain_name}"
    frontend_url             = var.create_route53 ? "https://${var.domain_name}" : "https://${module.cloudfront.cloudfront_domain_name}"
    aws_region               = var.aws_region
    environment              = var.environment
  }
}

# ============================================================================
# Deployment Instructions
# ============================================================================

output "deployment_instructions" {
  description = "Instructions for deploying the frontend"
  value = <<-EOT

    ============================================
    Frontend Deployment Instructions
    ============================================

    1. Build your frontend:
       cd frontend && npm run build

    2. Deploy to S3:
       aws s3 sync dist/ s3://${module.s3.bucket_name}/ --delete

    3. Invalidate CloudFront cache:
       aws cloudfront create-invalidation \
         --distribution-id ${module.cloudfront.distribution_id} \
         --paths "/*"

    4. Access your frontend:
       ${var.create_route53 ? "https://${var.domain_name}" : "https://${module.cloudfront.cloudfront_domain_name}"}

    ============================================
  EOT
}
