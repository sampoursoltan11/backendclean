"""
AWS Bedrock helpers for model identifier handling.

This module provides utilities for correctly handling Bedrock model identifiers
across different API contexts:

1. Converse/ConverseStream API: Requires plain model IDs without regional prefixes
   - Example: "anthropic.claude-3-5-sonnet-20240620-v1:0"

2. Knowledge Bases/RetrieveAndGenerate: May use regional inference profiles
   - Example: "apac.anthropic.claude-3-5-sonnet-20240620-v1:0" 

The module offers helper functions to ensure model IDs are properly sanitized
for each specific API context, including stripping regional prefixes where needed
and providing fallbacks for invalid configurations.

Note: Invalid model identifiers will cause Bedrock API operations to fail with
ValidationException: "The provided model identifier is invalid".
"""

import logging
from typing import Optional, Tuple, List
from .common import sanitize_bedrock_model_id, INFERENCE_PROFILE_PREFIXES

logger = logging.getLogger(__name__)

def _default_model_for_region(region: str) -> str:
    """Return a conservative default model id known to be generally available.

    Using Claude 3 Haiku which is more readily available without inference profile
    requirements and provides good performance for TRA use cases.
    """
    # Region is not currently used to vary the id, but we keep it for future mapping.
    return "anthropic.claude-3-haiku-20240307-v1:0"


def sanitize_converse_model_id(raw_id: Optional[str], region: str) -> str:
    """Sanitize a configured model identifier for use with Converse/ConverseStream.

    Accepts:
    - Foundation model ids like "anthropic.claude-3-5-sonnet-20240620-v1:0" (passes through)
    - Regional inference profile ids like "apac.anthropic.claude-3-5-sonnet-20240620-v1:0"
      (strips the leading "apac." prefix)
    - Full ARNs (foundation model or inference profile). For ARNs we cannot safely
      use them with Converse modelId directly, so we fall back to a default.

    Returns a plain foundation model id suitable for Converse APIs.
    """
    if not raw_id:
        fallback = _default_model_for_region(region)
        logger.warning(
            f"No Bedrock model id configured for Converse. Falling back to {fallback}."
        )
        return fallback

    rid = raw_id.strip()
    
    logger.info(f"Sanitizing Bedrock model ID from '{rid}' for Converse API")

    # If an ARN is provided, choose a safe default (Converse expects modelId string).
    if rid.startswith("arn:aws:bedrock:"):
        fallback = _default_model_for_region(region)
        logger.warning(
            "Bedrock model configured as ARN for Converse usage; using default modelId %s",
            fallback,
        )
        return fallback

    # Strip known regional inference profile prefixes like "apac." or "na.".
    if "." in rid:
        # If it looks like "apac.anthropic.claude-3-5-sonnet...", remove the first segment
        first, rest = rid.split(".", 1)
        if first.lower() in {"apac", "na", "eu"} and rest.startswith("anthropic."):
            sanitized_id = rest
            logger.info(f"Removed regional prefix '{first}.' from model ID, using '{sanitized_id}'")
            return sanitized_id

    # Otherwise assume it's already a valid model id
    logger.info(f"Using model ID as-is: '{rid}'")
    return rid


# sanitize_bedrock_model_id is now imported from backend.utils.common


def get_converse_model_id(configured_id: Optional[str], region: str, override: Optional[str] = None) -> str:
    """Resolve the Converse model id using optional override and sanitization."""
    if override:
        return sanitize_converse_model_id(override, region)
    
    result = sanitize_converse_model_id(configured_id, region)
    logger.info(f"Final Converse model ID: '{result}'")
    return result
