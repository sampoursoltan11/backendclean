# ============================================================================
# Route53 Module - DNS Configuration
# ============================================================================
# Creates DNS records for custom domain pointing to CloudFront

# ============================================================================
# Route53 Record for CloudFront
# ============================================================================

resource "aws_route53_record" "frontend" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

# ============================================================================
# IPv6 Support (AAAA record)
# ============================================================================

resource "aws_route53_record" "frontend_ipv6" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

# ============================================================================
# WWW Subdomain (optional)
# ============================================================================

resource "aws_route53_record" "frontend_www" {
  count   = var.create_www_record ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "frontend_www_ipv6" {
  count   = var.create_www_record ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}
