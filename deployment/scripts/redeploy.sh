#!/bin/bash

##############################################################################
# Quick Redeploy Script - Updates code on existing EC2 instance
##############################################################################

set -e

# Configuration
REGION="ap-southeast-2"
S3_BUCKET="bhp-tra-agent-docs-poc"
EC2_IP="3.25.202.107"
KEY_FILE="~/.ssh/bhp-tra-key.pem"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

echo -e "${GREEN}==>${NC} ${BLUE}Quick Redeploy to EC2${NC}"
echo ""

# Build frontend if needed
log_info "Checking frontend build..."
cd "$FRONTEND_DIR"
if [ -d "dist" ] && [ -f "dist/enterprise_tra_home_clean.html" ]; then
    log_success "Using existing frontend build"
else
    log_info "Building frontend..."
    npm install
    npm run build
    log_success "Frontend built"
fi

# Create deployment package
log_info "Creating deployment package..."
DEPLOY_DIR="/tmp/tra-deploy-$(date +%s)"
mkdir -p "$DEPLOY_DIR/backend"

# Copy backend AS a package
cp -r "$BACKEND_DIR"/* "$DEPLOY_DIR/backend/"

# Copy frontend build
mkdir -p "$DEPLOY_DIR/backend/frontend/build"
cp -r "$FRONTEND_DIR/dist"/* "$DEPLOY_DIR/backend/frontend/build/"

# Create archive
cd /tmp
tar -czf tra-app.tar.gz -C "$DEPLOY_DIR" .
log_success "Package created"

# Upload to S3
log_info "Uploading to S3..."
aws s3 cp /tmp/tra-app.tar.gz s3://$S3_BUCKET/deployments/tra-app-latest.tar.gz --region $REGION
log_success "Uploaded to S3"

# Deploy to EC2
log_info "Deploying to EC2..."
ssh -i ~/.ssh/bhp-tra-key.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP << 'ENDSSH'
set -e

# Stop the service
sudo systemctl stop tra-app

# Backup old version
sudo rm -rf /opt/tra-app-backup
sudo mv /opt/tra-app /opt/tra-app-backup || true

# Download and extract new version
sudo mkdir -p /opt/tra-app
cd /opt/tra-app
aws s3 cp s3://bhp-tra-agent-docs-poc/deployments/tra-app-latest.tar.gz /tmp/tra-app.tar.gz --region ap-southeast-2
sudo tar -xzf /tmp/tra-app.tar.gz -C /opt/tra-app/
rm /tmp/tra-app.tar.gz

# Create logs directory
sudo mkdir -p /opt/tra-app/logs

# Update systemd service
sudo tee /etc/systemd/system/tra-app.service > /dev/null << 'SERVICECONF'
[Unit]
Description=BHP TRA Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tra-app
Environment="AWS_REGION=ap-southeast-2"
Environment="AWS_DEFAULT_REGION=ap-southeast-2"
Environment="DYNAMODB_TABLE_NAME=tra-system"
Environment="S3_BUCKET_NAME=bhp-tra-agent-docs-poc"
Environment="BEDROCK_REGION=ap-southeast-2"
Environment="ENVIRONMENT=production"
Environment="PYTHONPATH=/opt/tra-app"
ExecStart=/usr/bin/python3.11 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICECONF

# Reload and start
sudo systemctl daemon-reload
sudo systemctl start tra-app
sudo systemctl enable tra-app

echo "Deployment complete!"
ENDSSH

log_success "Deployed to EC2!"

# Wait and test
log_info "Waiting for application to start..."
sleep 15

log_info "Testing health endpoint..."
for i in {1..5}; do
    if curl -s -f "http://$EC2_IP/api/health" &>/dev/null; then
        log_success "Application is healthy!"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}   Deployment Successful!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Application URL: http://$EC2_IP"
        echo "Health Check: http://$EC2_IP/api/health"
        echo ""
        exit 0
    fi
    log_info "Attempt $i/5 failed, retrying in 10s..."
    sleep 10
done

echo ""
echo "Health check failed. Check logs with:"
echo "  ssh -i ~/.ssh/bhp-tra-key.pem ec2-user@$EC2_IP 'sudo journalctl -u tra-app -n 50'"
echo ""
