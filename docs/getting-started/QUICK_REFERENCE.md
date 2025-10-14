# TRA Backend - Quick Reference

## Essential Commands

### Server Management

```bash
# Start backend
./scripts/run_backend.sh

# Stop backend
./scripts/stop_backend.sh

# Test backend
./scripts/test_backend.sh
```

### Monitoring

```bash
# View logs
tail -f logs/tra_system.log

# Check server status
curl http://localhost:8000/api/health
```

### Testing

```bash
# Test GSI queries
python3 tests/test_gsi_queries.py

# Test API scenarios
python3 tests/test_api_scenarios.py

# Manual endpoint test
curl "http://localhost:8000/api/assessments/search?query=test"
```

## Key URLs

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **System Status**: http://localhost:8000/api/system/status

## Project Structure

```
├── README.md                  # Main documentation
├── backend/                   # Application code
├── scripts/                   # Utility scripts
│   ├── run_backend.sh         # Start server
│   ├── stop_backend.sh        # Stop server
│   ├── test_backend.sh        # Run tests
│   └── check_gsi_status.sh    # Check GSI status
├── docs/                      # Documentation
│   ├── QUICK_REFERENCE.md     # This file
│   ├── RUNNING_LOCALLY.md     # Detailed setup
│   ├── TEST_RESULTS.md        # Test results
│   └── GSI_OPTIMIZATION_COMPLETE.md  # Performance info
├── tests/                     # Test files
├── infrastructure/            # Terraform IaC
└── logs/                      # Application logs
```

## GSI Indexes (All ACTIVE)

| Index | Keys | Used For |
|-------|------|----------|
| gsi2-session-entity | session_id + entity_type | Session queries |
| gsi3-assessment-events | assessment_id + event_type | Events |
| gsi4-state-updated | current_state + updated_at | State queries |
| gsi5-title-search | title_lowercase + created_at | Search |
| gsi6-entity-type | entity_type + updated_at | Type queries |

## Quick Troubleshooting

**Server won't start?**
```bash
# Check if already running
ps aux | grep uvicorn

# Stop existing server
./scripts/stop_backend.sh

# Check AWS credentials
aws sts get-caller-identity
```

**Tests failing?**
```bash
# Check DynamoDB table
aws dynamodb describe-table --table-name tra-system

# Check GSI status
./scripts/check_gsi_status.sh
```

## Performance Metrics

- **70-90%** reduction in DynamoDB costs
- **10-50x** faster query performance
- **< 200ms** API response times
- **Zero** SCAN operations

## Documentation

- **Main**: [README.md](../README.md)
- **Setup**: [RUNNING_LOCALLY.md](RUNNING_LOCALLY.md)
- **Tests**: [TEST_RESULTS.md](TEST_RESULTS.md)
- **GSI**: [GSI_OPTIMIZATION_COMPLETE.md](GSI_OPTIMIZATION_COMPLETE.md)
- **Infrastructure**: [../infrastructure/terraform/README.md](../infrastructure/terraform/README.md)
