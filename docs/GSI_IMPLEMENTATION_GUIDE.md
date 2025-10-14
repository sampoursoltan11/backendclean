# DynamoDB GSI Implementation Guide

## Overview

Your DynamoDB table currently uses expensive SCAN operations to query data. This guide shows you exactly how to add Global Secondary Indexes (GSIs) to enable fast, efficient Query operations.

**Impact:** 70-90% cost reduction + 10-100x faster queries

---

## Current Table Structure

Your table uses a single-table design pattern:

```
Primary Key:
- pk (Partition Key): String - e.g., "ASSESSMENT#123", "DOC#456"
- sk (Sort Key): String - e.g., "METADATA", "VERSION#1"

Existing GSI:
- gsi1_pk (Partition Key)
- gsi1_sk (Sort Key)
```

---

## Required GSI Indexes

You need to add **5 new GSI indexes** to your DynamoDB table:

### GSI 2: Query by Session ID
**Purpose:** Find documents and messages by session
**Current problem:** Lines using SCAN:
- `get_session_messages()` - dynamodb_service.py:268
- `link_documents_to_assessment()` - dynamodb_service.py:113

```yaml
IndexName: gsi2-session-entity
PartitionKey: session_id (String)
SortKey: entity_type (String)
ProjectionType: ALL
```

**Usage:**
```python
# Instead of SCAN
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi2-session-entity',
    KeyConditionExpression='session_id = :sid',
    ExpressionAttributeValues={':sid': {'S': session_id}}
)
```

---

### GSI 3: Query by Assessment ID + Event Type
**Purpose:** Find events/reviews for an assessment
**Current problem:** Lines using SCAN:
- `get_assessment_reviews()` - dynamodb_service.py:278
- `get_assessment_events()` - dynamodb_service.py:288

```yaml
IndexName: gsi3-assessment-events
PartitionKey: assessment_id (String)
SortKey: event_type (String)
ProjectionType: ALL
```

**Usage:**
```python
# Get all events for an assessment
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi3-assessment-events',
    KeyConditionExpression='assessment_id = :aid',
    ExpressionAttributeValues={':aid': {'S': assessment_id}}
)

# Get specific event type (e.g., only reviews)
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi3-assessment-events',
    KeyConditionExpression='assessment_id = :aid AND event_type = :typ',
    ExpressionAttributeValues={
        ':aid': {'S': assessment_id},
        ':typ': {'S': 'assessment_review'}
    }
)
```

---

### GSI 4: Query by Assessment State
**Purpose:** List assessments by status (draft, in_progress, completed)
**Current problem:** Lines using SCAN:
- `query_assessments_by_state()` - dynamodb_service.py:297

```yaml
IndexName: gsi4-state-updated
PartitionKey: current_state (String)
SortKey: updated_at (String)
ProjectionType: ALL
```

**Usage:**
```python
# Get all "in_progress" assessments, sorted by most recent
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi4-state-updated',
    KeyConditionExpression='current_state = :state',
    ExpressionAttributeValues={':state': {'S': 'in_progress'}},
    ScanIndexForward=False  # Descending order (newest first)
)
```

---

### GSI 5: Search Assessments by Title
**Purpose:** Search/filter assessments by title
**Current problem:** Lines using SCAN:
- `search_assessments()` - dynamodb_service.py:480

```yaml
IndexName: gsi5-title-search
PartitionKey: title_lowercase (String)
SortKey: created_at (String)
ProjectionType: ALL
```

**Note:** You'll need to add a `title_lowercase` attribute when creating/updating assessments.

**Usage:**
```python
# Exact title match (or begins_with for partial match)
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi5-title-search',
    KeyConditionExpression='begins_with(title_lowercase, :title)',
    ExpressionAttributeValues={':title': {'S': 'azure migration'}}
)
```

---

### GSI 6: List Items by Entity Type
**Purpose:** List all assessments, documents, or KB items
**Current problem:** Lines using SCAN:
- `list_assessments()` - tools/assessment_tools.py:256
- Similar patterns in document and KB tools

```yaml
IndexName: gsi6-entity-type
PartitionKey: entity_type (String)
SortKey: updated_at (String)
ProjectionType: ALL
```

**Usage:**
```python
# List all assessments, sorted by most recent
resp = await client.query(
    TableName='tra-system',
    IndexName='gsi6-entity-type',
    KeyConditionExpression='entity_type = :type',
    ExpressionAttributeValues={':type': {'S': 'ASSESSMENT'}},
    Limit=20,
    ScanIndexForward=False
)
```

---

## Implementation Steps

### Option 1: AWS Console (Quick & Easy)

1. **Open DynamoDB Console**
   - Go to: https://console.aws.amazon.com/dynamodb/
   - Region: `ap-southeast-2` (Sydney)
   - Select table: `tra-system`

