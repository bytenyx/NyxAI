"""Standardized API response models for NyxAI.

This module provides standardized response wrappers for all API endpoints
to ensure consistent response format across the API.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper.

    All API responses are wrapped in this format for consistency.

    Attributes:
        code: HTTP status code or custom error code
        message: Human-readable message
        data: The actual response data
    """

    code: int = 200
    message: str = "success"
    data: T | None = None


class ErrorResponse(BaseModel):
    """Error response model.

    Attributes:
        code: Error code
        message: Error message
        detail: Additional error details
    """

    code: int
    message: str
    detail: str | None = None


def success_response(data: T, message: str = "success", code: int = 200) -> ApiResponse[T]:
    """Create a success response.

    Args:
        data: The response data
        message: Success message
        code: HTTP status code

    Returns:
        ApiResponse: Wrapped success response
    """
    return ApiResponse(code=code, message=message, data=data)


def error_response(message: str, code: int = 400, detail: str | None = None) -> ErrorResponse:
    """Create an error response.

    Args:
        message: Error message
        code: Error code
        detail: Additional error details

    Returns:
        ErrorResponse: Error response
    """
    return ErrorResponse(code=code, message=message, detail=detail)
