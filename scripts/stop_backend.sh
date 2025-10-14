#!/bin/bash

# TRA Backend Stop Script
# Stops the running FastAPI backend server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TRA Backend Stop${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Find uvicorn processes
PIDS=$(ps aux | grep "uvicorn backend.api.main:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}⚠ No backend server is currently running${NC}"
    echo ""
    echo "To start the server, run:"
    echo -e "  ${GREEN}./scripts/run_backend.sh${NC}"
    exit 0
fi

# Count processes
COUNT=$(echo "$PIDS" | wc -l | tr -d ' ')

echo -e "${GREEN}Found ${COUNT} backend process(es) running${NC}"
echo ""

# Kill each process
for PID in $PIDS; do
    echo -n "Stopping process $PID... "
    if kill $PID 2>/dev/null; then
        echo -e "${GREEN}✓ Stopped${NC}"
    else
        echo -e "${RED}✗ Failed (may require sudo)${NC}"
    fi
done

# Wait a moment and verify
sleep 1

# Check if any still running
REMAINING=$(ps aux | grep "uvicorn backend.api.main:app" | grep -v grep | wc -l | tr -d ' ')

echo ""
if [ "$REMAINING" -eq 0 ]; then
    echo -e "${GREEN}✓ All backend processes stopped successfully${NC}"
else
    echo -e "${YELLOW}⚠ Warning: ${REMAINING} process(es) still running${NC}"
    echo ""
    echo "To force stop, run:"
    echo -e "  ${YELLOW}kill -9 \$(ps aux | grep 'uvicorn backend.api.main:app' | grep -v grep | awk '{print \$2}')${NC}"
fi

echo ""
