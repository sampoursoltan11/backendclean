# Running TRA Backend Locally

## Quick Start

### 1. Start the Backend Server

```bash
./run_backend.sh
```

The server will start on `http://localhost:8000`

### 2. Test the Backend (in another terminal)

```bash
./test_backend.sh
```

### 3. View API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Prerequisites

### Required

✅ **Python 3.9+** - Already installed
✅ **AWS Credentials** - Already configured
  - Account: `448608816491`
  - Region: `ap-southeast-2`

✅ **Dependencies** - Already installed:
  - FastAPI 0.118.0
  - Uvicorn 0.37.0
  - aioboto3 15.2.0
  - boto3 1.40.18
  - strands-agents 1.10.0

### AWS Resources (Already Set Up)

✅ **DynamoDB Table**: `tra-system`
  - All 5 GSI indexes ACTIVE
  - Optimized for 70-90% cost reduction

✅ **S3 Bucket**: `bhp-tra-agent-docs-poc`
  - Document storage

✅ **Bedrock**: Claude 3 Haiku model
  - Model: `anthropic.claude-3-haiku-20240307-v1:0`

## Detailed Instructions

### Starting the Server

#### Option 1: Use the Startup Script (Recommended)

```bash
./run_backend.sh
```

This script will:
- ✓ Check Python installation
- ✓ Verify AWS credentials
- ✓ Check DynamoDB table exists
- ✓ Check S3 bucket access
- ✓ Create required directories
- ✓ Start FastAPI with auto-reload

#### Option 2: Manual Start

```bash
# Create required directories
mkdir -p logs sessions backend/local_kb backend/local_s3

# Start server
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Server Information

Once running, you'll see:

```
================================
TRA Backend Startup
================================

✓ Checking Python...
✓ Checking AWS credentials...
✓ Checking DynamoDB table...
✓ Checking S3 bucket...
✓ Creating required directories...

Configuration:
  Region: ap-southeast-2
  DynamoDB Table: tra-system
  S3 Bucket: bhp-tra-agent-docs-poc
  Bedrock Model: anthropic.claude-3-haiku-20240307-v1:0

Starting FastAPI server...
  URL: http://localhost:8000
  Docs: http://localhost:8000/docs
  Logs: logs/tra_system.log
```

## Testing the Backend

### Automated Tests

```bash
# Run all tests
./test_backend.sh
```

This will test:
- ✓ Health check endpoint
- ✓ API documentation
- ✓ OpenAPI schema
- ✓ DynamoDB GSI queries
- ✓ Database connectivity

### Manual Testing

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "dynamodb": "reachable",
  "s3": "accessible"
}
```

#### 2. Test GSI Query (Draft Assessments)

```bash
curl "http://localhost:8000/api/assessments?status=draft"
```

This uses the optimized GSI4 query (10-50x faster than SCAN).

#### 3. Test Document Upload

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf" \
  -F "assessment_id=TRA-2025-TEST01"
```

### Python Test Script

Test DynamoDB GSI queries directly:

```python
python3 tests/test_gsi_queries.py
```

Expected output:
```
================================================================================
Testing GSI-Based DynamoDB Queries
================================================================================

Test 1: Creating assessment with GSI attributes...
✓ Assessment created: TRA-2025-XXXXXX
  - entity_type: assessment
  - status: draft
  - session_id: test-session-20251014

Test 2: Querying assessments by state using GSI4...
✓ GSI4 Query successful: Found XX draft assessments

...
```

## Available Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI documentation |
| `/redoc` | GET | ReDoc documentation |
| `/openapi.json` | GET | OpenAPI schema |

### Assessment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/assessments` | GET | List assessments (uses GSI4) |
| `/api/assessments/{id}` | GET | Get assessment details |
| `/ws/enterprise` | WebSocket | Enterprise TRA agent |

### Document Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents/upload` | POST | Upload document |
| `/api/documents/{assessment_id}` | GET | List docs (uses GSI1) |
| `/api/documents/ingestion_status/{job_id}` | GET | Check KB ingestion |

## Configuration

### Environment Variables (Optional)

