# BHP TRA Application - AWS EC2 Deployment Summary

## 🎉 Deployment Complete!

Your full BHP TRA application is now live on AWS EC2!

---

## 📍 Application URLs

### **Primary Application URL**
```
http://3.25.202.107
```
**USE THIS URL** - This is your main application URL for the frontend.

### API Endpoints
- Health Check: `http://3.25.202.107/api/health`
- System Status: `http://3.25.202.107/api/system/status`
- WebSocket (Enterprise): `ws://3.25.202.107/ws/enterprise/{session_id}`

---

## ✅ What's Deployed

### Backend (Full Application)
- ✅ FastAPI with all endpoints
- ✅ WebSocket support for real-time communication
- ✅ **Strands AI Agent Framework** (orchestrator + 4 specialized agents)
- ✅ S3 integration (bucket: `bhp-tra-agent-docs-poc`)
- ✅ DynamoDB integration (table: `tra-system`)
- ✅ AWS Bedrock integration (Claude models)
- ✅ Document processing (PDF, DOCX, TXT)
- ✅ All backend services and tools

### Frontend
- ✅ Complete React/Alpine.js UI
- ✅ Served at root URL: http://3.25.202.107
- ✅ All assets (CSS, JS) properly loaded
- ✅ WebSocket client for real-time updates

### Infrastructure
- **EC2 Instance**: i-099f9124e0d750f78
- **Type**: t3.medium
- **Region**: ap-southeast-2 (Sydney, Australia)
- **IP Address**: 3.25.202.107
- **OS**: Amazon Linux 2023
- **Python**: 3.11
- **Web Server**: Nginx (reverse proxy)
- **Service Manager**: SystemD (auto-restart enabled)

### Security & Permissions
- **IAM Role**: BHP-TRA-EC2-Role
- **Permissions**: Full access to S3, DynamoDB, Bedrock
- **Security Groups**:
  - Port 22 (SSH) - for management
  - Port 80 (HTTP) - for web traffic
  - Port 8000 (Direct app) - for debugging

---

## 🚀 Deployment Options

### Option 1: Manual Deployment (From Your Machine)

```bash
cd deployment
./scripts/redeploy.sh
```

This script will:
1. Build frontend
2. Package everything
3. Upload to S3
4. Deploy to EC2
5. Restart application
6. Run health checks

### Option 2: GitHub Actions (Automatic CI/CD)

**Setup (One-time)**:

1. Go to your GitHub repository → Settings → Secrets and Variables → Actions

2. Add these secrets:
   - `EC2_SSH_PRIVATE_KEY`: Content of `~/.ssh/bhp-tra-key.pem`
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

3. Push code to main/master branch

**Usage**:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

GitHub Actions will automatically deploy your changes!

**Manual trigger**: Go to GitHub Actions tab → "Deploy to EC2" → "Run workflow"

---

## 🔧 Management Commands

### SSH Access
```bash
ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107
```

### View Application Logs
```bash
ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo journalctl -u tra-app -f'
```

### Restart Application
```bash
ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo systemctl restart tra-app'
```

### Check Application Status
```bash
ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo systemctl status tra-app'
```

### View Nginx Logs
```bash
ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo tail -f /var/log/nginx/error.log'
```

---

## 📦 Files & Structure

### Deployment Scripts
- `deployment/scripts/deploy.sh` - Complete deployment (creates new EC2)
- `deployment/scripts/redeploy.sh` - Quick update (updates existing EC2)

### GitHub Actions
- `.github/workflows/deploy-ec2.yml` - CI/CD workflow
- `.github/workflows/README.md` - Setup instructions

### Requirements
- `backend/requirements.txt` - **Updated with all dependencies including Strands**

---

## 🔌 AWS Resources Connected

| Resource | Name/ID | Region |
|----------|---------|--------|
| DynamoDB Table | `tra-system` | ap-southeast-2 |
| S3 Bucket | `bhp-tra-agent-docs-poc` | ap-southeast-2 |
| Bedrock | Claude Models | ap-southeast-2 |
| EC2 Instance | i-099f9124e0d750f78 | ap-southeast-2 |
| IAM Role | BHP-TRA-EC2-Role | Global |
| Security Group | sg-0f6f4a8a88f384fa9 | ap-southeast-2 |

---

