"""
Utilities for AWS compatibility:
- Bedrock model ID sanitation (strip unsupported inference profile prefixes)
- DynamoDB-safe JSON serialization (convert float->Decimal, datetime->ISO strings)
"""

from __future__ import annotations

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Mapping, MutableMapping


INFERENCE_PROFILE_PREFIXES = (
    "apac.",
    "na.",
    "eu.",
)


def sanitize_bedrock_model_id(model_id: str) -> str:
    """Normalize Bedrock model identifiers for Converse/ConverseStream.

    Strips regional inference profile prefixes like "apac." that are not accepted
    as modelId in Converse/ConverseStream API. Returns the sanitized model id.
    """
    if not model_id:
        return model_id
    for prefix in INFERENCE_PROFILE_PREFIXES:
        if model_id.startswith(prefix):
            return model_id[len(prefix):]
    return model_id


def to_dynamodb_safe(value: Any) -> Any:
    """Recursively convert Python values to DynamoDB-safe types.

    - datetime/date -> ISO 8601 strings
    - float -> Decimal (via string to avoid float precision issues)
    - dict/list -> recursively processed
    - None/bool/int/str -> unchanged
    """
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        # DynamoDB prohibits float; use Decimal constructed from string
        return Decimal(str(value))
    if isinstance(value, Mapping):
        return {k: to_dynamodb_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dynamodb_safe(v) for v in value]
    return value


def model_dump_dynamodb_safe(pydantic_model: Any) -> dict:
    """Dump a Pydantic model to a dict compatible with DynamoDB.

    Uses mode="json" to serialize datetimes, then converts floats to Decimal.
    """
    try:
        data = pydantic_model.model_dump(mode="json")
    except Exception:
        # Fallback for non-pydantic objects
        data = dict(pydantic_model)
    return to_dynamodb_safe(data)
