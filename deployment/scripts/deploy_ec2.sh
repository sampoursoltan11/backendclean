#!/bin/bash

##############################################################################
# EC2 Deployment Script for BHP TRA Application
# Deploys full application to EC2 instance in ap-southeast-2
##############################################################################

set -e

# Configuration
REGION="ap-southeast-2"
INSTANCE_TYPE="t3.medium"
AMI_ID="ami-0892a9a01b998eae8"  # Amazon Linux 2023 in ap-southeast-2
KEY_NAME="bhp-tra-key"
INSTANCE_NAME="bhp-tra-app"
IAM_ROLE="aws-elasticbeanstalk-ec2-role"  # Reuse the IAM role we created

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${GREEN}==>${NC} ${BLUE}Starting EC2 Deployment${NC}"
echo ""
echo "Instance: $INSTANCE_NAME"
echo "Region: $REGION"
echo "Type: $INSTANCE_TYPE"
echo ""

# Check if key pair exists, create if not
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

# Create security group if it doesn't exist
log_info "Checking security group..."
SG_NAME="bhp-tra-sg"
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)

if aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --region "$REGION" &>/dev/null; then
    SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --region "$REGION" --query 'SecurityGroups[0].GroupId' --output text)
    log_success "Security group exists: $SG_ID"
else
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
fi

# Create user data script for EC2 initialization
log_info "Creating user data script..."
cat > /tmp/ec2-userdata.sh << 'EOF'
#!/bin/bash
set -e

# Update system
yum update -y

# Install Python 3.11
yum install -y python3.11 python3.11-pip git nginx

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
yum install -y nodejs

# Create application directory
mkdir -p /opt/tra-app
cd /opt/tra-app

# Clone or copy application (we'll use S3 for deployment package)
# For now, create placeholder - will be replaced by actual deployment

# Install Python dependencies globally
cat > /tmp/requirements.txt << 'PYREQ'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiofiles==23.2.1
websockets==12.0
python-multipart==0.0.6
boto3==1.34.0
aioboto3==12.3.0
anthropic==0.39.0
PyPDF2==3.0.1
python-docx==1.1.0
PyYAML==6.0.3
PYREQ

pip3.11 install -r /tmp/requirements.txt

# Configure nginx as reverse proxy
cat > /etc/nginx/conf.d/tra-app.conf << 'NGINXCONF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
NGINXCONF

# Start nginx
systemctl enable nginx
systemctl start nginx

# Create systemd service for the application
cat > /etc/systemd/system/tra-app.service << 'SERVICECONF'
[Unit]
Description=BHP TRA Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tra-app
Environment="AWS_REGION=ap-southeast-2"
Environment="AWS_DEFAULT_REGION=ap-southeast-2"
ExecStart=/usr/bin/python3.11 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICECONF

# Enable but don't start yet (wait for actual code deployment)
systemctl enable tra-app.service

echo "EC2 initialization complete"
EOF

log_success "User data script created"

# Launch EC2 instance
log_info "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --iam-instance-profile Name="$IAM_ROLE" \
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

log_success "Instance ready!"
echo ""
echo -e "${GREEN}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  SSH: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo "  HTTP URL: http://${PUBLIC_IP}"
echo ""
log_info "Waiting 2 minutes for user data script to complete..."
sleep 120

log_success "EC2 deployment complete!"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. SSH into the instance: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo "2. Copy your application code to /opt/tra-app/"
echo "3. Start the application: sudo systemctl start tra-app"
echo "4. Check status: sudo systemctl status tra-app"
echo ""
