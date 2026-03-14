"""Shared types for NyxAI.

This module contains shared types and enums used across the codebase
to avoid circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    """Roles for agents in the system."""

    MONITOR = "monitor"
    ANALYZE = "analyze"
    DECIDE = "decide"
    EXECUTE = "execute"


class AgentStatus(str, Enum):
    """Status of an agent execution."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentContext:
    """Context passed between agents in the workflow.

    Attributes:
        incident_id: Unique identifier for the incident.
        anomaly_data: Data about the detected anomaly.
        service_graph: Service topology information.
        root_causes: Identified root causes.
        recovery_actions: Recommended recovery actions.
        execution_results: Results of executed actions.
        metadata: Additional context metadata.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    incident_id: str
    anomaly_data: dict[str, Any] = field(default_factory=dict)
    service_graph: dict[str, Any] = field(default_factory=dict)
    root_causes: list[dict[str, Any]] = field(default_factory=list)
    recovery_actions: list[dict[str, Any]] = field(default_factory=list)
    execution_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(self, **kwargs: Any) -> None:
        """Update context fields.

        Args:
            **kwargs: Fields to update.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the context.
        """
        return {
            "incident_id": self.incident_id,
            "anomaly_data": self.anomaly_data,
            "service_graph": self.service_graph,
            "root_causes": self.root_causes,
            "recovery_actions": self.recovery_actions,
            "execution_results": self.execution_results,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
