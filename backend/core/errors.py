"""
Standardized error handling and exceptions for the TRA system.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TRAError(Exception):
    """Base exception class for TRA system errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TRAError):
    """Raised when data validation fails."""


class NotFoundError(TRAError):
    """Raised when a requested resource is not found."""


class PermissionError(TRAError):
    """Raised when user lacks permission for an operation."""


class ServiceUnavailableError(TRAError):
    """Raised when an external service is unavailable."""


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = True
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def handle_error(error: Exception, context: str = "") -> ErrorResponse:
    """
    Convert various error types to standardized error responses.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
    
    Returns:
        Standardized error response
    """
    if isinstance(error, TRAError):
        logger.error(f"{context}: {error.message}", extra={"error_code": error.error_code, "details": error.details})
        return ErrorResponse(
            message=error.message,
            error_code=error.error_code,
            details=error.details
        )
    
    elif isinstance(error, HTTPException):
        logger.error(f"{context}: HTTP {error.status_code}: {error.detail}")
        return ErrorResponse(
            message=str(error.detail),
            error_code=f"HTTP_{error.status_code}"
        )
    
    else:
        # Generic error handling
        error_msg = str(error) if str(error) else "An unexpected error occurred"
        logger.error(f"{context}: {error_msg}", exc_info=True)
        return ErrorResponse(
            message="An internal error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            details={"original_error": error_msg} if error_msg else None
        )


def raise_http_error(error: TRAError) -> None:
    """
    Convert TRAError to appropriate HTTPException.
    
    Args:
        error: The TRA error to convert
    
    Raises:
        HTTPException: Appropriate HTTP exception
    """
    if isinstance(error, NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message
        )
    elif isinstance(error, PermissionError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.message
        )
    elif isinstance(error, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.message
        )
    elif isinstance(error, ServiceUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error.message
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.message
        )


def log_error(error: Exception, context: str = "", user_id: str = None, session_id: str = None):
    """
    Log error with additional context information.
    
    Args:
        error: The exception that occurred
        context: Description of where/when the error occurred
        user_id: ID of the user involved (if applicable)
        session_id: Session ID where error occurred (if applicable)
    """
    extra_info = {}
    if user_id:
        extra_info["user_id"] = user_id
    if session_id:
        extra_info["session_id"] = session_id
    
    if isinstance(error, TRAError):
        extra_info.update({
            "error_code": error.error_code,
            "error_details": error.details
        })
    
    logger.error(
        f"TRA System Error - {context}: {str(error)}",
        extra=extra_info,
        exc_info=True
    )