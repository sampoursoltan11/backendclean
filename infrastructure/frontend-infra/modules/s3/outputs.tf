# ============================================================================
# S3 Module - Outputs
# ============================================================================

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.frontend.id
}

output "bucket_id" {
  description = "ID of the S3 bucket"
  value       = aws_s3_bucket.frontend.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.frontend.arn
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "website_endpoint" {
  description = "S3 website endpoint"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "website_domain" {
  description = "S3 website domain"
  value       = aws_s3_bucket_website_configuration.frontend.website_domain
}
