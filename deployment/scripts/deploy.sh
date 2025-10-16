#!/bin/bash

##############################################################################
# Complete EC2 Deployment Script for BHP TRA Application
# Automatically creates IAM roles, security groups, and deploys full app
##############################################################################

set -e

# Configuration
REGION="ap-southeast-2"
INSTANCE_TYPE="t3.medium"
AMI_ID="ami-075924b436aa32cd4"  # Amazon Linux 2023 in ap-southeast-2
KEY_NAME="bhp-tra-key"
INSTANCE_NAME="bhp-tra-app"
IAM_ROLE_NAME="BHP-TRA-EC2-Role"
IAM_POLICY_NAME="BHP-TRA-Full-Access-Policy"
SG_NAME="bhp-tra-sg"

# AWS Resources (from config.py)
DYNAMODB_TABLE="tra-system"
S3_BUCKET="bhp-tra-agent-docs-poc"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${GREEN}==>${NC} ${BLUE}BHP TRA Application - EC2 Deployment${NC}"
echo ""
echo "Region: $REGION"
echo "Instance Type: $INSTANCE_TYPE"
echo "DynamoDB Table: $DYNAMODB_TABLE"
echo "S3 Bucket: $S3_BUCKET"
echo ""

##############################################################################
# Step 1: Create IAM Policy with full permissions
##############################################################################

log_info "Creating IAM policy..."

cat > /tmp/tra-iam-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Check if policy exists
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$IAM_POLICY_NAME'].Arn" --output text --region $REGION 2>/dev/null || echo "")

if [ -z "$POLICY_ARN" ]; then
    log_info "Creating new IAM policy..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$IAM_POLICY_NAME" \
        --policy-document file:///tmp/tra-iam-policy.json \
        --region $REGION \
        --query 'Policy.Arn' \
        --output text)
    log_success "IAM policy created: $POLICY_ARN"
else
    log_success "IAM policy already exists: $POLICY_ARN"
fi

##############################################################################
# Step 2: Create IAM Role for EC2
##############################################################################

log_info "Creating IAM role for EC2..."

cat > /tmp/tra-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Check if role exists
if aws iam get-role --role-name "$IAM_ROLE_NAME" --region $REGION &>/dev/null; then
    log_success "IAM role already exists: $IAM_ROLE_NAME"
else
    log_info "Creating new IAM role..."
    aws iam create-role \
        --role-name "$IAM_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/tra-trust-policy.json \
        --region $REGION
    log_success "IAM role created: $IAM_ROLE_NAME"
fi

# Attach policy to role
aws iam attach-role-policy \
    --role-name "$IAM_ROLE_NAME" \
    --policy-arn "$POLICY_ARN" \
    --region $REGION 2>/dev/null || log_warning "Policy already attached"

# Create instance profile if it doesn't exist
if aws iam get-instance-profile --instance-profile-name "$IAM_ROLE_NAME" --region $REGION &>/dev/null; then
    log_success "Instance profile already exists"
else
    log_info "Creating instance profile..."
    aws iam create-instance-profile --instance-profile-name "$IAM_ROLE_NAME" --region $REGION
    aws iam add-role-to-instance-profile --instance-profile-name "$IAM_ROLE_NAME" --role-name "$IAM_ROLE_NAME" --region $REGION
    log_success "Instance profile created"
    # Wait for instance profile to be ready
    sleep 10
fi

##############################################################################
# Step 3: Create Security Group
##############################################################################

log_info "Setting up security group..."

VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --region "$REGION" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    log_info "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Security group for BHP TRA application" \
        --vpc-id "$VPC_ID" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)

    # Add rules
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$REGION"
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 --region "$REGION"
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region "$REGION"

    log_success "Security group created: $SG_ID"
else
    log_success "Security group exists: $SG_ID"
fi

##############################################################################
# Step 4: Create SSH Key Pair
##############################################################################

log_info "Checking SSH key pair..."
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    log_success "Key pair '$KEY_NAME' exists"
else
    log_info "Creating new key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/${KEY_NAME}.pem
    chmod 400 ~/.ssh/${KEY_NAME}.pem
    log_success "Key pair created and saved to ~/.ssh/${KEY_NAME}.pem"
fi

##############################################################################
# Step 5: Build Frontend
##############################################################################

log_info "Preparing frontend..."
cd "$FRONTEND_DIR"
if [ -d "dist" ] && [ -f "dist/enterprise_tra_home_clean.html" ]; then
    log_success "Using existing frontend build"
else
    log_info "Building frontend..."
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    npm run build
    log_success "Frontend built successfully"
fi

##############################################################################
# Step 6: Create Deployment Package
##############################################################################

log_info "Creating deployment package..."
DEPLOY_DIR="/tmp/tra-deploy-$(date +%s)"
mkdir -p "$DEPLOY_DIR/backend"

