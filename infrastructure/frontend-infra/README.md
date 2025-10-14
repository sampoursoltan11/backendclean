# TRA Frontend - Terraform Infrastructure

Complete, production-ready Terraform configuration for deploying the TRA frontend infrastructure on AWS.

## 📁 Project Structure

```
frontend-infra/
├── main.tf                          # Main orchestration
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
├── environments/
│   ├── development.tfvars          # Dev environment config
│   └── production.tfvars           # Prod environment config
└── modules/
    ├── s3/                          # S3 static website hosting
    ├── cloudfront/                  # CloudFront CDN distribution
    ├── route53/                     # DNS configuration (optional)
    └── iam/                         # Deployment IAM policies
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
cd infrastructure/frontend-infra
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

1. **S3 Bucket** for static website hosting
   - Versioning enabled
   - Encryption at rest (AES256)
   - CORS configuration
   - Lifecycle rules (delete old versions after 90 days)
   - Public access blocked (CloudFront access only)

2. **CloudFront Distribution** for global CDN
   - Origin Access Control (OAC) for secure S3 access
   - HTTPS redirect
   - Custom caching policies:
     - HTML: 1 hour default TTL
     - Static assets (/assets/*): 24 hours default TTL
     - API calls (/api/*): No caching
   - Custom error responses (404 → index.html)
   - Compression enabled
   - IPv6 support

3. **IAM User & Policies** for deployment
   - S3 upload permissions
   - CloudFront cache invalidation
   - Least-privilege access

### Optional Resources:

4. **Route53 DNS** (if `create_route53 = true`)
   - A record pointing to CloudFront
   - AAAA record for IPv6
   - Optional www subdomain

5. **ACM Certificate** (if `create_certificate = true`)
   - SSL/TLS certificate for custom domain
   - Automatic renewal

## ⚙️ Configuration

### Environment Variables

Edit `environments/development.tfvars` or `environments/production.tfvars`:

```hcl
environment = "development"
aws_region  = "ap-southeast-2"

# S3 Configuration
s3_bucket_name = "tra-frontend-dev"

# CloudFront Configuration
cloudfront_price_class = "PriceClass_100"  # US, Canada, Europe, Asia

# Domain Configuration (optional)
domain_name         = ""  # e.g., "tra.yourcompany.com"
create_certificate  = false
certificate_arn     = ""

# Route53 Configuration (optional)
create_route53  = false
hosted_zone_id  = ""
```

### Custom Configuration

Create a custom `.tfvars` file:

```hcl
# custom.tfvars
environment = "staging"
aws_region  = "us-east-1"
s3_bucket_name = "tra-frontend-staging"

# Enable custom domain
domain_name         = "staging.tra.yourcompany.com"
create_route53      = true
hosted_zone_id      = "Z1234567890ABC"
certificate_arn     = "arn:aws:acm:us-east-1:123456789:certificate/xxx"
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
terraform output cloudfront_url
terraform output s3_bucket_name
```

### Key Outputs:

- `frontend_url` - Primary URL to access your frontend
- `cloudfront_url` - CloudFront distribution URL
- `cloudfront_distribution_id` - For cache invalidation
- `s3_bucket_name` - Bucket name for deployment
- `deployment_instructions` - Step-by-step deployment guide

## 🚀 Deploying Your Frontend

### Step 1: Build Your Frontend

```bash
cd frontend
npm run build
```

This creates a `dist/` directory with your production-ready files.

### Step 2: Upload to S3

```bash
# Get bucket name from Terraform
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)

# Sync files to S3
aws s3 sync frontend/dist/ s3://$BUCKET_NAME/ --delete
```

### Step 3: Invalidate CloudFront Cache

```bash
# Get distribution ID from Terraform
export DIST_ID=$(terraform output -raw cloudfront_distribution_id)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

### Step 4: Access Your Frontend

```bash
# Get the URL
terraform output frontend_url
```

### Automated Deployment Script

Create `deploy-frontend.sh`:

```bash
#!/bin/bash
set -e

echo "Building frontend..."
cd frontend && npm run build && cd ..

echo "Getting Terraform outputs..."
BUCKET=$(cd infrastructure/frontend-infra && terraform output -raw s3_bucket_name)
DIST_ID=$(cd infrastructure/frontend-infra && terraform output -raw cloudfront_distribution_id)

echo "Uploading to S3: $BUCKET"
aws s3 sync frontend/dist/ s3://$BUCKET/ --delete

echo "Invalidating CloudFront cache: $DIST_ID"
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"

echo "Deployment complete!"
cd infrastructure/frontend-infra && terraform output frontend_url
```

Make it executable:
```bash
chmod +x deploy-frontend.sh
./deploy-frontend.sh
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
# Test S3 bucket
aws s3 ls s3://$(terraform output -raw s3_bucket_name)

# Test CloudFront distribution
curl -I $(terraform output -raw cloudfront_url)

# Test custom domain (if configured)
curl -I $(terraform output -raw frontend_url)
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

### Update Frontend Content

Just run the deployment script:
```bash
./deploy-frontend.sh
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

