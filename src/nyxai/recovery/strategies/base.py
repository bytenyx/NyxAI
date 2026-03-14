"""Base classes for recovery strategies.

This module defines the abstract base classes and data models
for recovery strategies and actions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of recovery actions."""

    RESTART = "restart"
    SCALE = "scale"
    CLEAR_CACHE = "clear_cache"
    CIRCUIT_BREAKER = "circuit_breaker"
    ROLLBACK = "rollback"
    CONFIG_UPDATE = "config_update"
    ALERT = "alert"
    CUSTOM = "custom"


class ActionStatus(str, Enum):
    """Status of a recovery action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk levels for recovery actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryAction:
    """Represents a recovery action to be executed.

    Attributes:
        id: Unique identifier for the action.
        action_type: Type of recovery action.
        target: Target service or resource.
        parameters: Action-specific parameters.
        risk_level: Risk level of the action.
        estimated_duration: Estimated duration in seconds.
        requires_approval: Whether action requires manual approval.
        status: Current status of the action.
        result: Execution result.
        created_at: Creation timestamp.
        executed_at: Execution timestamp.
        completed_at: Completion timestamp.
        metadata: Additional metadata.
    """

    id: str
    action_type: ActionType
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    estimated_duration: float = 60.0
    requires_approval: bool = False
    status: ActionStatus = ActionStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_executing(self) -> None:
        """Mark the action as in progress."""
        self.status = ActionStatus.IN_PROGRESS
        self.executed_at = datetime.utcnow()

    def mark_success(self, result: dict[str, Any] | None = None) -> None:
        """Mark the action as successfully completed.

        Args:
            result: Execution result data.
        """
        self.status = ActionStatus.SUCCESS
        self.completed_at = datetime.utcnow()
        if result:
            self.result.update(result)

    def mark_failed(self, error: str | None = None) -> None:
        """Mark the action as failed.

        Args:
            error: Error message.
        """
        self.status = ActionStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error:
            self.result["error"] = error

    def mark_rolled_back(self) -> None:
        """Mark the action as rolled back."""
        self.status = ActionStatus.ROLLED_BACK
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the action.
        """
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "target": self.target,
            "parameters": self.parameters,
            "risk_level": self.risk_level.value,
            "estimated_duration": self.estimated_duration,
            "requires_approval": self.requires_approval,
            "status": self.status.value,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


class StrategyConfig(BaseModel):
    """Base configuration for recovery strategies.

    Attributes:
        name: Human-readable name for the strategy.
        description: Optional description.
        enabled: Whether the strategy is enabled.
        priority: Priority of the strategy (higher = more important).
        max_attempts: Maximum number of retry attempts.
        cooldown_seconds: Cooldown period between attempts.
        auto_rollback: Whether to auto-rollback on failure.
    """

    name: str = Field(default="BaseStrategy", description="Strategy name")
    description: str | None = Field(default=None, description="Strategy description")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")
    priority: int = Field(default=50, ge=1, le=100, description="Strategy priority")
    max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    cooldown_seconds: float = Field(default=60.0, ge=0, description="Cooldown period")
    auto_rollback: bool = Field(default=False, description="Auto-rollback on failure")


class RecoveryStrategy(ABC):
    """Abstract base class for recovery strategies.

    All recovery strategies must inherit from this class and implement
    the can_handle() and create_action() methods.

    Attributes:
        config: Strategy configuration.
    """

    def __init__(self, config: StrategyConfig | None = None) -> None:
        """Initialize the recovery strategy.

        Args:
            config: Strategy configuration. Uses defaults if None.
        """
        self.config = config or StrategyConfig()

    @abstractmethod
    def can_handle(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Check if this strategy can handle the given anomaly.

        Args:
            anomaly_type: Type of anomaly detected.
            service_id: ID of the affected service.
            context: Additional context about the anomaly.

        Returns:
            True if this strategy can handle the anomaly.
        """
        ...

    @abstractmethod
    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> RecoveryAction | None:
        """Create a recovery action for the anomaly.

        Args:
            anomaly_type: Type of anomaly detected.
            service_id: ID of the affected service.
            context: Additional context about the anomaly.

        Returns:
            Recovery action to execute, or None if no action needed.
        """
        ...

    def get_priority(self) -> int:
        """Get the strategy priority.

        Returns:
            Priority value (higher = more important).
        """
        return self.config.priority

    def is_enabled(self) -> bool:
        """Check if the strategy is enabled.

        Returns:
            True if strategy is enabled.
        """
        return self.config.enabled

    def get_name(self) -> str:
        """Get the strategy name.

        Returns:
            Strategy name.
        """
        return self.config.name

    def get_description(self) -> str | None:
        """Get the strategy description.

        Returns:
            Strategy description or None.
        """
        return self.config.description
