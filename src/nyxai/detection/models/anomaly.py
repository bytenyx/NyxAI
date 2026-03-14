"""Anomaly data models for NyxAI.

This module defines the core data models for representing anomalies,
including severity levels and status tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnomalySeverity(str, Enum):
    """Severity levels for anomalies.

    P0: Critical - Immediate action required
    P1: High - Urgent attention needed
    P2: Medium - Should be addressed soon
    P3: Low - Can be addressed in regular maintenance
    P4: Info - Informational only
    """

    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low
    P4 = "P4"  # Info

    @property
    def priority(self) -> int:
        """Get numeric priority (lower is more severe).

        Returns:
            Numeric priority from 0 (critical) to 4 (info).
        """
        return int(self.value[1])

    @classmethod
    def from_score(cls, score: float) -> AnomalySeverity:
        """Determine severity from anomaly score.

        Args:
            score: Anomaly score between 0.0 and 1.0.

        Returns:
            Appropriate severity level.
        """
        if score >= 0.95:
            return cls.P0
        elif score >= 0.85:
            return cls.P1
        elif score >= 0.70:
            return cls.P2
        elif score >= 0.50:
            return cls.P3
        else:
            return cls.P4


class AnomalyStatus(str, Enum):
    """Status of an anomaly.

    NEW: Newly detected, not yet acknowledged
    ACKNOWLEDGED: Acknowledged by a user
    INVESTIGATING: Currently being investigated
    RESOLVED: Issue has been resolved
    FALSE_POSITIVE: Marked as false positive
    SUPPRESSED: Suppressed to reduce noise
    """

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"


class Anomaly(BaseModel):
    """Anomaly model representing a detected anomaly.

    This model represents a single anomaly event detected by the system.
    It includes metadata about the detection, severity, and current status.

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

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the anomaly",
    )
    title: str = Field(..., description="Short title describing the anomaly")
    description: str | None = Field(default=None, description="Detailed description")
    severity: AnomalySeverity = Field(
        default=AnomalySeverity.P2,
        description="Severity level (P0-P4)",
    )
    status: AnomalyStatus = Field(
        default=AnomalyStatus.NEW,
        description="Current status of the anomaly",
    )
    source_type: str = Field(
        default="unknown",
        description="Type of source (e.g., 'metric', 'log', 'trace')",
    )
    detection_method: str = Field(
        default="unknown",
        description="Method used to detect the anomaly",
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the anomaly was detected",
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="Timestamp when the anomaly was resolved",
    )
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Anomaly score (0.0 to 1.0)",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the detection (0.0 to 1.0)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the anomaly",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of tags for categorization",
    )
    assigned_to: str | None = Field(
        default=None,
        description="User or team assigned to investigate",
    )

    class Config:
        """Pydantic configuration."""

        frozen = False
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @classmethod
    def create(
        cls,
        title: str,
        description: str | None = None,
        severity: AnomalySeverity | None = None,
        source_type: str = "unknown",
        detection_method: str = "unknown",
        score: float = 0.0,
        confidence: float = 0.0,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Anomaly:
        """Create a new anomaly with sensible defaults.

        Args:
            title: Short title describing the anomaly.
            description: Detailed description of the anomaly.
            severity: Severity level. If None, inferred from score.
            source_type: Type of source.
            detection_method: Method used for detection.
            score: Anomaly score.
            confidence: Confidence in detection.
            timestamp: Detection timestamp. Defaults to now.
            metadata: Additional metadata.
            tags: List of tags.

        Returns:
            New Anomaly instance.
        """
        if severity is None:
            severity = AnomalySeverity.from_score(score)

        return cls(
            title=title,
            description=description,
            severity=severity,
            source_type=source_type,
            detection_method=detection_method,
            detected_at=timestamp or datetime.utcnow(),
            score=score,
            confidence=confidence,
            metadata=metadata or {},
            tags=tags or [],
        )

    @classmethod
    def from_score(
        cls,
        score: float,
    ) -> AnomalySeverity:
        """Get severity level from anomaly score.

        Args:
            score: Anomaly score between 0.0 and 1.0.

        Returns:
            Appropriate severity level.
        """
        return AnomalySeverity.from_score(score)

    def resolve(self) -> None:
        """Mark the anomaly as resolved."""
        self.status = AnomalyStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    def acknowledge(self) -> None:
        """Acknowledge the anomaly."""
        if self.status == AnomalyStatus.NEW:
            self.status = AnomalyStatus.ACKNOWLEDGED

    def start_investigation(self) -> None:
        """Mark the anomaly as being investigated."""
        self.status = AnomalyStatus.INVESTIGATING

    def mark_false_positive(self) -> None:
        """Mark the anomaly as a false positive."""
        self.status = AnomalyStatus.FALSE_POSITIVE
        self.resolved_at = datetime.utcnow()

    def suppress(self) -> None:
        """Suppress the anomaly to reduce noise."""
        self.status = AnomalyStatus.SUPPRESSED

    def is_resolved(self) -> bool:
        """Check if the anomaly is resolved.

        Returns:
            True if resolved, False otherwise.
        """
        return self.status in (AnomalyStatus.RESOLVED, AnomalyStatus.FALSE_POSITIVE)

    def is_active(self) -> bool:
        """Check if the anomaly is still active.

        Returns:
            True if active, False otherwise.
        """
        return self.status not in (
            AnomalyStatus.RESOLVED,
            AnomalyStatus.FALSE_POSITIVE,
            AnomalyStatus.SUPPRESSED,
        )

    def update_score(self, score: float, confidence: float | None = None) -> None:
        """Update the anomaly score and optionally confidence.

        Args:
            score: New anomaly score.
            confidence: New confidence value (optional).
        """
        self.score = score
        if confidence is not None:
            self.confidence = confidence
        # Update severity based on new score
        self.severity = AnomalySeverity.from_score(score)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the anomaly.

        Args:
            tag: Tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the anomaly.

        Args:
            tag: Tag to remove.
        """
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> dict[str, Any]:
        """Convert anomaly to dictionary.

        Returns:
            Dictionary representation of the anomaly.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Convert anomaly to JSON string.

        Returns:
            JSON string representation of the anomaly.
        """
        return self.model_dump_json()
