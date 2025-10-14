#!/bin/bash

# TRA Backend Startup Script
# This script starts the FastAPI backend server with proper configuration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TRA Backend Startup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if in correct directory
if [ ! -f "backend/api/main.py" ]; then
    echo -e "${RED}Error: backend/api/main.py not found!${NC}"
    echo -e "${RED}Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check Python
echo -e "${GREEN}✓${NC} Checking Python..."
python3 --version

# Check AWS credentials
echo -e "${GREEN}✓${NC} Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text | awk -F'/' '{print $NF}')
    echo -e "  Account: ${YELLOW}${AWS_ACCOUNT}${NC}"
    echo -e "  User: ${YELLOW}${AWS_USER}${NC}"
else
    echo -e "${RED}✗ AWS credentials not configured!${NC}"
    echo -e "  Please run: aws configure"
    exit 1
fi

# Check DynamoDB table
echo -e "${GREEN}✓${NC} Checking DynamoDB table..."
if aws dynamodb describe-table --table-name tra-system --region ap-southeast-2 > /dev/null 2>&1; then
    echo -e "  Table: ${YELLOW}tra-system${NC} (ACTIVE)"
else
    echo -e "${YELLOW}⚠ Warning: DynamoDB table 'tra-system' not found${NC}"
    echo -e "  The server will start but database operations may fail"
fi

# Check S3 bucket
echo -e "${GREEN}✓${NC} Checking S3 bucket..."
if aws s3 ls s3://bhp-tra-agent-docs-poc --region ap-southeast-2 > /dev/null 2>&1; then
    echo -e "  Bucket: ${YELLOW}bhp-tra-agent-docs-poc${NC} (accessible)"
else
    echo -e "${YELLOW}⚠ Warning: S3 bucket 'bhp-tra-agent-docs-poc' not accessible${NC}"
    echo -e "  The server will start but file uploads may fail"
fi

# Create required directories
echo -e "${GREEN}✓${NC} Creating required directories..."
mkdir -p logs
mkdir -p sessions
mkdir -p backend/local_kb
mkdir -p backend/local_s3

# Configuration summary
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Region: ${YELLOW}ap-southeast-2${NC}"
echo -e "  DynamoDB Table: ${YELLOW}tra-system${NC}"
echo -e "  S3 Bucket: ${YELLOW}bhp-tra-agent-docs-poc${NC}"
echo -e "  Bedrock Model: ${YELLOW}anthropic.claude-3-haiku-20240307-v1:0${NC}"
echo ""

# Start server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo -e "  URL: ${YELLOW}http://localhost:8000${NC}"
echo -e "  Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Logs: ${YELLOW}logs/tra_system.log${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# Run uvicorn
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
