# ============================================================================
# DynamoDB Module - Optimized Table with GSI Indexes
# ============================================================================
# Creates DynamoDB table with all 5 optimized GSI indexes for cost reduction

resource "aws_dynamodb_table" "tra_system" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # On-demand billing (no capacity planning needed)

  # Primary Key
  hash_key  = "pk"
  range_key = "sk"

  # ============================================================================
  # Attribute Definitions
  # ============================================================================
  # Only define attributes used in keys (primary or GSI keys)

  # Primary key attributes
  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  # GSI 2: Session Index attributes
  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "entity_type"
    type = "S"
  }

  # GSI 3: Assessment Events attributes
  attribute {
    name = "assessment_id"
    type = "S"
  }

  attribute {
    name = "event_type"
    type = "S"
  }

  # GSI 4: State Index attributes
  attribute {
    name = "current_state"
    type = "S"
  }

  attribute {
    name = "updated_at"
    type = "S"
  }

  # GSI 5: Title Search attributes
  attribute {
    name = "title_lowercase"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # ============================================================================
  # Global Secondary Indexes
  # ============================================================================
  # Note: GSI1 (gsi1_pk + gsi1_sk) already exists in production for document-to-assessment
  # mapping. It's maintained by link_documents_to_assessment() method.
  # Adding it here is optional since it may already exist.

  # GSI 2: Query documents/messages by session
  # Replaces SCAN in: get_session_messages(), link_documents_to_assessment()
  # Cost reduction: 70-90%
  global_secondary_index {
    name            = "gsi2-session-entity"
    hash_key        = "session_id"
    range_key       = "entity_type"
    projection_type = "ALL"
  }

  # GSI 3: Query events by assessment
  # Replaces SCAN in: get_assessment_events(), get_assessment_reviews()
  # Performance: 10-100x faster
  global_secondary_index {
    name            = "gsi3-assessment-events"
    hash_key        = "assessment_id"
    range_key       = "event_type"
    projection_type = "ALL"
  }

  # GSI 4: Query assessments by state
  # Replaces SCAN in: query_assessments_by_state()
  # Enables filtering by status: draft, in_progress, completed
  global_secondary_index {
    name            = "gsi4-state-updated"
    hash_key        = "current_state"
    range_key       = "updated_at"
    projection_type = "ALL"
  }

  # GSI 5: Search assessments by title
  # Replaces SCAN in: search_assessments()
  # Note: Requires title_lowercase attribute in items
  global_secondary_index {
    name            = "gsi5-title-search"
    hash_key        = "title_lowercase"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # GSI 6: List items by entity type
  # Replaces SCAN in: search_assessments()
  # Enables efficient listing by type with sorting by recency
  global_secondary_index {
    name            = "gsi6-entity-type"
    hash_key        = "entity_type"
    range_key       = "updated_at"
    projection_type = "ALL"
  }

  # ============================================================================
  # Advanced Features
  # ============================================================================

  # Point-in-time recovery (automatic backups for 35 days)
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.environment == "production" ? aws_kms_key.dynamodb[0].arn : null
  }

  # Deletion protection (enabled for production)
  deletion_protection_enabled = var.environment == "production"

  # DynamoDB Streams (optional - uncomment if needed for CDC)
  # stream_enabled   = var.enable_streams
  # stream_view_type = "NEW_AND_OLD_IMAGES"

  # TTL (Time To Live) - optional, uncomment if needed
  # ttl {
  #   attribute_name = "ttl"
  #   enabled        = true
  # }

  tags = merge(
    var.tags,
    {
      Name        = var.table_name
      Environment = var.environment
      Purpose     = "TRA Backend Data Store"
      Optimized   = "true"
      GSI_Count   = "5"
    }
  )
}

# ============================================================================
# KMS Key for Production Encryption
# ============================================================================

resource "aws_kms_key" "dynamodb" {
  count                   = var.environment == "production" ? 1 : 0
  description             = "KMS key for DynamoDB table encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name        = "${var.table_name}-encryption-key"
      Environment = var.environment
    }
  )
}

resource "aws_kms_alias" "dynamodb" {
  count         = var.environment == "production" ? 1 : 0
  name          = "alias/${var.table_name}"
  target_key_id = aws_kms_key.dynamodb[0].key_id
}

# ============================================================================
# CloudWatch Alarms for Monitoring
# ============================================================================

# Alarm for throttled requests
resource "aws_cloudwatch_metric_alarm" "throttled_requests" {
  alarm_name          = "${var.table_name}-throttled-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This metric monitors DynamoDB throttled requests"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.tra_system.name
  }

  tags = var.tags
}

# Alarm for read capacity
resource "aws_cloudwatch_metric_alarm" "read_throttle" {
  alarm_name          = "${var.table_name}-read-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "This metric monitors DynamoDB read throttle events"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.tra_system.name
  }

  tags = var.tags
}
