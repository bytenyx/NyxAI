"""Anomaly API models for NyxAI.

This module contains Pydantic models for anomaly-related API requests and responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from nyxai.detection.models.anomaly import AnomalySeverity, AnomalyStatus


class AnomalyResponse(BaseModel):
    """Anomaly response model.

    Attributes:
        id: Unique identifier for the anomaly.
        title: Short title describing the anomaly.
        description: Detailed description of the anomaly.
        severity: Severity level (P0-P4).
        status: Current status of the anomaly.
        source_type: Type of source (e.g., 'metric', 'log', 'trace').
        detection_method: Method used to detect the anomaly.
        detected_at: Timestamp when the anomaly was detected.
        resolved_at: Timestamp when the anomaly was resolved (if applicable).
        score: Anomaly score (0.0 to 1.0).
        confidence: Confidence in the detection (0.0 to 1.0).
        metadata: Additional metadata about the anomaly.
        tags: List of tags for categorization.
        assigned_to: User or team assigned to investigate.
    """

    id: str = Field(..., description="Unique identifier for the anomaly")
    title: str = Field(..., description="Short title describing the anomaly")
    description: str | None = Field(default=None, description="Detailed description")
    severity: AnomalySeverity = Field(..., description="Severity level (P0-P4)")
    status: AnomalyStatus = Field(..., description="Current status of the anomaly")
    source_type: str = Field(..., description="Type of source")
    detection_method: str = Field(..., description="Method used to detect the anomaly")
    detected_at: datetime = Field(..., description="Timestamp when the anomaly was detected")
    resolved_at: datetime | None = Field(default=None, description="Timestamp when resolved")
    score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score (0.0 to 1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the detection")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: list[str] = Field(default_factory=list, description="List of tags for categorization")
    assigned_to: str | None = Field(default=None, description="User or team assigned")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class AnomalyCreateRequest(BaseModel):
    """Request model for creating a new anomaly.

    Attributes:
        title: Short title describing the anomaly.
        description: Detailed description of the anomaly.
        severity: Severity level (P0-P4). If not provided, inferred from score.
        source_type: Type of source.
        detection_method: Method used to detect the anomaly.
        score: Anomaly score (0.0 to 1.0).
        confidence: Confidence in the detection (0.0 to 1.0).
        metadata: Additional metadata about the anomaly.
        tags: List of tags for categorization.
        assigned_to: User or team assigned to investigate.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Short title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    severity: AnomalySeverity | None = Field(default=None, description="Severity level (P0-P4)")
    source_type: str = Field(default="unknown", description="Type of source")
    detection_method: str = Field(default="manual", description="Detection method")
    score: float = Field(default=0.5, ge=0.0, le=1.0, description="Anomaly score")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: list[str] = Field(default_factory=list, description="List of tags")
    assigned_to: str | None = Field(default=None, description="Assigned user or team")


class AnomalyUpdateRequest(BaseModel):
    """Request model for updating an anomaly.

    Attributes:
        title: Short title describing the anomaly.
        description: Detailed description of the anomaly.
        severity: Severity level (P0-P4).
        status: Current status of the anomaly.
        metadata: Additional metadata about the anomaly.
        tags: List of tags for categorization.
        assigned_to: User or team assigned to investigate.
    """

    title: str | None = Field(
        default=None, min_length=1, max_length=200, description="Short title"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    severity: AnomalySeverity | None = Field(default=None, description="Severity level")
    status: AnomalyStatus | None = Field(default=None, description="Current status")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    tags: list[str] | None = Field(default=None, description="List of tags")
    assigned_to: str | None = Field(default=None, description="Assigned user or team")


class AnomalyListResponse(BaseModel):
    """Response model for anomaly list endpoint.

    Attributes:
        items: List of anomalies.
        total: Total number of anomalies matching the query.
        page: Current page number.
        page_size: Number of items per page.
        total_pages: Total number of pages.
    """

    items: list[AnomalyResponse] = Field(..., description="List of anomalies")
    total: int = Field(..., ge=0, description="Total number of anomalies")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class AnomalyFilterParams(BaseModel):
    """Filter parameters for anomaly list endpoint.

    Attributes:
        severity: Filter by severity level.
        status: Filter by status.
        source_type: Filter by source type.
        detection_method: Filter by detection method.
        assigned_to: Filter by assigned user.
        tags: Filter by tags (comma-separated).
        start_date: Filter anomalies detected after this date.
        end_date: Filter anomalies detected before this date.
    """

    severity: AnomalySeverity | None = Field(default=None, description="Filter by severity")
    status: AnomalyStatus | None = Field(default=None, description="Filter by status")
    source_type: str | None = Field(default=None, description="Filter by source type")
    detection_method: str | None = Field(default=None, description="Filter by detection method")
    assigned_to: str | None = Field(default=None, description="Filter by assigned user")
    tags: str | None = Field(default=None, description="Filter by tags (comma-separated)")
    start_date: datetime | None = Field(default=None, description="Filter by start date")
    end_date: datetime | None = Field(default=None, description="Filter by end date")


class AnomalyActionResponse(BaseModel):
    """Response model for anomaly actions (acknowledge, resolve, etc.).

    Attributes:
        success: Whether the action was successful.
        anomaly: The updated anomaly.
        message: Action result message.
    """

    success: bool = Field(..., description="Whether the action was successful")
    anomaly: AnomalyResponse = Field(..., description="The updated anomaly")
    message: str = Field(..., description="Action result message")
