#!/bin/bash

# Health Check Script for BHP TRA Application
# Usage: ./check-health.sh

set -e

DOMAIN="bhp-tra-poc.duckdns.org"
EC2_IP="3.25.202.107"
SSH_KEY="$HOME/.ssh/bhp-tra-key.pem"

echo "🔍 Checking BHP TRA Application Health..."
echo "=========================================="
echo ""

# Check 1: Frontend HTTPS
echo "1️⃣ Checking Frontend (HTTPS)..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/)
if [ "$FRONTEND_STATUS" == "200" ]; then
    echo "✅ Frontend: OK ($FRONTEND_STATUS)"
else
    echo "❌ Frontend: FAILED ($FRONTEND_STATUS)"
fi
echo ""

# Check 2: Backend API Health
echo "2️⃣ Checking Backend API..."
BACKEND_RESPONSE=$(curl -s https://$DOMAIN/api/health)
if echo "$BACKEND_RESPONSE" | grep -q "healthy"; then
    echo "✅ Backend API: OK"
    echo "   Response: $BACKEND_RESPONSE"
else
    echo "❌ Backend API: FAILED"
    echo "   Response: $BACKEND_RESPONSE"
fi
echo ""

# Check 3: SSL Certificate
echo "3️⃣ Checking SSL Certificate..."
CERT_EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
echo "✅ SSL Certificate expires: $CERT_EXPIRY"
echo ""

# Check 4: EC2 Services (if SSH key exists)
if [ -f "$SSH_KEY" ]; then
    echo "4️⃣ Checking EC2 Services..."

    # Check backend service
    BACKEND_SERVICE=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'sudo systemctl is-active tra-app' 2>/dev/null)
    if [ "$BACKEND_SERVICE" == "active" ]; then
        echo "✅ Backend Service (tra-app): Running"
    else
        echo "❌ Backend Service (tra-app): $BACKEND_SERVICE"
    fi

    # Check nginx
    NGINX_SERVICE=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'sudo systemctl is-active nginx' 2>/dev/null)
    if [ "$NGINX_SERVICE" == "active" ]; then
        echo "✅ Nginx Service: Running"
    else
        echo "❌ Nginx Service: $NGINX_SERVICE"
    fi

    # Check CPU/Memory
    echo ""
    echo "📊 EC2 Resource Usage:"
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'free -h | grep Mem' 2>/dev/null
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'uptime' 2>/dev/null
else
    echo "⚠️  SSH key not found at $SSH_KEY"
    echo "   Skipping EC2 service checks"
fi

echo ""
echo "=========================================="
echo "✅ Health check complete!"
echo ""
echo "URLs:"
echo "  Frontend: https://$DOMAIN/"
echo "  API Health: https://$DOMAIN/api/health"
echo "  GitHub Actions: https://github.com/sampoursoltan11/backendclean/actions"
