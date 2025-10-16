#!/bin/bash

##############################################################################
# Health Check and Monitoring Script
# Monitors application health and sends alerts if issues are detected
##############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENV_NAME="${EB_ENV_NAME:-bhp-assessment-env}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(dirname "$SCRIPT_DIR")/build"

# Get environment URL
get_url() {
    cd "$BUILD_DIR" 2>/dev/null || cd "$SCRIPT_DIR"
    local url=$(eb status "$ENV_NAME" 2>/dev/null | grep "CNAME:" | awk '{print $2}')
    if [ -z "$url" ]; then
        echo "Unable to get URL"
        exit 1
    fi
    echo "https://$url"
}

# Health check function
check_health() {
    local url="$1"
    local endpoint="$2"
    local expected_status="$3"

    echo -e "${BLUE}Checking: ${NC}$url$endpoint"

    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url$endpoint" 2>/dev/null || echo "000")

    if [ "$response" == "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Performance check
check_performance() {
    local url="$1"
    local endpoint="$2"
    local max_time="$3"

    echo -e "${BLUE}Performance check: ${NC}$url$endpoint (max ${max_time}s)"

    local response_time=$(curl -s -o /dev/null -w "%{time_total}" "$url$endpoint" 2>/dev/null || echo "999")

    if (( $(echo "$response_time < $max_time" | bc -l) )); then
        echo -e "${GREEN}✓ PASS${NC} (${response_time}s)"
        return 0
    else
        echo -e "${YELLOW}⚠ SLOW${NC} (${response_time}s, expected <${max_time}s)"
        return 1
    fi
}

# Security headers check
check_security_headers() {
    local url="$1"

    echo -e "\n${BLUE}Checking security headers...${NC}"

    local headers=$(curl -sI "$url/" 2>/dev/null)

    local checks=(
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
    )

    local passed=0
    local total=${#checks[@]}

    for header in "${checks[@]}"; do
        if echo "$headers" | grep -qi "$header"; then
            echo -e "${GREEN}✓${NC} $header"
            passed=$((passed + 1))
        else
            echo -e "${RED}✗${NC} $header"
        fi
    done

    echo -e "\nSecurity Score: $passed/$total"

    if [ $passed -eq $total ]; then
        return 0
    else
        return 1
    fi
}

# Main monitoring
main() {
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}    Application Health Check${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}\n"

    local url=$(get_url)
    echo -e "Application URL: ${BLUE}$url${NC}\n"

    local total_checks=0
    local passed_checks=0

    # Backend health check
    echo -e "\n${YELLOW}Backend Health Checks:${NC}"
    if check_health "$url" "/api/health" "200"; then
        passed_checks=$((passed_checks + 1))
    fi
    total_checks=$((total_checks + 1))

    # Frontend check
    echo -e "\n${YELLOW}Frontend Checks:${NC}"
    if check_health "$url" "/" "200"; then
        passed_checks=$((passed_checks + 1))
    fi
    total_checks=$((total_checks + 1))

    # Performance checks
    echo -e "\n${YELLOW}Performance Checks:${NC}"
    if check_performance "$url" "/api/health" "2.0"; then
        passed_checks=$((passed_checks + 1))
    fi
    total_checks=$((total_checks + 1))

    # Security headers
    if check_security_headers "$url"; then
        passed_checks=$((passed_checks + 1))
    fi
    total_checks=$((total_checks + 1))

    # SSL/TLS check
    echo -e "\n${YELLOW}SSL/TLS Check:${NC}"
    if echo | openssl s_client -connect "${url#https://}:443" -servername "${url#https://}" 2>/dev/null | grep -q "Verify return code: 0"; then
        echo -e "${GREEN}✓ Valid SSL Certificate${NC}"
        passed_checks=$((passed_checks + 1))
    else
        echo -e "${RED}✗ SSL Certificate Issue${NC}"
    fi
    total_checks=$((total_checks + 1))

    # Summary
    echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}    Summary${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "Total Checks: $total_checks"
    echo -e "Passed: ${GREEN}$passed_checks${NC}"
    echo -e "Failed: ${RED}$((total_checks - passed_checks))${NC}"

    if [ $passed_checks -eq $total_checks ]; then
        echo -e "\n${GREEN}✓ All checks passed!${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}⚠ Some checks failed${NC}"
        exit 1
    fi
}

main "$@"