2. **Create GSI 2 (Session Index)**
   - Click "Indexes" tab
   - Click "Create index"
   - **Partition key:** `session_id` (String)
   - **Sort key:** `entity_type` (String)
   - **Index name:** `gsi2-session-entity`
   - **Projected attributes:** All
   - **Provisioned capacity:** Auto-scaling (or match table settings)
   - Click "Create index"
   - Wait 5-10 minutes for index to build

3. **Repeat for GSI 3, 4, 5, 6**
   - Follow same process with different attributes

4. **Update Code to Use New GSIs**
   - See "Code Changes" section below

---

### Option 2: AWS CLI (Scriptable)

```bash
# GSI 2: Session Index
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=entity_type,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"gsi2-session-entity\",\"KeySchema\":[{\"AttributeName\":\"session_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"entity_type\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"

# Wait for index to build (check status)
aws dynamodb describe-table --table-name tra-system --region ap-southeast-2 | grep IndexStatus

# GSI 3: Assessment Events Index
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --attribute-definitions \
        AttributeName=assessment_id,AttributeType=S \
        AttributeName=event_type,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"gsi3-assessment-events\",\"KeySchema\":[{\"AttributeName\":\"assessment_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"event_type\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"

# GSI 4: State Index
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --attribute-definitions \
        AttributeName=current_state,AttributeType=S \
        AttributeName=updated_at,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"gsi4-state-updated\",\"KeySchema\":[{\"AttributeName\":\"current_state\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"updated_at\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"

# GSI 5: Title Search Index
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --attribute-definitions \
        AttributeName=title_lowercase,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"gsi5-title-search\",\"KeySchema\":[{\"AttributeName\":\"title_lowercase\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"

# GSI 6: Entity Type Index
aws dynamodb update-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --attribute-definitions \
        AttributeName=entity_type,AttributeType=S \
        AttributeName=updated_at,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"gsi6-entity-type\",\"KeySchema\":[{\"AttributeName\":\"entity_type\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"updated_at\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"
```

---

### Option 3: Terraform (Infrastructure as Code)

```hcl
resource "aws_dynamodb_table" "tra_system" {
  name           = "tra-system"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "pk"
  range_key      = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  # Existing GSI1
  attribute {
    name = "gsi1_pk"
    type = "S"
  }

  attribute {
    name = "gsi1_sk"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi1"
    hash_key        = "gsi1_pk"
    range_key       = "gsi1_sk"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  # NEW: GSI 2 - Session Index
  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "entity_type"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi2-session-entity"
    hash_key        = "session_id"
    range_key       = "entity_type"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  # NEW: GSI 3 - Assessment Events Index
  attribute {
    name = "assessment_id"
    type = "S"
  }

  attribute {
    name = "event_type"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi3-assessment-events"
    hash_key        = "assessment_id"
    range_key       = "event_type"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  # NEW: GSI 4 - State Index
  attribute {
    name = "current_state"
    type = "S"
  }

  attribute {
    name = "updated_at"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi4-state-updated"
    hash_key        = "current_state"
    range_key       = "updated_at"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  # NEW: GSI 5 - Title Search Index
  attribute {
    name = "title_lowercase"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi5-title-search"
    hash_key        = "title_lowercase"
    range_key       = "created_at"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  # NEW: GSI 6 - Entity Type Index
  global_secondary_index {
    name            = "gsi6-entity-type"
    hash_key        = "entity_type"
    range_key       = "updated_at"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  tags = {
    Environment = "production"
    Project     = "TRA-System"
  }
}
```

Then run:
```bash
terraform plan
terraform apply
```

---

## Code Changes After Creating GSIs

### 1. Update `get_session_messages()` - Use GSI 2

**File:** `backend/services/dynamodb_service.py:261-270`

```python
async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
    if not self._use_aws:
        return [m for m in self._messages if m.get('session_id') == session_id]

    # Use GSI2 instead of SCAN
    session = aioboto3.Session()
    async with session.client('dynamodb') as client:
        resp = await client.query(
            TableName=self.table_name,
            IndexName='gsi2-session-entity',
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': {'S': session_id}}
        )
        items = resp.get('Items', [])
        return [{k: list(v.values())[0] for k, v in it.items()} for it in items]
```

---

### 2. Update `get_assessment_reviews()` - Use GSI 3

**File:** `backend/services/dynamodb_service.py:272-280`

```python
async def get_assessment_reviews(self, assessment_id: str) -> List[Dict[str, Any]]:
    if not self._use_aws:
        return self._assessment_reviews.get(assessment_id, [])

    # Use GSI3 instead of SCAN
    session = aioboto3.Session()
    async with session.client('dynamodb') as client:
        resp = await client.query(
            TableName=self.table_name,
            IndexName='gsi3-assessment-events',
            KeyConditionExpression='assessment_id = :aid AND event_type = :typ',
            ExpressionAttributeValues={
                ':aid': {'S': assessment_id},
                ':typ': {'S': 'assessment_review'}
            }
        )
        items = resp.get('Items', [])
        return [{k: list(v.values())[0] for k, v in it.items()} for it in items]
```

---

### 3. Update `get_assessment_events()` - Use GSI 3

