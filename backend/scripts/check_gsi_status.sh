#!/bin/bash

# Check status of GSI indexes
# Run this script to monitor the progress of GSI creation

TABLE_NAME="tra-system"
REGION="ap-southeast-2"

echo "========================================"
echo "Checking GSI Status for $TABLE_NAME"
echo "========================================"
echo ""

# Get all GSI statuses
aws dynamodb describe-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus,ItemCount]' \
    --output table

echo ""
echo "Status meanings:"
echo "  CREATING - Index is being built"
echo "  ACTIVE   - Index is ready to use"
echo "  UPDATING - Index is being modified"
echo ""

# Check if all are ACTIVE
ALL_ACTIVE=$(aws dynamodb describe-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --query 'Table.GlobalSecondaryIndexes[?IndexStatus!=`ACTIVE`]' \
    --output text)

if [ -z "$ALL_ACTIVE" ]; then
    echo "✓ All GSI indexes are ACTIVE and ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Update your code to use Query instead of Scan"
    echo "2. See: docs/GSI_IMPLEMENTATION_GUIDE.md (section: Code Changes)"
else
    echo "⏳ Some indexes are still building. Check again in a few minutes."
    echo ""
    echo "To continuously monitor, run:"
    echo "  watch -n 30 ./scripts/check_gsi_status.sh"
fi

echo ""
