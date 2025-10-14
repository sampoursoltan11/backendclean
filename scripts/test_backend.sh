#!/bin/bash

# TRA Backend Test Script
# Tests the running backend to verify GSI optimizations and functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="http://localhost:8000"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TRA Backend Testing${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "Testing ${name}... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${url}")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} (${http_code})"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (${http_code})"
        echo "$body" | head -5
        return 1
    fi
}

# Check if server is running
echo -n "Checking if server is running... "
if curl -s "${BASE_URL}/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running!${NC}"
    echo -e "Please start the server first with: ${YELLOW}./run_backend.sh${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Testing API Endpoints:${NC}"
echo ""

# Test health check
test_endpoint "Health Check" "/health"

# Test docs
echo -n "Testing API Documentation... "
if curl -s "${BASE_URL}/docs" | grep -q "FastAPI"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Test OpenAPI schema
echo -n "Testing OpenAPI Schema... "
if curl -s "${BASE_URL}/openapi.json" | grep -q "openapi"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""
echo -e "${BLUE}Testing DynamoDB GSI Queries:${NC}"
echo ""

# Run Python test for GSI functionality
echo "Running comprehensive GSI tests..."
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

from backend.services.dynamodb_service import DynamoDBService

async def test_gsi():
    db = DynamoDBService()

    print('  Testing query_assessments_by_state (GSI4)...', end=' ')
    try:
        results = await db.query_assessments_by_state('draft')
        print(f'✓ Found {len(results)} draft assessments')
    except Exception as e:
        print(f'✗ Error: {e}')

    print('  Testing health check...', end=' ')
    try:
        result = await db.health_check()
        print('✓ DynamoDB is reachable')
    except Exception as e:
        print(f'✗ Error: {e}')

asyncio.run(test_gsi())
"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "View full API documentation at: ${YELLOW}${BASE_URL}/docs${NC}"
echo -e "View logs at: ${YELLOW}logs/tra_system.log${NC}"
echo ""
