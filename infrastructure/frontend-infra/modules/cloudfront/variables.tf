# ============================================================================
# CloudFront Module - Variables
# ============================================================================

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "s3_bucket_id" {
  description = "ID of the S3 bucket"
  type        = string
}

variable "s3_bucket_domain" {
  description = "Regional domain name of the S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN (must be in us-east-1)"
  type        = string
  default     = ""
}

variable "create_certificate" {
  description = "Whether to create ACM certificate"
  type        = bool
  default     = false
}

variable "price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_100"
}

variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false
}

variable "logging_bucket" {
  description = "S3 bucket for CloudFront logs"
  type        = string
  default     = ""
}