# Copy backend AS a package
cp -r "$BACKEND_DIR"/* "$DEPLOY_DIR/backend/"

# Copy frontend build into backend/frontend
mkdir -p "$DEPLOY_DIR/backend/frontend/build"
cp -r "$FRONTEND_DIR/dist"/* "$DEPLOY_DIR/backend/frontend/build/"

# Add cache-busting version to main.js import
log_info "Adding cache-busting version parameter..."
VERSION=$(date +%Y%m%d%H%M%S)
sed -i.bak "s|/js/main.js\"|/js/main.js?v=$VERSION\"|g" "$DEPLOY_DIR/backend/frontend/build/enterprise_tra_home_clean.html"
rm -f "$DEPLOY_DIR/backend/frontend/build/enterprise_tra_home_clean.html.bak"
log_success "Cache-busting version added: v=$VERSION"

# Create deployment archive
cd /tmp
tar -czf tra-app.tar.gz -C "$DEPLOY_DIR" .

# Upload to S3
log_info "Uploading deployment package to S3..."
aws s3 cp /tmp/tra-app.tar.gz s3://$S3_BUCKET/deployments/tra-app-latest.tar.gz --region $REGION
log_success "Deployment package uploaded"

##############################################################################
# Step 7: Create User Data Script
##############################################################################

log_info "Creating user data script..."
cat > /tmp/ec2-userdata.sh << USERDATA
#!/bin/bash
set -e

echo "Starting TRA application setup..."

# Update system
yum update -y

# Install Python 3.11
yum install -y python3.11 python3.11-pip git nginx

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Create application directory
mkdir -p /opt/tra-app
cd /opt/tra-app

# Download and extract application
aws s3 cp s3://$S3_BUCKET/deployments/tra-app-latest.tar.gz /tmp/tra-app.tar.gz --region $REGION
tar -xzf /tmp/tra-app.tar.gz -C /opt/tra-app/
rm /tmp/tra-app.tar.gz

# Install Python dependencies
pip3.11 install -r /opt/tra-app/backend/requirements.txt

# Create logs directory
mkdir -p /opt/tra-app/logs

# Configure nginx
cat > /etc/nginx/conf.d/tra-app.conf << 'NGINXCONF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name bhp-tra-poc.duckdns.org;

    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name bhp-tra-poc.duckdns.org;
    client_max_body_size 20M;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/bhp-tra-poc.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bhp-tra-poc.duckdns.org/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend static files
    root /opt/tra-app/backend/frontend/build;
    index enterprise_tra_home_clean.html;

    # Serve frontend - simpler version without try_files loop
    location = / {
        try_files /enterprise_tra_home_clean.html =404;
    }

    # Serve static files
    location / {
        try_files \$uri =404;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Proxy WebSocket connections
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINXCONF

# Start nginx
systemctl enable nginx
systemctl start nginx

# Create systemd service
cat > /etc/systemd/system/tra-app.service << 'SERVICECONF'
[Unit]
Description=BHP TRA Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tra-app
Environment="AWS_REGION=$REGION"
Environment="AWS_DEFAULT_REGION=$REGION"
Environment="DYNAMODB_TABLE_NAME=$DYNAMODB_TABLE"
Environment="S3_BUCKET_NAME=$S3_BUCKET"
Environment="BEDROCK_REGION=$REGION"
Environment="ENVIRONMENT=production"
Environment="PYTHONPATH=/opt/tra-app"
ExecStart=/usr/bin/python3.11 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICECONF

# Start the application
systemctl daemon-reload
systemctl enable tra-app.service
systemctl start tra-app.service

echo "TRA application setup complete!"
USERDATA

##############################################################################
# Step 8: Launch EC2 Instance
##############################################################################

log_info "Launching EC2 instance..."

# Check if instance already exists
EXISTING_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,pending,stopping,stopped" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_INSTANCE" ] && [ "$EXISTING_INSTANCE" != "None" ]; then
    log_warning "Instance already exists: $EXISTING_INSTANCE"
    log_info "Stopping existing instance..."
    aws ec2 terminate-instances --instance-ids "$EXISTING_INSTANCE" --region "$REGION"
    aws ec2 wait instance-terminated --instance-ids "$EXISTING_INSTANCE" --region "$REGION"
    log_success "Old instance terminated"
fi

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --iam-instance-profile Name="$IAM_ROLE_NAME" \
    --user-data file:///tmp/ec2-userdata.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --region "$REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)

log_success "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
log_info "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
log_success "Instance is running"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

PUBLIC_DNS=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicDnsName' \
    --output text)

log_success "Instance details retrieved"

##############################################################################
# Step 9: Wait for Application to Start
##############################################################################

log_info "Waiting for application to initialize (this may take 3-5 minutes)..."
sleep 180

# Test health endpoint
log_info "Testing application health..."
for i in {1..10}; do
    if curl -s -f "http://${PUBLIC_IP}/api/health" &>/dev/null; then
        log_success "Application is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        log_warning "Application health check failed, but instance is running"
        log_info "Check logs with: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP} 'sudo journalctl -u tra-app -n 50'"
    else
        log_info "Attempt $i/10 failed, retrying in 15s..."
        sleep 15
    fi
done

##############################################################################
# Deployment Complete
##############################################################################

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Public DNS: $PUBLIC_DNS"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Application: http://${PUBLIC_IP}"
echo "  Health Check: http://${PUBLIC_IP}/api/health"
echo ""
echo -e "${BLUE}SSH Access:${NC}"
echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP} 'sudo journalctl -u tra-app -f'"
echo "  Restart app: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP} 'sudo systemctl restart tra-app'"
echo "  Check status: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP} 'sudo systemctl status tra-app'"
echo ""
