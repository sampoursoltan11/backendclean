# GitHub Actions Deployment

This workflow automatically deploys your BHP TRA application to EC2 when you push code to the main/master branch.

## Setup Instructions

### 1. Get Your EC2 SSH Private Key

Your SSH private key is located at:
```bash
~/.ssh/bhp-tra-key.pem
```

Copy its contents:
```bash
cat ~/.ssh/bhp-tra-key.pem
```

### 2. Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add these secrets:

**EC2_SSH_PRIVATE_KEY**:
- The entire contents of `~/.ssh/bhp-tra-key.pem` (including BEGIN and END lines)

**AWS_ACCESS_KEY_ID**:
- Your AWS access key ID (same one you use locally)

**AWS_SECRET_ACCESS_KEY**:
- Your AWS secret access key (same one you use locally)

### 3. Get AWS Credentials

If you don't remember your AWS credentials, you can find them:

```bash
# Check your AWS config
cat ~/.aws/credentials

# Or check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

### 4. How It Works

Once setup is complete:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **Automatic Deployment**: GitHub Actions will:
   - Build the frontend
   - Package backend + frontend
   - Upload to S3
   - Deploy to EC2
   - Restart the application
   - Run health checks

3. **Manual Trigger**: You can also trigger deployment manually:
   - Go to Actions tab in GitHub
   - Select "Deploy to EC2" workflow
   - Click "Run workflow"

### 5. Monitor Deployment

Watch the deployment progress:
- Go to GitHub → Actions tab
- Click on the latest workflow run
- Watch the logs in real-time

### Deployment Status

The workflow will:
- ✅ Show green checkmark if successful
- ❌ Show red X if failed (with error logs)

### Troubleshooting

If deployment fails:

1. **Check GitHub Actions logs** for specific errors
2. **SSH into EC2** to check application logs:
   ```bash
   ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@3.25.202.107
   sudo journalctl -u tra-app -n 100
   ```

3. **Verify secrets** are correctly added in GitHub

### Current Application

- **EC2 IP**: 3.25.202.107
- **Application URL**: http://3.25.202.107
- **Region**: ap-southeast-2 (Sydney)
- **S3 Bucket**: bhp-tra-agent-docs-poc

### Security Note

Never commit your SSH private key or AWS credentials to Git! Always use GitHub Secrets.
