# ============================================================================
# TRA Backend Infrastructure - Outputs
# ============================================================================
# Define outputs that will be displayed after deployment

# ============================================================================
# General Outputs
# ============================================================================

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

# ============================================================================
# DynamoDB Outputs
# ============================================================================

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.dynamodb.table_arn
}

output "dynamodb_gsi_names" {
  description = "List of Global Secondary Index names"
  value       = module.dynamodb.gsi_names
}

# ============================================================================
# S3 Outputs
# ============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.s3.bucket_domain_name
}

# ============================================================================
# IAM Outputs
# ============================================================================

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = module.iam.ecs_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = module.iam.ecs_task_role_arn
}

output "backend_service_role_arn" {
  description = "ARN of the backend service role"
  value       = module.iam.backend_service_role_arn
}

# ============================================================================
# CloudWatch Outputs
# ============================================================================

output "application_log_group_name" {
  description = "Name of the application CloudWatch log group"
  value       = module.cloudwatch.application_log_group_name
}

output "application_log_group_arn" {
  description = "ARN of the application CloudWatch log group"
  value       = module.cloudwatch.application_log_group_arn
}

# ============================================================================
# VPC Outputs (if created)
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? module.vpc[0].vpc_id : var.existing_vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = var.create_vpc ? module.vpc[0].private_subnet_ids : var.existing_private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = var.create_vpc ? module.vpc[0].public_subnet_ids : var.existing_public_subnet_ids
}

# ============================================================================
# ECS Outputs (if created)
# ============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.create_ecs ? module.ecs[0].cluster_name : null
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = var.create_ecs ? module.ecs[0].cluster_arn : null
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = var.create_ecs ? module.ecs[0].service_name : null
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = var.create_ecs ? module.ecs[0].alb_dns_name : null
}

output "backend_url" {
  description = "URL to access the backend API"
  value       = var.create_ecs ? "http://${module.ecs[0].alb_dns_name}" : "Configure manually"
}

# ============================================================================
# Configuration Summary
# ============================================================================

output "configuration_summary" {
  description = "Summary of deployed configuration"
  value = {
    project           = var.project_name
    environment       = var.environment
    region            = var.aws_region
    dynamodb_table    = module.dynamodb.table_name
    s3_bucket         = module.s3.bucket_name
    vpc_created       = var.create_vpc
    ecs_created       = var.create_ecs
    bedrock_model     = var.bedrock_model_id
  }
}

# ============================================================================
# Application Configuration
# ============================================================================

output "application_config" {
  description = "Environment variables for application configuration"
  value = {
    DYNAMODB_TABLE_NAME = module.dynamodb.table_name
    AWS_REGION          = var.aws_region
    S3_BUCKET_NAME      = module.s3.bucket_name
    BEDROCK_MODEL_ID    = var.bedrock_model_id
    BEDROCK_REGION      = var.aws_region
    LOG_LEVEL           = var.log_level
  }
  sensitive = false
}

# ============================================================================
# Cost Estimation
# ============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (approximate)"
  value = {
    dynamodb_ondemand = "~$0.25 per GB storage + per-request pricing"
    s3_storage        = "~$0.023 per GB"
    cloudwatch_logs   = "~$0.50 per GB ingested"
    ecs_fargate       = var.create_ecs ? "~$${var.ecs_desired_count * 0.04048 * 730} (${var.ecs_cpu}/${var.ecs_memory})" : "N/A"
    bedrock_claude    = "~$0.25 per 1K input tokens, ~$1.25 per 1K output tokens"
    total_estimate    = "Varies based on usage - monitor CloudWatch billing"
  }
}