## 💰 Cost Estimation

### Development Environment

- **S3:** ~$0.50-1/month (low storage + requests)
- **CloudFront:** ~$1-5/month (low traffic, PriceClass_100)
- **Route53:** ~$0.50/month (if using custom domain)
- **Total:** ~$2-7/month

### Production Environment

- **S3:** ~$2-10/month (depends on storage + requests)
- **CloudFront:** ~$10-100/month (depends on traffic, PriceClass_All)
- **Route53:** ~$0.50/month (if using custom domain)
- **Total:** ~$15-150/month

**Note:** AWS Free Tier includes:
- 5GB S3 storage (first 12 months)
- 50GB CloudFront data transfer (always free)
- Route53 hosted zone not included in free tier

Use AWS Cost Calculator: https://calculator.aws/

## 🔒 Security Best Practices

### Implemented:

- ✅ S3 bucket encryption at rest (AES256)
- ✅ CloudFront enforces HTTPS
- ✅ S3 public access blocked
- ✅ CloudFront Origin Access Control (OAC)
- ✅ Least privilege IAM policies
- ✅ S3 versioning enabled
- ✅ Compression enabled (reduces bandwidth)

### Recommended:

1. **Enable CloudFront logging** for audit trail
2. **Set up AWS WAF** for web application firewall
3. **Enable CloudTrail** for API audit logging
4. **Use AWS Secrets Manager** for deployment credentials
5. **Implement CSP headers** via Lambda@Edge
6. **Set up CloudWatch alarms** for monitoring

## 🎯 Custom Domain Setup

### Prerequisites

1. Domain registered (via Route53 or external registrar)
2. Route53 hosted zone created
3. ACM certificate in **us-east-1** (required for CloudFront)

### Step 1: Request ACM Certificate

```bash
aws acm request-certificate \
  --domain-name tra.yourcompany.com \
  --validation-method DNS \
  --region us-east-1
```

### Step 2: Validate Certificate

Follow the DNS validation instructions or email validation.

### Step 3: Update Terraform Configuration

Edit `environments/production.tfvars`:

```hcl
domain_name         = "tra.yourcompany.com"
create_route53      = true
hosted_zone_id      = "Z1234567890ABC"  # Your Route53 zone ID
certificate_arn     = "arn:aws:acm:us-east-1:123456789:certificate/xxx"
```

### Step 4: Apply Configuration

```bash
terraform apply -var-file="environments/production.tfvars"
```

DNS propagation can take 5-60 minutes.

## 📚 Additional Resources

### Terraform Modules

- **S3:** [`modules/s3/`](modules/s3/) - Static website hosting bucket
- **CloudFront:** [`modules/cloudfront/`](modules/cloudfront/) - CDN distribution
- **Route53:** [`modules/route53/`](modules/route53/) - DNS configuration
- **IAM:** [`modules/iam/`](modules/iam/) - Deployment permissions

### Documentation

- [Backend Infrastructure](../backend-infra/README.md)
- [Frontend README](../../frontend/README.md)
- [Main Project README](../../README.md)

### AWS Documentation

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/best-practices.html)

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
terraform import module.s3.aws_s3_bucket.frontend tra-frontend-dev

# Or use different names in tfvars
```

**Issue:** CloudFront changes take long time
```bash
# CloudFront updates can take 15-20 minutes
# Monitor progress:
aws cloudfront get-distribution --id DIST_ID
```

**Issue:** Certificate not working
```bash
# Verify certificate is in us-east-1
aws acm list-certificates --region us-east-1

# Check certificate status
aws acm describe-certificate --certificate-arn ARN --region us-east-1
```

**Issue:** 403 Forbidden after deployment
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket BUCKET_NAME

# Verify OAC is configured
aws cloudfront get-distribution-config --id DIST_ID | grep OriginAccessControl
```

### Get Help

- Check [Terraform documentation](https://www.terraform.io/docs)
- Review [AWS provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- See project issues: `docs/` folder

## 🎯 Next Steps

After deployment:

1. ✅ Verify resources in AWS Console
2. ✅ Test CloudFront URL
3. ✅ Deploy frontend files
4. ✅ Test custom domain (if configured)
5. ✅ Set up CI/CD pipeline
6. ✅ Monitor CloudWatch metrics
7. ✅ Configure CloudFront alarms
8. ✅ Document runbooks

## 🔗 CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Build frontend
        run: cd frontend && npm run build

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-2

      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://${{ secrets.S3_BUCKET_NAME }}/ --delete

      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DIST_ID }} \
            --paths "/*"
```

---

**You're all set! Your TRA frontend infrastructure is ready!** 🚀
