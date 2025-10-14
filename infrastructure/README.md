# TRA System Infrastructure

This directory contains all Infrastructure as Code (IaC) for the complete TRA system - both backend and frontend.

## 📁 Structure

```
infrastructure/
├── README.md              # This file
├── backend-infra/         # Backend infrastructure (API, DynamoDB, S3)
│   ├── README.md          # Backend deployment guide
│   ├── main.tf            # Backend orchestration
│   ├── variables.tf       # Backend configuration
│   ├── outputs.tf         # Backend outputs
│   ├── environments/      # Backend environment configs
│   │   ├── development.tfvars
│   │   └── production.tfvars
│   └── modules/
│       ├── dynamodb/      # DynamoDB with 5 GSI indexes
│       ├── s3/            # Document storage
│       ├── iam/           # IAM roles and policies
│       ├── cloudwatch/    # Logging and monitoring
│       ├── vpc/           # Optional VPC
│       └── ecs/           # Optional ECS cluster
│
└── frontend-infra/        # Frontend infrastructure (S3, CloudFront, CDN)
    ├── README.md          # Frontend deployment guide
    ├── main.tf            # Frontend orchestration
    ├── variables.tf       # Frontend configuration
    ├── outputs.tf         # Frontend outputs
    ├── environments/      # Frontend environment configs
    │   ├── development.tfvars
    │   └── production.tfvars
    └── modules/
        ├── s3/            # Static website hosting
        ├── cloudfront/    # CDN distribution
        ├── route53/       # DNS configuration
        └── iam/           # Deployment policies
```

## 🚀 Quick Start

### Backend Infrastructure

Deploy the backend API infrastructure (DynamoDB, S3, IAM):

```bash
cd backend-infra
terraform init
terraform plan -var-file="environments/development.tfvars"
terraform apply -var-file="environments/development.tfvars"
```

**See:** [backend-infra/README.md](./backend-infra/README.md) for complete documentation.

### Frontend Infrastructure

Deploy the frontend static website (S3, CloudFront, CDN):

```bash
cd frontend-infra
terraform init
terraform plan -var-file="environments/development.tfvars"
terraform apply -var-file="environments/development.tfvars"
```

**See:** [frontend-infra/README.md](./frontend-infra/README.md) for complete documentation.

## 📦 What's Included

### Backend Infrastructure

- **DynamoDB Table** with 5 optimized GSI indexes (70-90% cost reduction)
- **S3 Bucket** for document storage with versioning and lifecycle policies
- **IAM Roles** with least-privilege access for DynamoDB, S3, and Bedrock
- **CloudWatch** logging and monitoring dashboard
- **Optional VPC** for network isolation
- **Optional ECS** for containerized deployment

### Frontend Infrastructure

- **S3 Bucket** for static website hosting with encryption and versioning
- **CloudFront Distribution** for global CDN with custom caching rules
- **IAM User & Policies** for CI/CD deployment
- **Route53 DNS** (optional) for custom domain support
- **ACM Certificate** (optional) for HTTPS with custom domain

## 🌍 Deployment Workflow

### Complete System Deployment

1. **Deploy Backend Infrastructure:**
   ```bash
   cd backend-infra
   terraform init
   terraform apply -var-file="environments/production.tfvars"
   cd ..
   ```

2. **Deploy Frontend Infrastructure:**
   ```bash
   cd frontend-infra
   terraform init
   terraform apply -var-file="environments/production.tfvars"
   cd ..
   ```

3. **Deploy Backend Application:**
   ```bash
   # Use backend outputs to configure your API
   cd backend-infra
   terraform output
   # Deploy your FastAPI application using these values
   ```

4. **Deploy Frontend Application:**
   ```bash
   # Build and upload frontend
   cd ../../frontend
   npm run build

   # Get bucket name from terraform
   cd ../infrastructure/frontend-infra
   export BUCKET=$(terraform output -raw s3_bucket_name)
   export DIST_ID=$(terraform output -raw cloudfront_distribution_id)

   # Upload files
   aws s3 sync ../../frontend/dist/ s3://$BUCKET/ --delete

   # Invalidate cache
   aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
   ```

## 💰 Cost Estimation

### Development Environment

