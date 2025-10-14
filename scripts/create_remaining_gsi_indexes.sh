#!/bin/bash

# DynamoDB GSI Creation Script - Create Remaining Indexes
# This script creates the remaining 4 GSI indexes one at a time
# DynamoDB only allows 1 GSI to be created at a time

set -e  # Exit on error

TABLE_NAME="tra-system"
REGION="ap-southeast-2"

echo "========================================"
echo "DynamoDB GSI Creation Script"
echo "Creating Remaining GSI Indexes"
echo "========================================"
echo "Table: $TABLE_NAME"
echo "Region: $REGION"
echo ""

# Function to wait for all GSIs to be ACTIVE
wait_for_gsi_active() {
    echo "⏳ Waiting for all GSIs to be ACTIVE..."
    while true; do
        # Check if any GSI is still CREATING or UPDATING
        STATUS=$(aws dynamodb describe-table \
            --table-name $TABLE_NAME \
            --region $REGION \
            --query 'Table.GlobalSecondaryIndexes[?IndexStatus!=`ACTIVE`]' \
            --output text 2>/dev/null)

        if [ -z "$STATUS" ]; then
            echo "✓ All GSIs are ACTIVE!"
            break
        fi

        # Show current status
        aws dynamodb describe-table \
            --table-name $TABLE_NAME \
            --region $REGION \
            --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]' \
            --output table

        echo "Still building... checking again in 30 seconds"
        sleep 30
    done
}

# Check current status
echo "Current GSI Status:"
aws dynamodb describe-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]' \
    --output table || echo "No GSIs yet"

echo ""

# Wait for any in-progress GSI creation to complete
wait_for_gsi_active

# ========================================
# GSI 3: Assessment Events Index
# ========================================
echo ""
echo "----------------------------------------"
echo "Creating GSI 3: gsi3-assessment-events"
echo "Purpose: Query events by assessment"
echo "----------------------------------------"

aws dynamodb update-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --attribute-definitions \
        AttributeName=assessment_id,AttributeType=S \
        AttributeName=event_type,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "gsi3-assessment-events",
                "KeySchema": [
                    {"AttributeName": "assessment_id", "KeyType": "HASH"},
                    {"AttributeName": "event_type", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        }]' && echo "✓ GSI 3 creation initiated" || echo "⚠ GSI 3 already exists"

wait_for_gsi_active

# ========================================
# GSI 4: State Index
# ========================================
echo ""
echo "----------------------------------------"
echo "Creating GSI 4: gsi4-state-updated"
echo "Purpose: Query assessments by status"
echo "----------------------------------------"

aws dynamodb update-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --attribute-definitions \
        AttributeName=current_state,AttributeType=S \
        AttributeName=updated_at,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "gsi4-state-updated",
                "KeySchema": [
                    {"AttributeName": "current_state", "KeyType": "HASH"},
                    {"AttributeName": "updated_at", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        }]' && echo "✓ GSI 4 creation initiated" || echo "⚠ GSI 4 already exists"

wait_for_gsi_active

# ========================================
# GSI 5: Title Search Index
# ========================================
echo ""
echo "----------------------------------------"
echo "Creating GSI 5: gsi5-title-search"
echo "Purpose: Search assessments by title"
echo "----------------------------------------"

aws dynamodb update-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --attribute-definitions \
        AttributeName=title_lowercase,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "gsi5-title-search",
                "KeySchema": [
                    {"AttributeName": "title_lowercase", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        }]' && echo "✓ GSI 5 creation initiated" || echo "⚠ GSI 5 already exists"

wait_for_gsi_active

# ========================================
# GSI 6: Entity Type Index
# ========================================
echo ""
echo "----------------------------------------"
echo "Creating GSI 6: gsi6-entity-type"
echo "Purpose: List items by type"
echo "----------------------------------------"

aws dynamodb update-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --attribute-definitions \
        AttributeName=entity_type,AttributeType=S \
        AttributeName=updated_at,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "gsi6-entity-type",
                "KeySchema": [
                    {"AttributeName": "entity_type", "KeyType": "HASH"},
                    {"AttributeName": "updated_at", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        }]' && echo "✓ GSI 6 creation initiated" || echo "⚠ GSI 6 already exists"

wait_for_gsi_active

# ========================================
# Final Status
# ========================================
echo ""
echo "========================================"
echo "✓ All GSI Indexes Created Successfully!"
echo "========================================"
echo ""
echo "Final GSI Status:"
aws dynamodb describe-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus,ItemCount]' \
    --output table

echo ""
echo "Next steps:"
echo "1. Update your code to use Query instead of Scan"
echo "2. See: docs/GSI_IMPLEMENTATION_GUIDE.md (section: Code Changes)"
echo ""
