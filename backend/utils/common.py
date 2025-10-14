"""
Common utility functions for the TRA system.
Consolidated datetime, serialization, and AWS utilities to eliminate code duplication.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, Optional
from collections.abc import Mapping
import logging

logger = logging.getLogger(__name__)


# ===== DATETIME UTILITIES =====

def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string (e.g., '2025-01-14T10:30:45.123456')
    """
    return datetime.utcnow().isoformat()


def serialize_datetime(obj: Any) -> Any:
    """Recursively serialize datetime and Decimal objects for JSON compatibility.

    Converts:
    - datetime/date -> ISO 8601 string
    - Decimal -> float
    - dict -> recursively processed dict
    - list -> recursively processed list
    - others -> unchanged

    Args:
        obj: Object to serialize (dict, list, datetime, Decimal, or primitive)

    Returns:
        JSON-serializable version of the input object
    """
    if isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(v) for v in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


# ===== DYNAMODB SERIALIZATION =====

def to_dynamodb_safe(value: Any) -> Any:
    """Recursively convert Python values to DynamoDB-safe types.

    DynamoDB doesn't support:
    - datetime/date objects (converts to ISO 8601 strings)
    - float values (converts to Decimal)

    Args:
        value: Python value to convert

    Returns:
        DynamoDB-compatible value

    Examples:
        >>> to_dynamodb_safe({"time": datetime(2025, 1, 14), "score": 3.14})
        {"time": "2025-01-14T00:00:00", "score": Decimal("3.14")}
    """
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        # Use string conversion to avoid binary float precision issues
        return Decimal(str(value))
    if isinstance(value, Mapping):
        return {k: to_dynamodb_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dynamodb_safe(v) for v in value]
    return value


def model_dump_dynamodb_safe(pydantic_model: Any) -> dict:
    """Dump a Pydantic model to a dict compatible with DynamoDB.

    Uses Pydantic's mode="json" to serialize datetime objects,
    then converts floats to Decimal for DynamoDB compatibility.

    Args:
        pydantic_model: Pydantic model instance or dict-like object

    Returns:
        Dictionary with all values converted to DynamoDB-compatible types

    Raises:
        None - falls back gracefully if model is not Pydantic
    """
    try:
        # Try Pydantic v2 model_dump
        data = pydantic_model.model_dump(mode="json")
    except Exception:
        try:
            # Fallback to dict() for older Pydantic or dict-like objects
            data = dict(pydantic_model)
        except Exception as e:
            logger.warning(f"Failed to convert object to dict: {e}")
            # Last resort if it's not a model or dict-like
            data = pydantic_model if isinstance(pydantic_model, dict) else {}

    return to_dynamodb_safe(data)


# ===== AWS MODEL ID SANITIZATION =====

# Regional inference profile prefixes that must be stripped for Bedrock Converse API
INFERENCE_PROFILE_PREFIXES = ("apac.", "na.", "eu.")


def sanitize_bedrock_model_id(model_id: str) -> str:
    """Normalize Bedrock model identifiers for Converse/ConverseStream APIs.

    Strips regional inference profile prefixes like "apac.", "na.", "eu." that are
    not accepted as modelId in Bedrock Converse/ConverseStream API.

    Args:
        model_id: Raw Bedrock model identifier

    Returns:
        Sanitized model identifier suitable for Converse API

    Examples:
        >>> sanitize_bedrock_model_id("apac.anthropic.claude-3-5-sonnet-20240620-v1:0")
        "anthropic.claude-3-5-sonnet-20240620-v1:0"

        >>> sanitize_bedrock_model_id("anthropic.claude-3-haiku-20240307-v1:0")
        "anthropic.claude-3-haiku-20240307-v1:0"
    """
    if not model_id:
        return model_id

    for prefix in INFERENCE_PROFILE_PREFIXES:
        if model_id.startswith(prefix):
            sanitized = model_id[len(prefix):]
            logger.debug(f"Stripped prefix '{prefix}' from model ID: {model_id} -> {sanitized}")
            return sanitized

    return model_id


# ===== EXPORTS =====

__all__ = [
    'get_current_timestamp',
    'serialize_datetime',
    'to_dynamodb_safe',
    'model_dump_dynamodb_safe',
    'sanitize_bedrock_model_id',
    'INFERENCE_PROFILE_PREFIXES',
]