| Service | Monthly Cost |
|---------|--------------|
| **Backend** |
| DynamoDB | $0-5 (on-demand, low usage) |
| S3 (documents) | $0-2 |
| CloudWatch | $0-1 |
| **Frontend** |
| S3 (static files) | $0.50-1 |
| CloudFront | $1-5 (low traffic) |
| **Total** | **$2-15/month** |

### Production Environment

| Service | Monthly Cost |
|---------|--------------|
| **Backend** |
| DynamoDB | $50-200 (depends on traffic) |
| S3 (documents) | $5-20 |
| CloudWatch | $5-10 |
| ECS (optional) | $30-100 per task |
| **Frontend** |
| S3 (static files) | $2-10 |
| CloudFront | $10-100 (depends on traffic) |
| Route53 (optional) | $0.50 |
| **Total** | **$75-500/month** |

**AWS Free Tier includes:**
- 25GB DynamoDB storage (always free)
- 5GB S3 storage (first 12 months)
- 50GB CloudFront transfer (always free)

## 🔒 Security Best Practices

Both infrastructures implement:

- ✅ Encryption at rest (DynamoDB, S3)
- ✅ Encryption in transit (TLS/HTTPS)
- ✅ Least privilege IAM policies
- ✅ S3 public access blocked
- ✅ CloudWatch logging enabled
- ✅ Point-in-time recovery (DynamoDB)
- ✅ Versioning enabled (S3)

## 📚 Documentation

| Component | Documentation |
|-----------|---------------|
| **Backend Infrastructure** | [backend-infra/README.md](./backend-infra/README.md) |
| **Frontend Infrastructure** | [frontend-infra/README.md](./frontend-infra/README.md) |
| **Backend Application** | [../backend/README.md](../backend/) |
| **Frontend Application** | [../frontend/README.md](../frontend/) |
| **Main Project** | [../README.md](../README.md) |

## 🎯 Environment Support

Both infrastructures support multiple environments:

- **Development** - Minimal resources, debug logging
- **Staging** - Production-like for testing
- **Production** - High availability, optimized settings

Deploy to any environment:
```bash
terraform apply -var-file="environments/{environment}.tfvars"
```

## 🌐 Multi-Region Support

Deploy to any AWS region by setting the `aws_region` variable:

```bash
terraform apply -var="aws_region=us-west-2" -var-file="environments/production.tfvars"
```

**Note:** For frontend, ACM certificates must be in `us-east-1` for CloudFront compatibility.

## 🧪 Testing Infrastructure

### Validate Configuration

```bash
# Backend
cd backend-infra
terraform fmt -recursive
terraform validate
terraform plan -var-file="environments/development.tfvars"

# Frontend
cd ../frontend-infra
terraform fmt -recursive
terraform validate
terraform plan -var-file="environments/development.tfvars"
```

### Test Deployed Resources

```bash
# Test backend
aws dynamodb describe-table --table-name tra-system-dev
aws s3 ls s3://bhp-tra-agent-docs-poc

# Test frontend
aws s3 ls s3://tra-frontend-dev
curl -I https://$(cd frontend-infra && terraform output -raw cloudfront_domain_name)
```

## 🗑️ Cleanup

### Destroy All Infrastructure

```bash
# Destroy frontend first (depends on S3 content)
cd frontend-infra
terraform destroy -var-file="environments/development.tfvars"

# Then destroy backend
cd ../backend-infra
terraform destroy -var-file="environments/development.tfvars"
```

**Warning:** This will delete all data. Make sure you have backups!

## ❓ Troubleshooting

### Common Issues

**Issue:** `Error: AccessDenied`
```bash
# Check AWS credentials
aws sts get-caller-identity
```

**Issue:** `Error: Resource already exists`
```bash
# Import existing resources
terraform import module.dynamodb.aws_dynamodb_table.tra_system tra-system
```

**Issue:** Circular dependency between S3 and CloudFront
```bash
# This has been resolved - bucket policy is created in main.tf after CloudFront
```

### Get Help

- Backend: See [backend-infra/README.md](./backend-infra/README.md#troubleshooting)
- Frontend: See [frontend-infra/README.md](./frontend-infra/README.md#troubleshooting)
- Terraform: https://www.terraform.io/docs
- AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

---

**Last Updated:** October 15, 2025
**Version:** 2.0.0 - Separated Backend & Frontend Infrastructure
**Status:** ✅ Production Ready
