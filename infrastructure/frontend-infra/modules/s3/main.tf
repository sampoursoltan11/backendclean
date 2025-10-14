# ============================================================================
# S3 Module - Static Website Hosting
# ============================================================================
# Creates an S3 bucket configured for static website hosting with CloudFront

# ============================================================================
# S3 Bucket
# ============================================================================

resource "aws_s3_bucket" "frontend" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    Purpose     = "Frontend Static Website"
  }
}

# ============================================================================
# Bucket Versioning
# ============================================================================

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ============================================================================
# Bucket Encryption
# ============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ============================================================================
# Block Public Access (CloudFront will access via OAI)
# ============================================================================

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Note: Bucket Policy is created in main.tf after CloudFront distribution
# to avoid circular dependency
# ============================================================================

# ============================================================================
# Bucket Website Configuration
# ============================================================================

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "enterprise_tra_home_clean.html"
  }

  error_document {
    key = "error.html"
  }
}

# ============================================================================
# Lifecycle Rules
# ============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ============================================================================
# CORS Configuration
# ============================================================================

resource "aws_s3_bucket_cors_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
