# AWS Elastic Beanstalk Deployment Guide

Complete DevOps solution for deploying the BHP Assessment Application to AWS with enterprise-grade security, monitoring, and CI/CD.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Manual Deployment](#manual-deployment)
- [Automated CI/CD](#automated-cicd)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Rollback](#rollback)
- [Troubleshooting](#troubleshooting)
- [Cost Management](#cost-management)

## 🔧 Prerequisites

### Required Software

1. **AWS CLI** (v2 or higher)
   ```bash
   # Install on macOS
   brew install awscli

   # Or download from: https://aws.amazon.com/cli/
   ```

2. **EB CLI** (Elastic Beanstalk CLI)
   ```bash
   pip install awsebcli --upgrade --user
   ```

3. **Node.js** (v18 or higher)
   ```bash
   # Check version
   node --version
   ```

4. **Python** (v3.11 or higher)
   ```bash
   # Check version
   python3 --version
   ```

### AWS Account Setup

1. **Create AWS Account**
   - Visit: https://aws.amazon.com/
   - Sign up for a new account (Free tier available)

2. **Create IAM User for Deployment**
   ```bash
   # Required permissions:
   - AWSElasticBeanstalkFullAccess
   - AmazonS3FullAccess
   - CloudWatchLogsFullAccess
   - AmazonEC2FullAccess (for EB instances)
   ```

3. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter:
   # - AWS Access Key ID
   # - AWS Secret Access Key
   # - Default region (e.g., us-east-1)
   # - Output format: json
   ```

4. **Verify Configuration**
   ```bash
   aws sts get-caller-identity
   # Should display your account information
   ```

## 🚀 Initial Setup

### 1. Environment Configuration

Copy the example environment file and configure:

```bash
cd deployment/config
cp .env.example .env
```

Edit `.env` with your values:
```bash
AWS_REGION=us-east-1
EB_APP_NAME=bhp-assessment-app
EB_ENV_NAME=bhp-assessment-env
```

### 2. Update SSL Certificate (Optional)

If you have a custom SSL certificate from AWS Certificate Manager:

Edit `deployment/.ebextensions/01_flask.config`:
```yaml
SSLCertificateArns: 'arn:aws:acm:REGION:ACCOUNT_ID:certificate/CERT_ID'
```

Or use the default AWS EB certificate (automatically provided).

## 📦 Manual Deployment

### First Time Deployment

Run the comprehensive deployment script:

```bash
# From project root
./deployment/scripts/deploy.sh
```

The script will:
1. ✅ Check all prerequisites
2. ✅ Build React frontend
3. ✅ Prepare Flask backend
4. ✅ Create deployment package
5. ✅ Initialize Elastic Beanstalk
6. ✅ Deploy to AWS
7. ✅ Wait for environment to be ready
8. ✅ Run health checks
9. ✅ Run smoke tests
10. ✅ Display deployment URL

**Expected Time:** 10-15 minutes for first deployment

### Subsequent Deployments

For updates after the initial deployment:

```bash
./deployment/scripts/deploy.sh
```

**Expected Time:** 5-10 minutes

### What You'll Get

After successful deployment:
```
═══════════════════════════════════════════════════════════════
              DEPLOYMENT SUCCESSFUL!
═══════════════════════════════════════════════════════════════

Application URL:
  https://bhp-assessment-env.us-east-1.elasticbeanstalk.com

Security:
  ✓ HTTPS Enabled
  ✓ Security Headers Configured
  ✓ Auto-scaling Enabled
  ✓ Enhanced Health Monitoring
```

## 🔄 Automated CI/CD

### GitHub Actions Setup

The project includes automated deployment via GitHub Actions.

#### 1. Add GitHub Secrets

Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Add the following secrets:

```
AWS_ACCESS_KEY_ID: your_aws_access_key
AWS_SECRET_ACCESS_KEY: your_aws_secret_key
```

#### 2. Enable Workflow

The workflow is located at: `.github/workflows/deploy.yml`

**Automatic Deployment Triggers:**
- ✅ Push to `main` branch
- ✅ Manual trigger via GitHub Actions UI

**What it does:**
1. Runs frontend tests
2. Runs backend tests
3. Builds application
4. Deploys to AWS EB
5. Runs health checks
6. Notifies on success/failure

#### 3. Monitor Deployment

View deployment progress:
- GitHub → Actions tab → Deploy to AWS Elastic Beanstalk

## 🏥 Monitoring & Health Checks

### Run Health Checks

Monitor application health:

```bash
./deployment/scripts/health_check.sh
```

**Checks Performed:**
- ✅ Backend API health
- ✅ Frontend accessibility
- ✅ Response time performance
- ✅ Security headers
- ✅ SSL/TLS certificate validity

**Example Output:**
```
Backend Health Checks:
✓ PASS (HTTP 200)

Frontend Checks:
✓ PASS (HTTP 200)

Performance Checks:
✓ PASS (0.234s)

Security Score: 4/4
✓ All checks passed!
```

### View Application Logs

```bash
cd deployment/build
eb logs bhp-assessment-env --all
```

### Monitor via AWS Console

Access AWS Elastic Beanstalk Console:
```
https://console.aws.amazon.com/elasticbeanstalk/
```

View:
- Environment health
- Request metrics
- Error logs
- CPU/Memory usage

### Set Up CloudWatch Alarms (Optional)

Create alarms for:
- High error rate
- High response time
- CPU > 80%
- Memory > 80%

## ⏮️ Rollback

If deployment fails or issues arise, quickly rollback:

```bash
./deployment/scripts/rollback.sh
```

**Interactive Rollback:**
1. Shows recent deployment history
2. Identifies previous version
3. Confirms rollback
4. Deploys previous version
5. Runs health checks

**Manual Rollback:**
```bash
cd deployment/build
eb deploy --version VERSION_LABEL
```

## 🐛 Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Configured
```
Error: Unable to locate credentials
```

**Solution:**
```bash
aws configure
# Enter your credentials
```

#### 2. EB CLI Not Found
```
Error: eb: command not found
```

**Solution:**
```bash
pip install awsebcli --upgrade --user
# Add to PATH: export PATH=$PATH:~/.local/bin
```

#### 3. Deployment Timeout
```
Error: Environment did not become ready within 600s
```

**Solution:**
- Check AWS console for detailed errors
- View logs: `eb logs bhp-assessment-env`
- Increase timeout in deploy.sh: `MAX_WAIT_TIME=900`

#### 4. Health Checks Failing
```
Error: Health checks failed after 10 attempts
```

**Solution:**
- Check if backend is running: `eb logs bhp-assessment-env | grep error`
- Verify environment variables are set
- Check security group allows HTTP/HTTPS
- Ensure backend has `/api/health` endpoint

#### 5. Build Failures

**Frontend build fails:**
```bash
cd frontend
npm install
npm run build
# Check for errors
```

**Backend issues:**
```bash
cd backend
pip install -r requirements.txt
python app.py
# Check for errors
```

### View Detailed Logs

```bash
# All logs
eb logs bhp-assessment-env --all

# Last 100 lines
eb logs bhp-assessment-env

# Stream live logs
eb logs -f bhp-assessment-env

# Download logs
eb logs --zip bhp-assessment-env
```

### SSH into Instance

For advanced debugging:

```bash
cd deployment/build
eb ssh bhp-assessment-env
```

## 💰 Cost Management

### Estimated Monthly Costs

**Free Tier (First 12 months):**
- ✅ 750 hours/month EC2 t2.micro/t3.micro
- ✅ 5GB S3 storage
- ✅ 1 million HTTP requests via Load Balancer
- **Total: $0/month**

**After Free Tier:**
- EC2 t3.small: ~$15/month
- Load Balancer: ~$16/month
- Data Transfer: ~$1-5/month
- **Total: ~$32-36/month**

### Cost Optimization

#### 1. Use Spot Instances (50-70% savings)
Already enabled in deployment script with `--enable-spot`

#### 2. Auto-scaling
```bash
# Scale down during off-hours
eb scale 1 bhp-assessment-env

# Scale up for peak hours
eb scale 2 bhp-assessment-env
```

#### 3. Terminate When Not Needed
```bash
# Terminate environment (keeps application)
eb terminate bhp-assessment-env

# Redeploy when needed
./deployment/scripts/deploy.sh
```

#### 4. Monitor Costs
- AWS Cost Explorer: https://console.aws.amazon.com/cost-management/
- Set up billing alerts

## 🔒 Security Features

Included in deployment:

✅ **HTTPS Enforcement** - All traffic redirected to HTTPS
✅ **Security Headers** - XSS, CSRF, Clickjacking protection
✅ **HSTS** - HTTP Strict Transport Security enabled
✅ **CSP** - Content Security Policy configured
✅ **Auto-scaling** - Handle traffic spikes
✅ **Enhanced Health Monitoring** - AWS CloudWatch integration
✅ **Isolated Environment** - VPC security groups

## 📞 Support & Resources

### Useful Commands

```bash
# Environment status
eb status bhp-assessment-env

# Open application in browser
eb open bhp-assessment-env

# View deployment history
cd deployment/build && eb history

# Update environment configuration
eb config bhp-assessment-env

# Restart application
eb restart bhp-assessment-env

# Terminate environment
eb terminate bhp-assessment-env
```

### AWS Documentation

- [Elastic Beanstalk Docs](https://docs.aws.amazon.com/elasticbeanstalk/)
- [EB CLI Reference](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html)
- [Python on EB](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)

### Getting Help

1. **Check Logs:** `eb logs bhp-assessment-env --all`
2. **AWS Support:** https://console.aws.amazon.com/support/
3. **Community:** AWS Forums, Stack Overflow

## 🎯 Next Steps

After successful deployment:

1. ✅ **Test Application** - Visit the HTTPS URL
2. ✅ **Set Up Custom Domain** (Optional)
   - Register domain in Route 53
   - Configure DNS records
   - Update EB environment settings

3. ✅ **Configure Backups**
   - Set up RDS backups if using database
   - S3 versioning for important data

4. ✅ **Set Up Monitoring Alerts**
   - CloudWatch alarms
   - SNS notifications

5. ✅ **Performance Testing**
   - Load testing with realistic traffic
   - Optimize based on metrics

6. ✅ **Security Hardening**
   - WAF rules (optional)
   - DDoS protection
   - Regular security audits

---

## 📝 Quick Reference

### Deploy
```bash
./deployment/scripts/deploy.sh
```

### Health Check
```bash
./deployment/scripts/health_check.sh
```

### Rollback
```bash
./deployment/scripts/rollback.sh
```

### View Logs
```bash
cd deployment/build
eb logs bhp-assessment-env
```

---

**🎉 Your application is now enterprise-ready and deployed on AWS with full DevOps automation!**
