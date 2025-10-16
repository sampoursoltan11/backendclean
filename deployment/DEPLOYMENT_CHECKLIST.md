# 📋 AWS Deployment Checklist

Use this checklist to ensure a smooth deployment process.

## ✅ Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS account created
- [ ] IAM user created with required permissions:
  - [ ] AWSElasticBeanstalkFullAccess
  - [ ] AmazonS3FullAccess
  - [ ] CloudWatchLogsFullAccess
  - [ ] AmazonEC2FullAccess
- [ ] AWS credentials configured locally (`aws configure`)
- [ ] AWS credentials tested (`aws sts get-caller-identity`)

### Software Installation
- [ ] AWS CLI installed (`aws --version`)
- [ ] EB CLI installed (`eb --version`)
- [ ] Node.js installed (`node --version`)
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Git installed (`git --version`)

### Project Preparation
- [ ] Backend code is working locally
- [ ] Frontend code is working locally
- [ ] Backend has `requirements.txt`
- [ ] Frontend has `package.json` and `package-lock.json`
- [ ] All tests passing locally
- [ ] No hardcoded sensitive data in code

### Configuration
- [ ] Review `deployment/config/.env.example`
- [ ] Create `deployment/config/.env` with your values
- [ ] Update application name if needed (EB_APP_NAME)
- [ ] Update environment name if needed (EB_ENV_NAME)
- [ ] Select AWS region (default: us-east-1)

## 🚀 Deployment Checklist

### First Time Deployment
- [ ] Navigate to project root directory
- [ ] Make scripts executable:
  ```bash
  chmod +x deployment/scripts/*.sh
  ```
- [ ] Run deployment script:
  ```bash
  ./deployment/scripts/deploy.sh
  ```
- [ ] Monitor deployment progress (10-15 minutes)
- [ ] Note down the application URL provided
- [ ] Test application in browser

### Post-Deployment Verification
- [ ] Application URL is accessible
- [ ] HTTPS is working (no certificate warnings)
- [ ] Frontend loads correctly
- [ ] Backend API responds correctly
- [ ] Run health checks:
  ```bash
  ./deployment/scripts/health_check.sh
  ```
- [ ] All health checks pass

### Security Verification
- [ ] Test security headers in browser DevTools
- [ ] Verify HTTPS redirect from HTTP
- [ ] Check SSL certificate validity
- [ ] Confirm security score in health check output

## 🔄 CI/CD Setup Checklist

### GitHub Actions (Optional but Recommended)
- [ ] Push code to GitHub repository
- [ ] Add GitHub repository secrets:
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] Verify workflow file exists: `.github/workflows/deploy.yml`
- [ ] Test automated deployment by pushing to main branch
- [ ] Monitor GitHub Actions tab for deployment status

## 🏥 Monitoring Setup Checklist

### Health Monitoring
- [ ] Set up health check cron job (optional):
  ```bash
  # Add to crontab
  */15 * * * * /path/to/deployment/scripts/health_check.sh
  ```
- [ ] Access AWS CloudWatch dashboard
- [ ] Review default metrics (CPU, Memory, Requests)
- [ ] Set up CloudWatch alarms (optional):
  - [ ] High CPU usage (>80%)
  - [ ] High error rate (>5%)
  - [ ] Low request count (application down)

### Log Management
- [ ] Know how to access logs:
  ```bash
  cd deployment/build
  eb logs bhp-assessment-env
  ```
- [ ] Set up log retention policy in CloudWatch
- [ ] Consider log aggregation tool (optional)

## 💰 Cost Management Checklist

### Initial Cost Review
- [ ] Understand free tier limits
- [ ] Review estimated monthly costs (~$30-35 after free tier)
- [ ] Set up AWS billing alerts
- [ ] Enable cost allocation tags

### Optimization
- [ ] Spot instances enabled (automatically by script)
- [ ] Auto-scaling configured (automatically by script)
- [ ] Plan for scaling down during off-hours if needed
- [ ] Review costs monthly

## 🔒 Security Hardening Checklist

### Basic Security (Included)
- [x] HTTPS enforced
- [x] Security headers configured
- [x] HSTS enabled
- [x] Content Security Policy set
- [x] Auto-scaling for DDoS protection

### Additional Security (Optional)
- [ ] Set up AWS WAF (Web Application Firewall)
- [ ] Enable AWS Shield (DDoS protection)
- [ ] Set up VPC flow logs
- [ ] Configure AWS GuardDuty
- [ ] Regular security audits scheduled

## 🎯 Client Handoff Checklist

### Documentation
- [ ] Share application URL with client
- [ ] Provide access credentials (if applicable)
- [ ] Share deployment documentation
- [ ] Create user guide (if needed)

### Training
- [ ] Train client on basic usage
- [ ] Show how to access logs if needed
- [ ] Explain monitoring dashboards
- [ ] Document support contact information

### Ongoing Maintenance
- [ ] Schedule regular health checks
- [ ] Set up automated backups (if using database)
- [ ] Plan for updates and patches
- [ ] Define SLA and uptime expectations

## 🐛 Troubleshooting Checklist

If deployment fails:
- [ ] Check AWS credentials are valid
- [ ] Review deployment logs
- [ ] Verify all prerequisites are met
- [ ] Check AWS service limits
- [ ] Try deployment with verbose logging:
  ```bash
  eb deploy --debug
  ```
- [ ] Review [README.md](README.md) troubleshooting section

If health checks fail:
- [ ] Check application logs: `eb logs bhp-assessment-env`
- [ ] Verify backend `/api/health` endpoint exists
- [ ] Check security group allows HTTP/HTTPS
- [ ] Test locally first
- [ ] Try rollback: `./deployment/scripts/rollback.sh`

## 📞 Emergency Contacts

### AWS Support
- Console: https://console.aws.amazon.com/support/
- Documentation: https://docs.aws.amazon.com/

### Quick Commands for Support
```bash
# Environment status
cd deployment/build && eb status bhp-assessment-env

# Recent logs
cd deployment/build && eb logs bhp-assessment-env

# Deployment history
cd deployment/build && eb history

# SSH access
cd deployment/build && eb ssh bhp-assessment-env
```

---

## ✨ Success Criteria

Your deployment is successful when:
- ✅ Application is accessible via HTTPS URL
- ✅ All health checks pass
- ✅ Security score is 100%
- ✅ No errors in logs
- ✅ Client can access and use the application
- ✅ Monitoring is in place
- ✅ Rollback process is tested and documented

---

**Date Deployed:** _______________

**Deployed By:** _______________

**Application URL:** _______________

**AWS Account ID:** _______________

**Notes:**
_______________________________________________
_______________________________________________
_______________________________________________
