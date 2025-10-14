# TRA Backend Infrastructure

This directory contains all Infrastructure as Code (IaC) for the TRA backend system.

## Quick Start

```bash
cd terraform
terraform init
terraform plan -var-file="environments/development.tfvars"
terraform apply -var-file="environments/development.tfvars"
```

## Structure

```
infrastructure/
└── terraform/           # Complete Terraform infrastructure
    ├── README.md        # Detailed deployment guide
    ├── main.tf          # Main orchestration
    ├── variables.tf     # Configuration parameters
    ├── outputs.tf       # Exported values
    ├── environments/    # Environment-specific configs
    │   ├── development.tfvars
    │   └── production.tfvars
    └── modules/         # Reusable infrastructure modules
        ├── dynamodb/    # DynamoDB with 5 GSI indexes
        ├── s3/          # Document storage
        ├── iam/         # IAM roles and policies
        ├── cloudwatch/  # Logging and monitoring
        ├── vpc/         # Optional VPC
        └── ecs/         # Optional ECS cluster
```

## What's Included

- **DynamoDB Table** with 5 optimized GSI indexes (70-90% cost reduction)
- **S3 Bucket** for document storage with versioning and lifecycle policies
- **IAM Roles** with least-privilege access for DynamoDB, S3, and Bedrock
- **CloudWatch** logging and monitoring dashboard
- **Optional VPC** for network isolation
- **Optional ECS** for containerized deployment

## Documentation

For detailed deployment instructions, configuration options, and troubleshooting, see [terraform/README.md](./terraform/README.md).

## Environment Support

- **Development** - Minimal resources, debug logging
- **Production** - High availability, optimized settings

Deploy to any environment:
```bash
terraform apply -var-file="environments/production.tfvars"
```

## Multi-Region Support

Deploy to any AWS region by setting the `aws_region` variable:
```bash
terraform apply -var="aws_region=us-west-2" -var-file="environments/production.tfvars"
```
