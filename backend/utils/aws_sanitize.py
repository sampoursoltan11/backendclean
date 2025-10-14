"""
Utilities for AWS compatibility - DEPRECATED FILE

This file has been consolidated into backend.utils.common
Import from there instead:

    from backend.utils.common import (
        sanitize_bedrock_model_id,
        to_dynamodb_safe,
        model_dump_dynamodb_safe,
        INFERENCE_PROFILE_PREFIXES
    )

This file remains for backward compatibility only.
"""

from .common import (
    sanitize_bedrock_model_id,
    to_dynamodb_safe,
    model_dump_dynamodb_safe,
    INFERENCE_PROFILE_PREFIXES
)

__all__ = [
    'sanitize_bedrock_model_id',
    'to_dynamodb_safe',
    'model_dump_dynamodb_safe',
    'INFERENCE_PROFILE_PREFIXES',
]
