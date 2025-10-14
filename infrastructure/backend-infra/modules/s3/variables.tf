# S3 Module Variables

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning for the bucket"
  type        = bool
  default     = true
}

variable "lifecycle_glacier_days" {
  description = "Days before moving old versions to Glacier"
  type        = number
  default     = 90
}

variable "lifecycle_expiration_days" {
  description = "Days before expiring old versions"
  type        = number
  default     = 365
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "size_alarm_threshold_gb" {
  description = "Bucket size alarm threshold in GB"
  type        = number
  default     = 100
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