**File:** `backend/services/dynamodb_service.py:282-290`

```python
async def get_assessment_events(self, assessment_id: str) -> List[Dict[str, Any]]:
    if not self._use_aws:
        return [e for e in self._events if e.get('assessment_id') == assessment_id]

    # Use GSI3 instead of SCAN
    session = aioboto3.Session()
    async with session.client('dynamodb') as client:
        resp = await client.query(
            TableName=self.table_name,
            IndexName='gsi3-assessment-events',
            KeyConditionExpression='assessment_id = :aid',
            ExpressionAttributeValues={':aid': {'S': assessment_id}}
        )
        items = resp.get('Items', [])
        return [{k: list(v.values())[0] for k, v in it.items()} for it in items]
```

---

### 4. Update `query_assessments_by_state()` - Use GSI 4

**File:** `backend/services/dynamodb_service.py:292-299`

```python
async def query_assessments_by_state(self, state: str) -> List[Dict[str, Any]]:
    import logging
    logging.debug(f"[DynamoDBService DEBUG] query_assessments_by_state (state={state}) AWS_ONLY={self._use_aws}")

    # Use GSI4 instead of SCAN
    session = aioboto3.Session()
    async with session.client('dynamodb') as client:
        resp = await client.query(
            TableName=self.table_name,
            IndexName='gsi4-state-updated',
            KeyConditionExpression='current_state = :state',
            ExpressionAttributeValues={':state': {'S': state}},
            ScanIndexForward=False  # Newest first
        )
        items = resp.get('Items', [])
        return [{k: list(v.values())[0] for k, v in it.items()} for it in items]
```

---

### 5. Update `link_documents_to_assessment()` - Use GSI 2

**File:** `backend/services/dynamodb_service.py:108-120`

```python
# Replace SCAN with Query on GSI2
resp = await client.query(
    TableName=self.table_name,
    IndexName='gsi2-session-entity',
    KeyConditionExpression='session_id = :sid AND begins_with(entity_type, :doc)',
    ExpressionAttributeValues={
        ':sid': {'S': session_id},
        ':doc': {'S': 'DOCUMENT'}
    }
)
```

---

### 6. Update Assessment Creation - Add Required Attributes

**File:** `backend/services/dynamodb_service.py` - In `create_assessment()` method

Add these fields when creating assessments:

```python
safe_item = {
    # ... existing fields ...
    'entity_type': 'ASSESSMENT',  # For GSI6
    'title_lowercase': assessment_obj.title.lower(),  # For GSI5
    'current_state': assessment_obj.current_state,  # For GSI4
}
```

---

### 7. Update Document Creation - Add Required Attributes

Add these fields when creating documents:

```python
document_item = {
    # ... existing fields ...
    'entity_type': 'DOCUMENT',  # For GSI6
    'session_id': session_id,  # For GSI2
}
```

---

## Validation & Testing

### 1. Check GSI Status

```bash
aws dynamodb describe-table \
    --table-name tra-system \
    --region ap-southeast-2 \
    --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]' \
    --output table
```

Expected output:
```
+------------------------+--------+
| gsi1                  | ACTIVE |
| gsi2-session-entity   | ACTIVE |
| gsi3-assessment-events| ACTIVE |
| gsi4-state-updated    | ACTIVE |
| gsi5-title-search     | ACTIVE |
| gsi6-entity-type      | ACTIVE |
+------------------------+--------+
```

---

### 2. Performance Testing

Before/after comparison:

```python
import time

async def benchmark_query():
    # Test query_assessments_by_state
    start = time.time()
    results = await db.query_assessments_by_state('in_progress')
    elapsed = time.time() - start
    print(f"Query time: {elapsed:.3f}s, Results: {len(results)}")

# BEFORE (SCAN): ~2-5 seconds for 1000+ items
# AFTER (Query): ~0.05-0.2 seconds for same items
# 10-100x faster!
```

---

### 3. Cost Monitoring

Check CloudWatch metrics:
- Go to: https://console.aws.amazon.com/cloudwatch/
- Select `DynamoDB` → `Table Metrics`
- Monitor:
  - `ConsumedReadCapacityUnits` (should drop 70-90%)
  - `UserErrors` (should be 0 - no throttling)

---

## Summary

**What to do:**
1. Create 5 new GSI indexes (use AWS Console, CLI, or Terraform)
2. Wait for indexes to build (5-30 minutes depending on data size)
3. Update code in 6 locations to use Query instead of Scan
4. Add required attributes (`entity_type`, `title_lowercase`) to items
5. Test and monitor cost/performance improvements

**Expected Results:**
- 70-90% reduction in DynamoDB costs
- 10-100x faster query performance
- No more expensive SCAN operations

**Estimated Time:**
- GSI creation: 15-30 minutes
- Code updates: 1-2 hours
- Testing: 30 minutes
- **Total: 2-3 hours**

**Need Help?**
- DynamoDB GSI Docs: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
- Best Practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes.html
