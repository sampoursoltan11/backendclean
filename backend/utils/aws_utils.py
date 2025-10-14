"""
AWS utility functions consolidated module.

This module serves as a central import point for all AWS-related utilities,
creating a clean, well-organized API for AWS-related functionality throughout the application.

Available Utilities:
1. Bedrock Model ID Handling (from aws_bedrock.py)
   - sanitize_bedrock_model_id(): Strips regional prefixes from Bedrock model IDs
   - sanitize_converse_model_id(): Comprehensive sanitization with logging and fallbacks
   - get_converse_model_id(): High-level helper with optional override

2. DynamoDB Serialization (from dynamodb_serialization.py)
   - to_dynamodb_safe(): Converts Python values to DynamoDB-compatible types
   - model_dump_dynamodb_safe(): Safely dumps Pydantic models for DynamoDB
   - serialize_for_dynamodb(): Alias for to_dynamodb_safe()
   - json_serialize_for_dynamodb(): Alternative JSON round-trip serialization

This module consolidates multiple utility files to provide a consistent interface
and reduce import complexity across the application.
"""

# Re-export Bedrock utilities
from backend.utils.aws_bedrock import (
    sanitize_bedrock_model_id,
    sanitize_converse_model_id,
    get_converse_model_id,
)

# Re-export DynamoDB serialization utilities
from backend.utils.dynamodb_serialization import (
    to_dynamodb_safe,
    model_dump_dynamodb_safe,
    serialize_for_dynamodb,
    json_serialize_for_dynamodb,
)

# Export all for * imports
__all__ = [
    # Bedrock utilities
    'sanitize_bedrock_model_id',
    'sanitize_converse_model_id',
    'get_converse_model_id',
    
    # DynamoDB utilities
    'to_dynamodb_safe',
    'model_dump_dynamodb_safe',
    'serialize_for_dynamodb',
    'json_serialize_for_dynamodb',
]