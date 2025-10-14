"""
DynamoDB serialization utilities.

This module provides comprehensive utilities for safely serializing data for DynamoDB
storage, addressing common type compatibility issues:

Common DynamoDB Type Errors:
- "Float types are not supported. Use Decimal types instead." - Occurs when trying to 
  store Python float values directly in DynamoDB
- "Unsupported type <class 'datetime.datetime'>" - Occurs when datetime objects 
  aren't converted to strings

Key Functions:
- to_dynamodb_safe(): Recursively converts Python values to DynamoDB-safe types
- model_dump_dynamodb_safe(): Safely dumps Pydantic models for DynamoDB storage
- serialize_for_dynamodb(): Alias for to_dynamodb_safe() for backwards compatibility
- json_serialize_for_dynamodb(): Alternative approach using JSON round-trip serialization

Type Conversions:
- datetime/date → ISO 8601 strings
- float → Decimal (via string to avoid precision issues)
- dict/list → recursively processed
- None/bool/int/str → unchanged (already DynamoDB-compatible)

Usage Examples:
1. With Pydantic models: item = model_dump_dynamodb_safe(my_pydantic_model)
2. With dictionaries: item = to_dynamodb_safe(my_dict)

These utilities ensure all data is properly sanitized before writing to DynamoDB tables.
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Mapping, MutableMapping, Union, Tuple, Optional

logger = logging.getLogger(__name__)


# Import consolidated functions from common.py
from .common import to_dynamodb_safe, model_dump_dynamodb_safe


def serialize_for_dynamodb(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare an item for storage in DynamoDB by converting unsupported types.
    
    This is an alias for to_dynamodb_safe to maintain backwards compatibility.
    
    Args:
        item: Dictionary to serialize
        
    Returns:
        Dictionary with all values converted to DynamoDB-compatible types
    """
    return to_dynamodb_safe(item)


def json_serialize_for_dynamodb(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Alternative serialization approach using JSON round-trip with Decimal parsing.
    This can be useful for complex nested structures.
    
    Args:
        item: Dictionary to serialize
        
    Returns:
        Dictionary with all values converted to DynamoDB-compatible types
    """
    # Convert to JSON with datetime handling
    json_str = json.dumps(item, default=lambda o: o.isoformat() if isinstance(o, (datetime, date)) else str(o))
    
    # Parse back with Decimal handling for floats
    return json.loads(json_str, parse_float=Decimal)