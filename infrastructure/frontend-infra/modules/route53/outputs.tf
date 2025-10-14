# ============================================================================
# Route53 Module - Outputs
# ============================================================================

output "dns_name" {
  description = "DNS name configured"
  value       = aws_route53_record.frontend.name
}

output "dns_fqdn" {
  description = "Fully qualified domain name"
  value       = aws_route53_record.frontend.fqdn
}

output "www_dns_name" {
  description = "WWW subdomain DNS name (if created)"
  value       = var.create_www_record ? aws_route53_record.frontend_www[0].name : ""
}