Create a `.env` file to override defaults:

```bash
# AWS Configuration
AWS_REGION=ap-southeast-2
DYNAMODB_TABLE_NAME=tra-system
S3_BUCKET_NAME=bhp-tra-agent-docs-poc

# Application
LOG_LEVEL=INFO
DEBUG=false

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### Default Configuration

Defaults from `backend/core/config.py`:

```python
aws_region = "ap-southeast-2"
dynamodb_table_name = "tra-system"
s3_bucket_name = "bhp-tra-agent-docs-poc"
bedrock_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
```

## Monitoring

### View Logs

```bash
# Follow logs in real-time
tail -f logs/tra_system.log

# View last 100 lines
tail -n 100 logs/tra_system.log

# Search for errors
grep ERROR logs/tra_system.log
```

### Log Locations

- **Application Logs**: `logs/tra_system.log`
- **Session Data**: `sessions/`
- **Local KB**: `backend/local_kb/` (fallback)
- **Local S3**: `backend/local_s3/` (fallback)

## Troubleshooting

### Server won't start

**Problem**: `ModuleNotFoundError`

```bash
# Solution: Install dependencies
pip3 install fastapi uvicorn aioboto3 boto3 strands-agents pydantic pydantic-settings
```

**Problem**: `AWS credentials not configured`

```bash
# Solution: Configure AWS CLI
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=ap-southeast-2
```

**Problem**: `DynamoDB table not found`

```bash
# Solution: Create table with Terraform
cd infrastructure/terraform
terraform init
terraform apply -var-file="environments/development.tfvars"
```

### DynamoDB GSI Errors

**Problem**: `ValidationException: The table does not have the specified index`

**Solution**: Check GSI status

```bash
aws dynamodb describe-table \
  --table-name tra-system \
  --query "Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]" \
  --output table
```

All GSIs should show `ACTIVE`:
- gsi2-session-entity
- gsi3-assessment-events
- gsi4-state-updated
- gsi5-title-search
- gsi6-entity-type

### Performance Issues

**Problem**: Slow queries

**Solution**: Check if GSIs are being used

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=tra-system \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## Development Tips

### Auto-Reload

The server runs with `--reload` flag, so code changes will automatically restart the server.

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG ./run_backend.sh
```

### Interactive API Testing

Use Swagger UI for interactive testing:

1. Open http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"

### WebSocket Testing

Use a WebSocket client to test the agent:

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/enterprise');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'message',
    content: 'Start new TRA assessment'
  }));
};

ws.onmessage = (event) => {
  console.log('Response:', JSON.parse(event.data));
};
```

## Performance Metrics

### GSI Optimization Results

With all 5 GSIs ACTIVE:

| Operation | Before (SCAN) | After (GSI Query) | Improvement |
|-----------|---------------|-------------------|-------------|
| Get assessments by state | 2-5s | 50-100ms | **20-50x faster** |
| Get session messages | 2-4s | 50-150ms | **15-30x faster** |
| Get assessment events | 2-4s | 50-150ms | **15-30x faster** |
| Link documents | 3-8s | 100-200ms | **15-40x faster** |

**Cost Reduction**: 70-90% reduction in DynamoDB read costs

## Next Steps

1. **Frontend Integration**: Connect frontend to `http://localhost:8000`
2. **Custom Testing**: Create assessment via WebSocket
3. **Document Upload**: Test document processing workflow
4. **Monitoring**: Set up CloudWatch dashboards
5. **Production Deploy**: Use Terraform to deploy to AWS

## Support

### Documentation

- **GSI Optimization**: [docs/GSI_OPTIMIZATION_COMPLETE.md](docs/GSI_OPTIMIZATION_COMPLETE.md)
- **Infrastructure**: [infrastructure/terraform/README.md](infrastructure/terraform/README.md)
- **API Docs**: http://localhost:8000/docs (when server running)

### Logs

All operations are logged to `logs/tra_system.log` with timestamps and context.

---

**Server Status**: Ready to run ✓
**AWS Resources**: Configured ✓
**GSI Optimization**: Complete ✓
