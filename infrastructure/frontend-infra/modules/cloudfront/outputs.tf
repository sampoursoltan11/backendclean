# ============================================================================
# CloudFront Module - Outputs
# ============================================================================

output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_zone_id" {
  description = "Zone ID of the CloudFront distribution (for Route53)"
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
}

output "origin_access_control_id" {
  description = "ID of the Origin Access Control"
  value       = aws_cloudfront_origin_access_control.frontend.id
}
