# ============================================================================
# TRA Backend Infrastructure - Main Configuration
# ============================================================================
# This is the main entry point for Terraform infrastructure deployment
# It orchestrates all resources needed for the TRA backend system

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state (recommended for team environments)
  # backend "s3" {
  #   bucket         = "tra-terraform-state"
  #   key            = "tra-backend/terraform.tfstate"
  #   region         = "ap-southeast-2"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TRA-System"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "backendclean"
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# Modules
# ============================================================================

# DynamoDB Table with optimized GSI indexes
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name  = var.dynamodb_table_name
  environment = var.environment
}

# S3 Bucket for document storage
module "s3" {
  source = "./modules/s3"

  bucket_name = var.s3_bucket_name
  environment = var.environment
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"

  environment         = var.environment
  dynamodb_table_arn  = module.dynamodb.table_arn
  s3_bucket_arn       = module.s3.bucket_arn
  bedrock_region      = var.aws_region
}

# CloudWatch Logging
module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment = var.environment
  log_retention_days = var.log_retention_days
}

# VPC for ECS (optional - for containerized deployment)
module "vpc" {
  source = "./modules/vpc"
  count  = var.create_vpc ? 1 : 0

  environment = var.environment
  vpc_cidr    = var.vpc_cidr
}

# ECS Cluster for FastAPI backend (optional)
module "ecs" {
  source = "./modules/ecs"
  count  = var.create_ecs ? 1 : 0

  environment         = var.environment
  cluster_name        = "${var.project_name}-${var.environment}"
  vpc_id              = var.create_vpc ? module.vpc[0].vpc_id : var.existing_vpc_id
  private_subnet_ids  = var.create_vpc ? module.vpc[0].private_subnet_ids : var.existing_private_subnet_ids
  public_subnet_ids   = var.create_vpc ? module.vpc[0].public_subnet_ids : var.existing_public_subnet_ids
  execution_role_arn  = module.iam.ecs_execution_role_arn
  task_role_arn       = module.iam.ecs_task_role_arn

  # Container configuration
  container_image     = var.container_image
  container_port      = var.container_port
  cpu                 = var.ecs_cpu
  memory              = var.ecs_memory
  desired_count       = var.ecs_desired_count

  # Environment variables for container
  environment_variables = {
    DYNAMODB_TABLE_NAME        = module.dynamodb.table_name
    AWS_REGION                 = var.aws_region
    S3_BUCKET_NAME            = module.s3.bucket_name
    BEDROCK_MODEL_ID          = var.bedrock_model_id
    BEDROCK_REGION            = var.aws_region
    LOG_LEVEL                 = var.log_level
  }
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}
