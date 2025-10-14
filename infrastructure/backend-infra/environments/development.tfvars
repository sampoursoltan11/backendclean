# Development Environment Configuration

environment          = "development"
aws_region          = "ap-southeast-2"
dynamodb_table_name = "tra-system-dev"
s3_bucket_name      = "tra-agent-docs-dev"

# Logging
log_level           = "DEBUG"
log_retention_days  = 7

# Optional: Enable ECS for containerized deployment
create_ecs = false
create_vpc = false
