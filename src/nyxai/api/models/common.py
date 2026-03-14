"""Common API models for NyxAI.

This module contains shared Pydantic models used across multiple API endpoints.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper.

    Attributes:
        success: Whether the request was successful.
        data: The response data.
        message: Optional message describing the result.
        timestamp: Response timestamp.
    """

    success: bool = Field(default=True, description="Whether the request was successful")
    data: T | None = Field(default=None, description="The response data")
    message: str | None = Field(default=None, description="Optional message describing the result")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model.

    Attributes:
        success: Always False for error responses.
        error_code: Machine-readable error code.
        message: Human-readable error message.
        details: Additional error details.
        timestamp: Error timestamp.
    """

    success: bool = Field(default=False, description="Always False for error responses")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Overall health status (healthy, unhealthy, degraded).
        version: Application version.
        timestamp: Check timestamp.
        checks: Detailed health check results.
    """

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    checks: dict[str, Any] = Field(
        default_factory=dict, description="Detailed health check results"
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints.

    Attributes:
        page: Page number (1-based).
        page_size: Number of items per page.
    """

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries.

        Returns:
            The offset value.
        """
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper.

    Attributes:
        items: List of items for the current page.
        total: Total number of items.
        page: Current page number.
        page_size: Items per page.
        total_pages: Total number of pages.
    """

    items: list[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
