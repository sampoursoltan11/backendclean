#!/bin/bash

##############################################################################
# Rollback Script
# Quickly rollback to previous deployment version
##############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENV_NAME="${EB_ENV_NAME:-bhp-assessment-env}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(dirname "$SCRIPT_DIR")/build"

cd "$BUILD_DIR" 2>/dev/null || {
    echo -e "${RED}Build directory not found. Have you deployed yet?${NC}"
    exit 1
}

echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}    Rollback to Previous Version${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}\n"

# Show deployment history
echo -e "${BLUE}Recent deployments:${NC}"
eb history | head -n 5

echo -e "\n${YELLOW}Current version:${NC}"
eb status "$ENV_NAME" | grep "Deployed Version"

# Get previous version
PREV_VERSION=$(eb history | sed -n '2p' | awk '{print $2}')

if [ -z "$PREV_VERSION" ]; then
    echo -e "${RED}No previous version found to rollback to${NC}"
    exit 1
fi

echo -e "\n${BLUE}Previous version: $PREV_VERSION${NC}"

# Confirm rollback
read -p "Do you want to rollback to version $PREV_VERSION? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Rollback cancelled${NC}"
    exit 0
fi

echo -e "${BLUE}Rolling back...${NC}"
eb deploy --version "$PREV_VERSION"

echo -e "\n${GREEN}✓ Rollback completed!${NC}"
echo -e "Run health checks with: ${BLUE}./deployment/scripts/health_check.sh${NC}"
