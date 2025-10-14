# Production Environment Configuration

environment          = "production"
aws_region          = "ap-southeast-2"
dynamodb_table_name = "tra-system"
s3_bucket_name      = "tra-agent-docs-prod"

# Logging
log_level           = "INFO"
log_retention_days  = 30

# Optional: Enable ECS for containerized deployment
create_ecs = false
create_vpc = false
