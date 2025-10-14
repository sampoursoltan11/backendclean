# ============================================================================
# S3 Module - Document Storage Bucket
# ============================================================================
# Creates S3 bucket for TRA document storage with versioning and lifecycle

resource "aws_s3_bucket" "documents" {
  bucket = var.bucket_name

  tags = merge(
    var.tags,
    {
      Name        = var.bucket_name
      Environment = var.environment
      Purpose     = "TRA Document Storage"
    }
  )
}

# ============================================================================
# Bucket Versioning
# ============================================================================

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# ============================================================================
# Server-Side Encryption
# ============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.environment == "production" ? "aws:kms" : "AES256"
      kms_master_key_id = var.environment == "production" ? aws_kms_key.s3[0].arn : null
    }
    bucket_key_enabled = true
  }
}

# ============================================================================
# Block Public Access
# ============================================================================

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Lifecycle Rules
# ============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  # Move old versions to cheaper storage
  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = var.lifecycle_glacier_days
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.lifecycle_expiration_days
    }
  }

  # Abort incomplete multipart uploads
  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ============================================================================
# CORS Configuration
# ============================================================================

resource "aws_s3_bucket_cors_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# ============================================================================
# KMS Key for Production
# ============================================================================

resource "aws_kms_key" "s3" {
  count                   = var.environment == "production" ? 1 : 0
  description             = "KMS key for S3 bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name        = "${var.bucket_name}-encryption-key"
      Environment = var.environment
    }
  )
}

resource "aws_kms_alias" "s3" {
  count         = var.environment == "production" ? 1 : 0
  name          = "alias/${var.bucket_name}"
  target_key_id = aws_kms_key.s3[0].key_id
}

# ============================================================================
# CloudWatch Metrics
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "bucket_size" {
  alarm_name          = "${var.bucket_name}-size-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = 86400 # 24 hours
  statistic           = "Average"
  threshold           = var.size_alarm_threshold_gb * 1024 * 1024 * 1024
  alarm_description   = "S3 bucket size exceeds ${var.size_alarm_threshold_gb}GB"

  dimensions = {
    BucketName  = aws_s3_bucket.documents.id
    StorageType = "StandardStorage"
  }

  tags = var.tags
}
