# 🚀 Quick Start Guide - 5 Minutes to Deploy

## Prerequisites Check

```bash
# 1. Check AWS CLI
aws --version

# 2. Configure AWS (if not done)
aws configure

# 3. Verify credentials
aws sts get-caller-identity
```

## Deploy in 3 Steps

### Step 1: Set Environment Variables (Optional)

```bash
export AWS_REGION=us-east-1
export EB_APP_NAME=bhp-assessment-app
export EB_ENV_NAME=bhp-assessment-env
```

### Step 2: Run Deployment Script

```bash
# From project root directory
./deployment/scripts/deploy.sh
```

### Step 3: Wait & Get URL

The script will:
- ✅ Build everything automatically
- ✅ Deploy to AWS
- ✅ Run tests
- ✅ Give you a secure HTTPS URL

**Expected Time:** 10-15 minutes

## What You Get

```
Application URL:
  https://bhp-assessment-env.us-east-1.elasticbeanstalk.com

✓ HTTPS Enabled
✓ Auto-scaling
✓ Enterprise Security
✓ Health Monitoring
```

## Quick Commands

```bash
# Check health
./deployment/scripts/health_check.sh

# View logs
cd deployment/build && eb logs bhp-assessment-env

# Rollback if needed
./deployment/scripts/rollback.sh

# Open in browser
cd deployment/build && eb open bhp-assessment-env
```

## Need Help?

See full documentation: [README.md](README.md)

## Cost

- **Free Tier:** $0/month for 12 months
- **After:** ~$30-35/month
- **Spot Instances:** Enabled (50-70% savings)

---

**That's it! Your application is now live on AWS with enterprise-grade security! 🎉**
