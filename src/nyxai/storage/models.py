"""Database models for NyxAI.

This module defines SQLAlchemy ORM models for anomaly detection,
incident management, and recovery actions.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nyxai.storage.database import Base


class AnomalyStatus(str, PyEnum):
    """Status of an anomaly detection event."""

    DETECTED = "detected"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class AnomalySeverity(str, PyEnum):
    """Severity level of an anomaly."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, PyEnum):
    """Status of an incident."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, PyEnum):
    """Severity level of an incident."""

    P4 = "p4"  # Low
    P3 = "p3"  # Medium
    P2 = "p2"  # High
    P1 = "p1"  # Critical


class RecoveryActionStatus(str, PyEnum):
    """Status of a recovery action."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Anomaly(Base):
    """Anomaly detection event model.

    Represents a detected anomaly in the monitored system.

    Attributes:
        id: Unique identifier (UUID).
        metric_name: Name of the metric that triggered the anomaly.
        metric_labels: Labels/tags associated with the metric (JSON).
        detected_at: Timestamp when the anomaly was detected.
        resolved_at: Timestamp when the anomaly was resolved (if applicable).
        status: Current status of the anomaly.
        severity: Severity level of the anomaly.
        confidence: Confidence score of the detection (0-1).
        value: The anomalous metric value.
        expected_value: The expected/normal value.
        algorithm: The detection algorithm used.
        description: Human-readable description of the anomaly.
        root_cause: Identified root cause (if available).
        metadata: Additional metadata (JSON).
        incident_id: Foreign key to associated incident.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__ = "anomalies"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    metric_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    metric_labels: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[AnomalyStatus] = mapped_column(
        Enum(AnomalyStatus),
        default=AnomalyStatus.DETECTED,
        nullable=False,
    )
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity),
        default=AnomalySeverity.MEDIUM,
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )
    value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    expected_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    incident: Mapped["Incident | None"] = relationship(
        "Incident",
        back_populates="anomalies",
        foreign_keys=[incident_id],
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<Anomaly(id={self.id}, "
            f"metric={self.metric_name}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )


class Incident(Base):
    """Incident model for tracking system issues.

    Represents a system incident that may be composed of multiple anomalies.

    Attributes:
        id: Unique identifier (UUID).
        title: Short title of the incident.
        description: Detailed description of the incident.
        status: Current status of the incident.
        severity: Severity level of the incident.
        started_at: Timestamp when the incident started.
        detected_at: Timestamp when the incident was detected.
        resolved_at: Timestamp when the incident was resolved.
        closed_at: Timestamp when the incident was closed.
        root_cause: Identified root cause.
        impact_summary: Summary of the impact.
        affected_services: List of affected services (JSON).
        metadata: Additional metadata (JSON).
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity),
        default=IncidentSeverity.P3,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    impact_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    affected_services: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
    )
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    anomalies: Mapped[list["Anomaly"]] = relationship(
        "Anomaly",
        back_populates="incident",
        foreign_keys="Anomaly.incident_id",
    )
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(
        "RecoveryAction",
        back_populates="incident",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<Incident(id={self.id}, "
            f"title={self.title}, "
            f"severity={self.severity}, "
            f"status={self.status})>"
        )


class RecoveryAction(Base):
    """Recovery action model for automated remediation.

    Represents an action taken to recover from an incident.

    Attributes:
        id: Unique identifier (UUID).
        incident_id: Foreign key to the associated incident.
        action_type: Type of recovery action.
        action_name: Human-readable name of the action.
        description: Detailed description of the action.
        status: Current status of the action.
        parameters: Action parameters (JSON).
        result: Action result data (JSON).
        error_message: Error message if action failed.
        executed_at: Timestamp when the action was executed.
        completed_at: Timestamp when the action completed.
        approved_by: User/system that approved the action.
        execution_logs: Execution logs (JSON).
        rollback_action: Reference to rollback action if applicable.
        metadata: Additional metadata (JSON).
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__ = "recovery_actions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    action_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[RecoveryActionStatus] = mapped_column(
        Enum(RecoveryActionStatus),
        default=RecoveryActionStatus.PENDING,
        nullable=False,
        index=True,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    execution_logs: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
    )
    rollback_action_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recovery_actions.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="recovery_actions",
    )
    rollback_action: Mapped["RecoveryAction | None"] = relationship(
        "RecoveryAction",
        remote_side="RecoveryAction.id",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<RecoveryAction(id={self.id}, "
            f"action={self.action_name}, "
            f"status={self.status})>"
        )
