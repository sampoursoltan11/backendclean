# TRA Backend - Terraform Infrastructure

Complete, production-ready Terraform configuration for deploying the TRA backend infrastructure on AWS.

## 📁 Project Structure

```
terraform/
├── main.tf                          # Main orchestration
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
├── environments/
│   ├── development.tfvars          # Dev environment config
│   └── production.tfvars           # Prod environment config
└── modules/
    ├── dynamodb/                    # DynamoDB with 5 GSI indexes
    ├── s3/                          # S3 document storage
    ├── iam/                         # IAM roles and policies
    ├── cloudwatch/                  # Logging and monitoring
    ├── vpc/                         # VPC (optional)
    └── ecs/                         # ECS cluster (optional)
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or download from: https://www.terraform.io/downloads

# Verify installation
terraform version  # Should be >= 1.0

# Configure AWS credentials
aws configure
# OR export environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="ap-southeast-2"
```

### 2. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### 3. Deploy to Development

```bash
# Preview changes
terraform plan -var-file="environments/development.tfvars"

# Apply changes
terraform apply -var-file="environments/development.tfvars"
```

### 4. Deploy to Production

```bash
# Preview changes
terraform plan -var-file="environments/production.tfvars"

# Apply changes
terraform apply -var-file="environments/production.tfvars"
```

## 📋 What Gets Created

### Core Resources (Always Created):

1. **DynamoDB Table** with 5 optimized GSI indexes
   - `gsi2-session-entity` - Query by session
   - `gsi3-assessment-events` - Query events
   - `gsi4-state-updated` - Query by state
   - `gsi5-title-search` - Search by title
   - `gsi6-entity-type` - List by type
   - Point-in-time recovery enabled
   - Encryption at rest
   - CloudWatch alarms

2. **S3 Bucket** for document storage
   - Versioning enabled
   - Lifecycle rules
   - Encryption at rest
   - CORS configured
   - Public access blocked

3. **IAM Roles** for AWS service access
   - ECS execution role
   - ECS task role
   - Backend service role
   - Policies for DynamoDB, S3, Bedrock

4. **CloudWatch** logging and monitoring
   - Application log group
   - ECS log group (if using ECS)
   - Metrics dashboard

### Optional Resources:

5. **VPC** (if `create_vpc = true`)
   - Public and private subnets
   - NAT Gateway
   - Internet Gateway

6. **ECS Cluster** (if `create_ecs = true`)
   - Fargate task definition
   - Application Load Balancer
   - Auto-scaling configuration

## ⚙️ Configuration

### Environment Variables

Edit `environments/development.tfvars` or `environments/production.tfvars`:

```hcl
environment          = "development"
aws_region          = "ap-southeast-2"
dynamodb_table_name = "tra-system-dev"
s3_bucket_name      = "tra-agent-docs-dev"
log_level           = "DEBUG"
log_retention_days  = 7

# Optional: Enable containerized deployment
create_ecs = false
create_vpc = false
```

### Custom Configuration

Create a custom `.tfvars` file:

```hcl
# custom.tfvars
environment          = "staging"
aws_region          = "us-east-1"
dynamodb_table_name = "tra-system-staging"
s3_bucket_name      = "tra-docs-staging"

# Enable ECS deployment
create_ecs         = true
create_vpc         = true
ecs_desired_count  = 3
ecs_cpu            = 1024
ecs_memory         = 2048
```

Then deploy:
```bash
terraform apply -var-file="custom.tfvars"
```

## 📊 Outputs

After deployment, Terraform outputs important information:

```bash
# View all outputs
terraform output

# View specific output
terraform output dynamodb_table_name
terraform output s3_bucket_name
terraform output backend_url
```

### Key Outputs:

- `dynamodb_table_name` - Table name for app config
- `dynamodb_gsi_names` - List of GSI indexes
- `s3_bucket_name` - Bucket name for app config
- `ecs_execution_role_arn` - IAM role ARN
- `application_config` - All environment variables for your app
- `backend_url` - URL to access API (if ECS enabled)

## 🔧 Update Your Application

After deployment, update your backend configuration:

**Option 1: Environment Variables**

```bash
# Export these in your deployment environment
export DYNAMODB_TABLE_NAME=$(terraform output -raw dynamodb_table_name)
export S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export AWS_REGION="ap-southeast-2"
```

**Option 2: Update `backend/core/config.py`**

```python
class Settings(BaseSettings):
    dynamodb_table_name: str = "tra-system-dev"  # From terraform output
    s3_bucket_name: str = "tra-agent-docs-dev"   # From terraform output
    aws_region: str = "ap-southeast-2"
```

**Option 3: Use Terraform Output JSON**

```bash
# Generate config file
terraform output -json application_config > ../backend/config/aws-config.json
```

## 🌍 Multi-Environment Deployment

### Deploy to Multiple Environments

```bash
# Development
terraform workspace new development
terraform apply -var-file="environments/development.tfvars"

# Staging
terraform workspace new staging
terraform apply -var-file="environments/staging.tfvars"

# Production
terraform workspace new production
terraform apply -var-file="environments/production.tfvars"

# List workspaces
terraform workspace list

# Switch workspace
terraform workspace select development
```

