# ============================================================================
# CloudFront Module - CDN Distribution
# ============================================================================
# Creates a CloudFront distribution for global content delivery

# ============================================================================
# CloudFront Origin Access Control (OAC) - Modern approach
# ============================================================================

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.environment}-tra-frontend-oac"
  description                       = "Origin Access Control for TRA Frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ============================================================================
# CloudFront Distribution
# ============================================================================

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "TRA Frontend Distribution - ${var.environment}"
  default_root_object = "enterprise_tra_home_clean.html"
  price_class         = var.price_class

  # Aliases (custom domain names)
  aliases = var.domain_name != "" ? [var.domain_name] : []

  # S3 Origin
  origin {
    domain_name              = var.s3_bucket_domain
    origin_id                = "S3-${var.s3_bucket_id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600    # 1 hour
    max_ttl                = 86400   # 24 hours
    compress               = true
  }

  # Cache behavior for static assets (JS, CSS, images)
  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    forwarded_values {
      query_string = false
      headers      = ["Origin"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400   # 24 hours
    max_ttl                = 31536000 # 1 year
    compress               = true
  }

  # Cache behavior for API calls (no caching)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.s3_bucket_id}"

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = false
  }

  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate
  viewer_certificate {
    # Use custom SSL certificate if provided
    dynamic "acm_certificate_arn" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        acm_certificate_arn      = var.certificate_arn
        ssl_support_method       = "sni-only"
        minimum_protocol_version = "TLSv1.2_2021"
      }
    }

    # Use default CloudFront certificate
    dynamic "cloudfront_default_certificate" {
      for_each = var.certificate_arn == "" ? [1] : []
      content {
        cloudfront_default_certificate = true
      }
    }

    # Fallback to default if no certificate
    cloudfront_default_certificate = var.certificate_arn == "" ? true : false
    acm_certificate_arn            = var.certificate_arn != "" ? var.certificate_arn : null
    ssl_support_method             = var.certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version       = var.certificate_arn != "" ? "TLSv1.2_2021" : "TLSv1"
  }

  # Custom error responses
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/enterprise_tra_home_clean.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/enterprise_tra_home_clean.html"
  }

  # Logging configuration (optional)
  dynamic "logging_config" {
    for_each = var.enable_logging ? [1] : []
    content {
      include_cookies = false
      bucket          = "${var.logging_bucket}.s3.amazonaws.com"
      prefix          = "cloudfront-logs/${var.environment}/"
    }
  }

  tags = {
    Name        = "tra-frontend-${var.environment}"
    Environment = var.environment
    Purpose     = "Frontend CDN"
  }

  # Wait for OAC to be created
  depends_on = [aws_cloudfront_origin_access_control.frontend]
}
