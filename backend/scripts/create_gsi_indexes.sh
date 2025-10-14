#!/bin/bash

# DynamoDB GSI Creation Script (On-Demand Billing Mode)
# This script creates 5 Global Secondary Indexes for the tra-system table
# Run this script to optimize DynamoDB queries and reduce costs by 70-90%

set -e  # Exit on error

TABLE_NAME="tra-system"
REGION="ap-southeast-2"

echo "========================================"
echo "DynamoDB GSI Creation Script"
echo "========================================"
echo "Table: $TABLE_NAME"
echo "Region: $REGION"
echo "Billing Mode: PAY_PER_REQUEST (On-Demand)"
echo ""

echo "Creating GSI indexes for $TABLE_NAME..."
echo ""

# ========================================
# GSI 2: Session Index
# ========================================
echo "----------------------------------------"
echo "Creating GSI 2: gsi2-session-entity"
echo "Purpose: Query documents by session"
echo "----------------------------------------"

aws dynamodb update-table \
    --table-name $TABLE_NAME \
    --region $REGION \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=entity_type,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "gsi2-session-entity",
                "KeySchema": [
                    {"AttributeName": "session_id", "KeyType": "HASH"},
                    {"AttributeName": "entity_type", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            }
        }]' && echo "✓ GSI 2 created successfully" || echo "⚠ GSI 2 already exists or error occurred"

echo ""

# Wait for the previous index to start building before creating the next
echo "Waiting 30 seconds before creating next index..."
sleep 30

# ========================================
# GSI 3: Assessment Events Index
# ========================================
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
        }]' && echo "✓ GSI 3 created successfully" || echo "⚠ GSI 3 already exists or error occurred"

echo ""

echo "Waiting 30 seconds before creating next index..."
sleep 30

# ========================================
# GSI 4: State Index
# ========================================
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
        }]' && echo "✓ GSI 4 created successfully" || echo "⚠ GSI 4 already exists or error occurred"

echo ""

echo "Waiting 30 seconds before creating next index..."
sleep 30

# ========================================
# GSI 5: Title Search Index
# ========================================
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
        }]' && echo "✓ GSI 5 created successfully" || echo "⚠ GSI 5 already exists or error occurred"

echo ""

echo "Waiting 30 seconds before creating next index..."
sleep 30

# ========================================
# GSI 6: Entity Type Index
# ========================================
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
        }]' && echo "✓ GSI 6 created successfully" || echo "⚠ GSI 6 already exists or error occurred"

echo ""

# ========================================
# Check Status
# ========================================
echo "========================================"
echo "All GSI creation commands completed!"
echo "========================================"
echo ""
echo "Indexes are now building in the background."
echo "This can take 5-30 minutes depending on your data size."
echo ""
echo "To check status, run:"
echo "  ./scripts/check_gsi_status.sh"
echo ""
echo "Or manually:"
echo "  aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]' --output table"
echo ""
