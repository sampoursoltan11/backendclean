# ============================================================================
# TRA Backend Infrastructure - Variables
# ============================================================================
# Define all input variables for infrastructure configuration

# ============================================================================
# General Configuration
# ============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "tra-system"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "ap-southeast-2"
}

# ============================================================================
# DynamoDB Configuration
# ============================================================================

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
  default     = "tra-system"
}

# ============================================================================
# S3 Configuration
# ============================================================================

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  type        = string
  default     = "tra-agent-docs"
}

variable "s3_enable_versioning" {
  description = "Enable versioning for S3 bucket"
  type        = bool
  default     = true
}

variable "s3_lifecycle_days" {
  description = "Days before transitioning objects to Glacier"
  type        = number
  default     = 90
}

# ============================================================================
# Bedrock Configuration
# ============================================================================

variable "bedrock_model_id" {
  description = "Bedrock model ID for LLM operations"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

# ============================================================================
# Logging Configuration
# ============================================================================

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, or ERROR."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# ============================================================================
# VPC Configuration (Optional)
# ============================================================================

variable "create_vpc" {
  description = "Create a new VPC for the backend"
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (if not creating new VPC)"
  type        = string
  default     = ""
}

variable "existing_private_subnet_ids" {
  description = "Existing private subnet IDs (if not creating new VPC)"
  type        = list(string)
  default     = []
}

variable "existing_public_subnet_ids" {
  description = "Existing public subnet IDs (if not creating new VPC)"
  type        = list(string)
  default     = []
}

# ============================================================================
# ECS Configuration (Optional - for containerized deployment)
# ============================================================================

variable "create_ecs" {
  description = "Create ECS cluster and service for FastAPI backend"
  type        = bool
  default     = false
}

variable "container_image" {
  description = "Docker image for the FastAPI backend"
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000
}

variable "ecs_cpu" {
  description = "CPU units for ECS task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "Memory for ECS task in MB (512, 1024, 2048, 4096, 8192)"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of tasks for auto-scaling"
  type        = number
  default     = 10
}

# ============================================================================
# Tags
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
