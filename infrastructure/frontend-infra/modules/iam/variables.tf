# ============================================================================
# IAM Module - Variables
# ============================================================================

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  type        = string
}

variable "create_access_key" {
  description = "Create IAM access key for programmatic access"
  type        = bool
  default     = false
}
