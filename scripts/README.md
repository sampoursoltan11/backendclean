# DynamoDB GSI Creation Scripts

This folder contains scripts to create Global Secondary Indexes (GSIs) for the `tra-system` DynamoDB table.

## Quick Start

### 1. Check Current Status

```bash
./scripts/check_gsi_status.sh
```

### 2. Create Remaining GSI Indexes

```bash
./scripts/create_remaining_gsi_indexes.sh
```

This script will:
- Wait for GSI 2 to finish building
- Create GSI 3 (assessment events)
- Wait for it to finish
- Create GSI 4 (state index)
- Wait for it to finish
- Create GSI 5 (title search)
- Wait for it to finish
- Create GSI 6 (entity type)
- Display final status

**Estimated time: 15-45 minutes** (depending on your data size)

## Current Status

✅ **GSI 2** (`gsi2-session-entity`) - Currently building (initiated successfully)

🔄 **GSI 3-6** - Waiting for GSI 2 to complete before creation

## Scripts

### `check_gsi_status.sh`
- Check the build status of all GSI indexes
- Shows IndexName, Status, and ItemCount
- Use this to monitor progress

### `create_gsi_indexes.sh`
- Original script (already executed)
- Created GSI 2 successfully
- Other indexes failed due to DynamoDB's 1-at-a-time limitation

### `create_remaining_gsi_indexes.sh`
- **Use this script** to create GSI 3, 4, 5, 6
- Automatically waits for each index to complete before creating the next
- Safe to run multiple times (skips existing indexes)

## Monitoring Progress

### Watch mode (auto-refresh every 30 seconds):
```bash
watch -n 30 ./scripts/check_gsi_status.sh
```

Press `Ctrl+C` to exit watch mode.

### Manual check:
```bash
aws dynamodb describe-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus,ItemCount]' \
    --output table
```

## What Each GSI Does

| Index | Purpose | Replaces |
|-------|---------|----------|
| **GSI 2** | Query documents by session | SCAN in `get_session_messages()` |
| **GSI 3** | Query events by assessment | SCAN in `get_assessment_events()` |
| **GSI 4** | Query assessments by status | SCAN in `query_assessments_by_state()` |
| **GSI 5** | Search assessments by title | SCAN in `search_assessments()` |
| **GSI 6** | List items by type | SCAN in `list_assessments()` |

## Expected Impact

- **70-90% cost reduction** on DynamoDB operations
- **10-100x faster** query performance
- No more expensive SCAN operations

## Next Steps (After All GSIs Are ACTIVE)

1. **Update your code** to use Query instead of Scan
   - See: [`docs/GSI_IMPLEMENTATION_GUIDE.md`](../docs/GSI_IMPLEMENTATION_GUIDE.md) (section: Code Changes)

2. **Test performance improvements**
   - Run your application
   - Monitor CloudWatch metrics
   - Verify cost reduction

3. **Monitor CloudWatch**
   - Check `ConsumedReadCapacityUnits` (should drop significantly)
   - Check query latencies (should improve 10-100x)

## Troubleshooting

### Script fails with "ResourceInUseException"
- This means the table is still updating from a previous operation
- Wait a few minutes and try again

### Script fails with "LimitExceededException"
- DynamoDB only allows 1 GSI to be created at a time
- Use `create_remaining_gsi_indexes.sh` which waits between creations

### Index stuck in "CREATING" status
- This is normal for large tables
- Can take 5-30 minutes depending on data size
- Use `check_gsi_status.sh` to monitor

### Need to delete a GSI?
```bash
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --global-secondary-index-updates \
        '[{"Delete": {"IndexName": "gsi2-session-entity"}}]'
```

## Reference

- Full implementation guide: [`docs/GSI_IMPLEMENTATION_GUIDE.md`](../docs/GSI_IMPLEMENTATION_GUIDE.md)
- Optimization summary: [`docs/OPTIMIZATION_SUMMARY.md`](../docs/OPTIMIZATION_SUMMARY.md)
- DynamoDB Best Practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html