### Deploy to Multiple Regions

```bash
# Sydney (ap-southeast-2)
terraform apply -var="aws_region=ap-southeast-2" \
  -var-file="environments/production.tfvars"

# US East (us-east-1)
terraform apply -var="aws_region=us-east-1" \
  -var-file="environments/production.tfvars"
```

## 🧪 Testing

### Validate Configuration

```bash
# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Check what will be created
terraform plan -var-file="environments/development.tfvars"
```

### Test Connectivity

```bash
# Test DynamoDB access
aws dynamodb describe-table \
  --table-name $(terraform output -raw dynamodb_table_name) \
  --region ap-southeast-2

# Test S3 access
aws s3 ls s3://$(terraform output -raw s3_bucket_name)

# Test IAM role
aws sts assume-role \
  --role-arn $(terraform output -raw backend_service_role_arn) \
  --role-session-name test-session
```

## 🔄 Updates and Changes

### Update Infrastructure

```bash
# Pull latest Terraform code
git pull

# Review changes
terraform plan -var-file="environments/production.tfvars"

# Apply updates
terraform apply -var-file="environments/production.tfvars"
```

### Add a New GSI Index

Edit `modules/dynamodb/main.tf`:

```hcl
global_secondary_index {
  name            = "gsi7-my-new-index"
  hash_key        = "my_field"
  range_key       = "sort_field"
  projection_type = "ALL"
}
```

Then apply:
```bash
terraform apply -var-file="environments/production.tfvars"
```

## 🗑️ Cleanup

### Destroy Development Environment

```bash
terraform destroy -var-file="environments/development.tfvars"
```

### Destroy Production Environment

```bash
# CAREFUL: This deletes everything!
terraform destroy -var-file="environments/production.tfvars"
```

### Destroy Specific Resources

```bash
# Remove only ECS resources
terraform destroy -target=module.ecs -var-file="environments/production.tfvars"
```

## 💰 Cost Estimation

### Development Environment

- **DynamoDB:** ~$0-5/month (on-demand, low usage)
- **S3:** ~$0-2/month (low storage)
- **CloudWatch:** ~$0-1/month (logs)
- **Total:** ~$0-10/month

### Production Environment

- **DynamoDB:** ~$50-200/month (depends on traffic)
- **S3:** ~$5-20/month (depends on storage)
- **CloudWatch:** ~$5-10/month
- **ECS (if enabled):** ~$30-100/month per task
- **Total:** ~$100-500/month

Use AWS Cost Calculator: https://calculator.aws/

## 🔒 Security Best Practices

### Implemented:

- ✅ Encryption at rest (DynamoDB, S3)
- ✅ Encryption in transit (TLS)
- ✅ Least privilege IAM policies
- ✅ S3 public access blocked
- ✅ VPC isolation (if using ECS)
- ✅ CloudWatch logging enabled
- ✅ Deletion protection (production)
- ✅ Point-in-time recovery (DynamoDB)

### Recommended:

1. **Use AWS Secrets Manager for credentials**
2. **Enable CloudTrail for audit logging**
3. **Set up AWS Config for compliance**
4. **Enable GuardDuty for threat detection**
5. **Implement WAF rules (if exposing API)**

## 📚 Additional Resources

### Terraform Modules

- **DynamoDB:** [`modules/dynamodb/`](modules/dynamodb/) - Table with 5 GSI indexes
- **S3:** [`modules/s3/`](modules/s3/) - Document storage bucket
- **IAM:** [`modules/iam/`](modules/iam/) - Roles and policies
- **CloudWatch:** [`modules/cloudwatch/`](modules/cloudwatch/) - Logging
- **VPC:** [`modules/vpc/`](modules/vpc/) - Network configuration
- **ECS:** [`modules/ecs/`](modules/ecs/) - Container orchestration

### Documentation

- [Main Infrastructure README](../README.md)
- [GSI Implementation Guide](../../docs/GSI_IMPLEMENTATION_GUIDE.md)
- [Optimization Summary](../../docs/OPTIMIZATION_SUMMARY.md)

### AWS Documentation

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

## ❓ Troubleshooting

### Common Issues

**Issue:** `Error: AccessDenied`
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions
aws iam get-user
```

**Issue:** `Error: Resource already exists`
```bash
# Import existing resource
terraform import module.dynamodb.aws_dynamodb_table.tra_system tra-system

# Or use different names in tfvars
```

**Issue:** `Error: Invalid count argument`
```bash
# Check conditional resources
terraform plan -var="create_ecs=false" -var-file="environments/development.tfvars"
```

### Get Help

- Check [Terraform documentation](https://www.terraform.io/docs)
- Review [AWS provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- See project issues: `docs/` folder

## 🎯 Next Steps

After deployment:

1. ✅ Verify resources in AWS Console
2. ✅ Update application configuration
3. ✅ Test database connectivity
4. ✅ Deploy application code
5. ✅ Monitor CloudWatch metrics
6. ✅ Set up alerting
7. ✅ Configure backups
8. ✅ Document runbooks

---

**You're all set! Your TRA backend infrastructure is ready!** 🚀
