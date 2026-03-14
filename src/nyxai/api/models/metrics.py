"""Metrics API models for NyxAI.

This module contains Pydantic models for Prometheus metrics-related API requests and responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    """Single metric value with timestamp.

    Attributes:
        timestamp: The timestamp of the metric value.
        value: The metric value.
    """

    timestamp: datetime = Field(..., description="The timestamp of the metric value")
    value: float = Field(..., description="The metric value")


class MetricSeries(BaseModel):
    """Metric series with labels and values.

    Attributes:
        metric: Metric name and labels.
        values: List of metric values for range queries.
        value: Single metric value for instant queries.
    """

    metric: dict[str, str] = Field(..., description="Metric name and labels")
    values: list[MetricValue] | None = Field(
        default=None, description="List of values for range queries"
    )
    value: MetricValue | None = Field(default=None, description="Single value for instant queries")


class QueryResponse(BaseModel):
    """Response model for instant query endpoint.

    Attributes:
        status: Query status (success/error).
        data: Query result data.
        error: Error message if status is error.
        error_type: Error type if status is error.
    """

    status: str = Field(..., description="Query status")
    data: dict[str, Any] = Field(..., description="Query result data")
    error: str | None = Field(default=None, description="Error message")
    error_type: str | None = Field(default=None, description="Error type")


class QueryRangeResponse(BaseModel):
    """Response model for range query endpoint.

    Attributes:
        status: Query status (success/error).
        data: Query result data.
        error: Error message if status is error.
        error_type: Error type if status is error.
    """

    status: str = Field(..., description="Query status")
    data: dict[str, Any] = Field(..., description="Query result data")
    error: str | None = Field(default=None, description="Error message")
    error_type: str | None = Field(default=None, description="Error type")


class LabelsResponse(BaseModel):
    """Response model for labels endpoint.

    Attributes:
        status: Query status (success/error).
        data: List of label names.
        error: Error message if status is error.
    """

    status: str = Field(..., description="Query status")
    data: list[str] = Field(..., description="List of label names")
    error: str | None = Field(default=None, description="Error message")


class LabelValuesResponse(BaseModel):
    """Response model for label values endpoint.

    Attributes:
        status: Query status (success/error).
        data: List of label values.
        error: Error message if status is error.
    """

    status: str = Field(..., description="Query status")
    data: list[str] = Field(..., description="List of label values")
    error: str | None = Field(default=None, description="Error message")


class MetricNamesResponse(BaseModel):
    """Response model for metric names endpoint.

    Attributes:
        status: Query status (success/error).
        data: List of metric names.
        error: Error message if status is error.
    """

    status: str = Field(..., description="Query status")
    data: list[str] = Field(..., description="List of metric names")
    error: str | None = Field(default=None, description="Error message")


class QueryRequest(BaseModel):
    """Request model for instant query.

    Attributes:
        query: PromQL query string.
        time: Optional timestamp for the query.
        timeout: Query timeout.
    """

    query: str = Field(..., min_length=1, description="PromQL query string")
    time: datetime | None = Field(default=None, description="Optional timestamp for the query")
    timeout: str | None = Field(default=None, description="Query timeout")


class QueryRangeRequest(BaseModel):
    """Request model for range query.

    Attributes:
        query: PromQL query string.
        start: Start time for the query range.
        end: End time for the query range.
        step: Query resolution step width.
        timeout: Query timeout.
    """

    query: str = Field(..., min_length=1, description="PromQL query string")
    start: datetime = Field(..., description="Start time for the query range")
    end: datetime = Field(..., description="End time for the query range")
    step: str = Field(default="15s", description="Query resolution step width (e.g., '1m', '5m')")
    timeout: str | None = Field(default=None, description="Query timeout")


class SeriesRequest(BaseModel):
    """Request model for series query.

    Attributes:
        match: List of series selectors.
        start: Optional start time.
        end: Optional end time.
    """

    match: list[str] = Field(..., description="List of series selectors")
    start: datetime | None = Field(default=None, description="Optional start time")
    end: datetime | None = Field(default=None, description="Optional end time")
