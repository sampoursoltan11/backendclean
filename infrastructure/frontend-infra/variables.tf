# ============================================================================
# TRA Frontend Infrastructure - Variables
# ============================================================================

# ============================================================================
# General Configuration
# ============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "tra-system"
}

variable "environment" {
  description = "Environment name (e.g., development, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "ap-southeast-2"
}

# ============================================================================
# S3 Configuration
# ============================================================================

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for static website hosting"
  type        = string
}

# ============================================================================
# CloudFront Configuration
# ============================================================================

variable "cloudfront_price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_100"  # US, Canada, Europe, Asia

  validation {
    condition     = contains(["PriceClass_All", "PriceClass_200", "PriceClass_100"], var.cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_All, PriceClass_200, PriceClass_100"
  }
}

# ============================================================================
# Domain and SSL Configuration
# ============================================================================

variable "domain_name" {
  description = "Domain name for the frontend application (optional)"
  type        = string
  default     = ""
}

variable "create_certificate" {
  description = "Whether to create ACM certificate for custom domain"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "ARN of existing ACM certificate (must be in us-east-1 for CloudFront)"
  type        = string
  default     = ""
}

# ============================================================================
# Route53 Configuration
# ============================================================================

variable "create_route53" {
  description = "Whether to create Route53 DNS records"
  type        = bool
  default     = false
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for DNS records"
  type        = string
  default     = ""
}

# ============================================================================
# Tags
# ============================================================================

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
