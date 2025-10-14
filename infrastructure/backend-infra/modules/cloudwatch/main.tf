# ============================================================================
# CloudWatch Module - Logging and Monitoring
# ============================================================================

# Application log group
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/tra-system/${var.environment}/application"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# ECS log group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/aws/ecs/tra-system-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# System metrics dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "tra-system-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { stat = "Sum" }],
            [".", "ConsumedWriteCapacityUnits", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "DynamoDB Capacity"
        }
      }
    ]
  })
}
