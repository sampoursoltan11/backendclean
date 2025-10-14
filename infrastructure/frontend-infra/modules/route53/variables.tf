# ============================================================================
# Route53 Module - Variables
# ============================================================================

variable "domain_name" {
  description = "Domain name for the frontend"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
}

variable "cloudfront_zone_id" {
  description = "CloudFront distribution zone ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "create_www_record" {
  description = "Create www subdomain record"
  type        = bool
  default     = false
}
