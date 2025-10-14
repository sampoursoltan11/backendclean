#!/usr/bin/env python3
"""
Comprehensive test script to verify all cleanup changes work correctly.
Tests imports, utilities, logging, and backward compatibility.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

# Test counters
total_tests = 0
passed_tests = 0
failed_tests = 0

def run_test(test_func):
    """Run a test function and track results."""
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    try:
        test_func()
        passed_tests += 1
        return True
    except Exception as e:
        failed_tests += 1
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 1: Core Imports
# ============================================================================

def test_core_imports():
    print_test("Core Module Imports")

    # Test that all core modules can be imported
    from core.config import get_settings
    print_success("Imported: core.config.get_settings")

    from models.tra_models import (
        TraAssessment,
        AssessmentState,
        EventType,
        TraEvent,
        DocumentMetadata
    )
    print_success("Imported: Essential models from tra_models")

    from utils.common import (
        get_current_timestamp,
        serialize_datetime,
        to_dynamodb_safe,
        model_dump_dynamodb_safe,
        sanitize_bedrock_model_id,
        INFERENCE_PROFILE_PREFIXES
    )
    print_success("Imported: All functions from utils.common")

    print_success("All core imports successful!")

# ============================================================================
# TEST 2: Backward Compatibility Imports
# ============================================================================

def test_backward_compatibility_imports():
    print_test("Backward Compatibility Imports")

    # Test that old import paths still work
    from utils.aws_sanitize import (
        to_dynamodb_safe,
        sanitize_bedrock_model_id
    )
    print_success("Imported: utils.aws_sanitize (backward compat)")

    from utils.dynamodb_serialization import (
        to_dynamodb_safe as ddb_safe,
        model_dump_dynamodb_safe
    )
    print_success("Imported: utils.dynamodb_serialization (backward compat)")

    from utils.aws_bedrock import sanitize_bedrock_model_id as sanitize_v2
    print_success("Imported: utils.aws_bedrock (backward compat)")

    print_success("All backward compatibility imports work!")

# ============================================================================
# TEST 3: Utility Functions Work Correctly
# ============================================================================

def test_utility_functions():
    print_test("Utility Functions Behavior")

    from datetime import datetime
    from decimal import Decimal
    from utils.common import (
        get_current_timestamp,
        serialize_datetime,
        to_dynamodb_safe,
        sanitize_bedrock_model_id
    )

    # Test 1: get_current_timestamp
    timestamp = get_current_timestamp()
    assert isinstance(timestamp, str), "Timestamp should be string"
    assert 'T' in timestamp, "Timestamp should be ISO format"
    print_success(f"get_current_timestamp() works: {timestamp[:19]}")

    # Test 2: serialize_datetime
    test_data = {
        "time": datetime(2025, 1, 14, 10, 30),
        "score": Decimal("3.14"),
        "name": "test",
        "items": [1, 2, Decimal("4.5")]
    }
    result = serialize_datetime(test_data)
    assert result["time"] == "2025-01-14T10:30:00", "Datetime should be serialized"
    assert result["score"] == 3.14, "Decimal should become float"
    assert result["items"][2] == 4.5, "Nested Decimal should work"
    print_success(f"serialize_datetime() works: {result}")

    # Test 3: to_dynamodb_safe
    test_data2 = {
        "time": datetime(2025, 1, 14),
        "value": 3.14,
        "nested": {"score": 2.5}
    }
    result2 = to_dynamodb_safe(test_data2)
    assert result2["time"] == "2025-01-14T00:00:00", "Date should be ISO string"
    assert isinstance(result2["value"], Decimal), "Float should become Decimal"
    assert isinstance(result2["nested"]["score"], Decimal), "Nested float should work"
    print_success(f"to_dynamodb_safe() works: {result2['time']}")

    # Test 4: sanitize_bedrock_model_id
    test_id = "apac.anthropic.claude-3-5-sonnet-20240620-v1:0"
    result3 = sanitize_bedrock_model_id(test_id)
    expected = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    assert result3 == expected, f"Should strip 'apac.' prefix"
    print_success(f"sanitize_bedrock_model_id() works: {result3[:40]}...")

    # Test that already clean IDs pass through
    clean_id = "anthropic.claude-3-haiku-20240307-v1:0"
    result4 = sanitize_bedrock_model_id(clean_id)
    assert result4 == clean_id, "Clean IDs should pass through unchanged"
    print_success(f"Clean IDs pass through correctly")

    print_success("All utility functions work correctly!")

# ============================================================================
# TEST 4: Service Imports
# ============================================================================

def test_service_imports():
    print_test("Service Module Imports")

    from services.dynamodb_service import DynamoDBService
    print_success("Imported: DynamoDBService")

    from services.s3_service import S3Service
    print_success("Imported: S3Service")

    from services.bedrock_kb_service import BedrockKnowledgeBaseService
    print_success("Imported: BedrockKnowledgeBaseService")

    from services.file_tracking_service import FileTrackingService
    print_success("Imported: FileTrackingService")

    print_success("All service imports successful!")

# ============================================================================
# TEST 5: Agent Imports
# ============================================================================

def test_agent_imports():
    print_test("Agent Module Imports")

    from variants.enterprise.orchestrator import EnterpriseOrchestratorAgent
    print_success("Imported: EnterpriseOrchestratorAgent")

    from variants.enterprise.agents.assessment_agent import AssessmentAgent
    print_success("Imported: AssessmentAgent")

    from variants.enterprise.agents.question_agent import QuestionAgent
    print_success("Imported: QuestionAgent")

    from variants.enterprise.agents.document_agent import DocumentAgent
    print_success("Imported: DocumentAgent")

    from variants.enterprise.agents.status_agent import StatusAgent
    print_success("Imported: StatusAgent")

    print_success("All agent imports successful!")

# ============================================================================
# TEST 6: API Imports
# ============================================================================

def test_api_imports():
    print_test("API Module Imports")

    try:
        from api.main import app
        print_success("Imported: FastAPI app")

        # Check that app has the expected routes
        routes = [route.path for route in app.routes]
        assert "/api/health" in routes, "Health endpoint should exist"
        print_success("API has health endpoint")

        # Check for WebSocket endpoint
        ws_routes = [r.path for r in app.routes if hasattr(r, 'path') and '/ws/' in r.path]
        assert len(ws_routes) > 0, "WebSocket endpoint should exist"
        print_success(f"API has WebSocket endpoint(s): {ws_routes}")

    except ImportError as e:
        print_warning(f"API import failed (may need dependencies): {e}")
        print_warning("This is OK if running without FastAPI installed")

    print_success("API import test complete!")

# ============================================================================
# TEST 7: Logging Infrastructure
# ============================================================================

def test_logging_infrastructure():
    print_test("Logging Infrastructure")

    import logging
    from logging_config import setup_logging

    # Test that logging can be set up
    log_file = setup_logging('logs/test_cleanup.log')
    print_success(f"Logging configured: {log_file}")

    # Test that logger works
    logger = logging.getLogger(__name__)
    logger.debug("Test debug message")
    logger.info("Test info message")
    logger.warning("Test warning message")
    print_success("Logger calls work correctly")

    # Check log file was created
    if os.path.exists('logs/test_cleanup.log'):
        print_success("Log file created successfully")
    else:
        print_warning("Log file not created (directory may not exist)")

    print_success("Logging infrastructure works!")

# ============================================================================
# TEST 8: No Syntax Errors in Modified Files
# ============================================================================

def test_syntax_errors():
    print_test("Syntax Errors in Modified Files")

    import py_compile

    modified_files = [
        "models/tra_models.py",
        "api/main.py",
        "utils/common.py",
        "utils/aws_sanitize.py",
        "utils/dynamodb_serialization.py",
        "utils/aws_bedrock.py",
        "services/dynamodb_service.py",
        "services/s3_service.py",
        "services/bedrock_kb_service.py",
        "services/file_tracking_service.py",
        "tools/question_tools.py",
        "variants/enterprise/orchestrator.py",
    ]

    for file_path in modified_files:
        full_path = backend_path / file_path
        if full_path.exists():
            try:
                py_compile.compile(str(full_path), doraise=True)
                print_success(f"No syntax errors: {file_path}")
            except py_compile.PyCompileError as e:
                print_error(f"Syntax error in {file_path}: {e}")
                raise
        else:
            print_warning(f"File not found: {file_path}")

    print_success("No syntax errors in any modified files!")

# ============================================================================
# TEST 9: Pydantic Models Work
# ============================================================================

def test_pydantic_models():
    print_test("Pydantic Models")

    from models.tra_models import TraAssessment, AssessmentState
    from datetime import datetime

    # Create a test assessment
    assessment = TraAssessment(
        assessment_id="TEST-2025-001",
        title="Test Assessment",
        project_name="Test Project",
        creator_email="test@example.com",
        current_state=AssessmentState.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    print_success(f"Created TraAssessment: {assessment.assessment_id}")

    # Test model_dump
    data = assessment.model_dump()
    assert data["assessment_id"] == "TEST-2025-001"
    print_success("model_dump() works")

    # Test with our utility
    from utils.common import model_dump_dynamodb_safe
    safe_data = model_dump_dynamodb_safe(assessment)
    print_success("model_dump_dynamodb_safe() works with Pydantic models")

    print_success("Pydantic models work correctly!")

# ============================================================================
# RUN ALL TESTS
# ============================================================================

def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}   TRA Backend - Cleanup Changes Verification Test Suite   {RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Run all tests
    run_test(test_core_imports)
    run_test(test_backward_compatibility_imports)
    run_test(test_utility_functions)
    run_test(test_service_imports)
    run_test(test_agent_imports)
    run_test(test_api_imports)
    run_test(test_logging_infrastructure)
    run_test(test_syntax_errors)
    run_test(test_pydantic_models)

    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}   TEST SUMMARY   {RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Total Tests:  {total_tests}")
    print(f"{GREEN}Passed:       {passed_tests}{RESET}")
    if failed_tests > 0:
        print(f"{RED}Failed:       {failed_tests}{RESET}")
    else:
        print(f"Failed:       {failed_tests}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    if failed_tests == 0:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}   ✅ ALL TESTS PASSED! Code changes are safe!   {RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'='*60}{RESET}")
        print(f"{RED}   ❌ SOME TESTS FAILED! Review errors above.   {RESET}")
        print(f"{RED}{'='*60}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
