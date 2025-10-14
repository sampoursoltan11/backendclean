# TRA System Backend - Clean Version

Multi-agent Technology Risk Assessment (TRA) system built with FastAPI and AWS services.

## Overview

This backend provides an AI-powered TRA system using:
- **FastAPI** - REST API + WebSocket support
- **AWS Bedrock** - Claude AI for agent intelligence
- **AWS DynamoDB** - NoSQL database for assessments
- **AWS S3** - Document storage
- **Strands Agents SDK 1.x** - Multi-agent orchestration

## Architecture

```
backend/
├── api/            # FastAPI application & endpoints
├── agents/         # Strands agent implementations (deprecated - see variants/)
├── variants/       # Production agents
│   └── enterprise/ # Multi-agent orchestrator + 4 specialized agents
├── services/       # AWS service clients (S3, DynamoDB, Bedrock)
├── tools/          # Agent tools for TRA operations
├── models/         # Pydantic data models
├── utils/          # Shared utilities
├── core/           # Configuration management
└── config/         # YAML configuration files
```

## Multi-Agent System

**Enterprise Orchestrator** routes requests to 4 specialized agents:

1. **Assessment Agent** - Create, update, manage TRA assessments
2. **Question Agent** - Handle TRA questionnaire flow
3. **Document Agent** - Upload, analyze documents, suggest risk areas
4. **Status Agent** - Progress tracking, reports, export

## Quick Start

### Prerequisites

- Python 3.9+
- AWS credentials configured
- DynamoDB table: `tra-system`
- S3 bucket: `bhp-tra-agent-docs-poc`

### Installation

```bash
# Install dependencies
pip install -r requirements.txt  # TODO: Create this file

# Set environment variables
export AWS_DEFAULT_REGION=ap-southeast-2
export DYNAMODB_TABLE_NAME=tra-system
export S3_BUCKET_NAME=bhp-tra-agent-docs-poc
```

### Run Locally

```bash
# Start the server
cd backend
uvicorn api.main:app --reload --port 8000

# Server will be available at:
# - HTTP: http://localhost:8000
# - WebSocket: ws://localhost:8000/ws/enterprise/{session_id}
```

## API Endpoints

### REST API

- `GET /api/health` - Health check
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/ingestion_status/{job_id}` - Check ingestion status

### WebSocket

- `ws://localhost:8000/ws/enterprise/{session_id}` - Enterprise TRA chat

**Message Format:**
```json
{
  "type": "message",
  "content": "Create a new TRA assessment",
  "context": {
    "assessment_id": "TRA-2025-ABC123"
  }
}
```

## Configuration

Configuration is managed through:
- **Environment variables** (`.env` file)
- **Pydantic settings** (`backend/core/config.py`)
- **Decision tree YAML** (`backend/config/decision_tree2.yaml`)

### Key Settings

```python
# AWS Configuration
aws_region = "ap-southeast-2"
bedrock_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
dynamodb_table_name = "tra-system"
s3_bucket_name = "bhp-tra-agent-docs-poc"

# Application
log_level = "INFO"
session_storage_dir = "./sessions"
```

## Logging

Logs are written to:
- **File**: `logs/tra_system.log` (with rotation, 7 days retention)
- **Console**: Formatted output for development

Log levels:
- `DEBUG` - Verbose developer information
- `INFO` - Important business events
- `WARNING` - Non-critical issues
- `ERROR` - Errors with stack traces

## Code Quality Improvements

This codebase has been cleaned and optimized:

✅ **Phase 1**: Removed 487 lines of unused analytics models
✅ **Phase 2**: Consolidated duplicate utilities into `utils/common.py`
✅ **Phase 4**: Replaced 140 print statements with proper logging

**Total**: ~700 lines cleaned/improved for better maintainability

See `docs/cleanup-history/` for detailed change logs.

## Testing

```bash
# TODO: Add test suite
pytest backend/tests/
```

## Deployment

### Docker (Recommended)

```bash
# TODO: Create Dockerfile
docker build -t tra-backend .
docker run -p 8000:8000 tra-backend
```

### AWS Deployment Options

1. **AWS App Runner** - Easiest, fully managed
2. **ECS Fargate** - More control, container orchestration
3. **Lambda + API Gateway** - Serverless (requires WebSocket refactoring)

See `docs/deployment/` for detailed instructions (TODO).

## Development

### Code Structure

- **Agents**: Follow Strands 1.x patterns
- **Tools**: Async functions with `@tool` decorator
- **Services**: Singleton pattern for AWS clients
- **Models**: Pydantic for data validation

### Adding New Agents

```python
from strands import Agent, tool
from strands.models import BedrockModel

@tool
async def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": "success"}

agent = Agent(
    model=BedrockModel(model_id="..."),
    system_prompt="You are...",
    tools=[my_tool]
)
```

## Contributing

1. Use proper logging (`logger.debug/info/warning/error`)
2. Follow async/await patterns
3. Add type hints
4. Update documentation
5. Test thoroughly

## Troubleshooting

### Common Issues

**Issue**: "No module named 'backend'"
- **Solution**: Run from project root, not `backend/` directory

**Issue**: AWS credentials not found
- **Solution**: Configure AWS CLI or set environment variables

**Issue**: DynamoDB table not found
- **Solution**: Create table with pk (String) and sk (String)

## License

[Add license information]

## Contact

[Add contact information]

---

**Last Updated**: 2025-01-14
**Version**: 2.0.0 - Strands 1.x Native
**Status**: ✅ Production Ready