## ⚠️ Important Notes

### 1. Requirements.txt is Already Updated
The `backend/requirements.txt` file **already includes** all necessary packages:
- Strands AI framework (`strands-agents`, `strands-agents-tools`)
- FastAPI and uvicorn
- AWS SDKs (boto3, aioboto3)
- Document processing libraries
- All other dependencies

**No action needed** - the requirements file is complete!

### 2. HTTP vs HTTPS
The current deployment uses **HTTP** (not HTTPS). This is fine for:
- Internal testing
- Development
- Demo purposes

For production with HTTPS, you would need:
- A domain name
- SSL certificate (from AWS Certificate Manager)
- Update load balancer configuration

### 3. Cost Considerations
Current AWS resources running:
- EC2 t3.medium instance (~$0.042/hour in Sydney region)
- S3 storage (minimal cost)
- DynamoDB on-demand (pay per request)
- Bedrock (pay per API call)

Estimated monthly cost: ~$30-50 depending on usage

### 4. Stopping/Starting EC2

**To stop EC2 (save costs when not using)**:
```bash
aws ec2 stop-instances --instance-ids i-099f9124e0d750f78 --region ap-southeast-2
```

**To start EC2 again**:
```bash
aws ec2 start-instances --instance-ids i-099f9124e0d750f78 --region ap-southeast-2
```

Note: IP address may change after stop/start. Update deployment scripts if needed.

---

## 🧪 Testing Your Deployment

### Test Backend Health
```bash
curl http://3.25.202.107/api/health
```

Expected response:
```json
{
    "status": "healthy",
    "service": "TRA System API",
    "version": "2.0.0",
    "timestamp": "2025-10-16T07:39:12.853814"
}
```

### Test Frontend
Open in your browser:
```
http://3.25.202.107
```

You should see the TRA application interface.

### Test WebSocket (Enterprise Agent)
Use a WebSocket client or your frontend to connect to:
```
ws://3.25.202.107/ws/enterprise/{session_id}
```

---

## 🆘 Troubleshooting

### Application Not Responding

1. **Check if EC2 is running**:
   ```bash
   aws ec2 describe-instances --instance-ids i-099f9124e0d750f78 --region ap-southeast-2 --query 'Reservations[0].Instances[0].State.Name'
   ```

2. **Check application logs**:
   ```bash
   ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo journalctl -u tra-app -n 100'
   ```

3. **Restart application**:
   ```bash
   ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107 'sudo systemctl restart tra-app'
   ```

### Deployment Fails

1. Check your AWS credentials are configured
2. Check S3 bucket is accessible
3. Check EC2 instance is running
4. Review deployment script logs

### GitHub Actions Fails

1. Verify all secrets are correctly added in GitHub
2. Check the Actions logs for specific errors
3. Ensure your SSH key has correct permissions

---

## 📚 Additional Resources

- AWS EC2 Console: https://console.aws.amazon.com/ec2
- GitHub Actions Documentation: https://docs.github.com/en/actions
- FastAPI Documentation: https://fastapi.tiangolo.com
- Strands AI Framework: https://github.com/anthropics/anthropic-sdk-python

---

## 🎯 Next Steps

1. **Test the application**: Visit http://3.25.202.107
2. **Set up GitHub Actions**: Add secrets to enable CI/CD
3. **Make changes**: Update code and push to deploy
4. **Monitor**: Use CloudWatch or application logs
5. **(Optional) Set up custom domain**: Configure Route53 and add SSL

---

## 📞 Support

If you encounter issues:
1. Check application logs on EC2
2. Review AWS CloudWatch logs
3. Check GitHub Actions workflow logs
4. Verify all AWS resources are accessible

---

**Deployment Date**: October 16, 2025
**Deployment Region**: ap-southeast-2 (Sydney)
**Application Version**: 2.0.0
**Status**: ✅ **LIVE AND RUNNING**

---

## 🎉 Summary

Your **complete BHP TRA application with full AI agent framework** is now:
- ✅ Deployed on AWS EC2
- ✅ Connected to DynamoDB, S3, and Bedrock
- ✅ Accessible at http://3.25.202.107
- ✅ Ready for CI/CD with GitHub Actions
- ✅ All features working (WebSocket, document upload, AI agents)

**You're all set!** 🚀
