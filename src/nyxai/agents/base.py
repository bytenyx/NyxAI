"""Base classes for NyxAI agents.

This module defines the abstract base classes and data models
for the agent orchestration system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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


@dataclass
class AgentResult:
    """Result of an agent execution.

    Attributes:
        success: Whether the execution was successful.
        data: Result data.
        error: Error message if failed.
        status: Execution status.
        agent_name: Name of the executing agent.
        execution_time_ms: Execution time in milliseconds.
        metadata: Additional result metadata.
    """

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    status: AgentStatus = AgentStatus.IDLE
    agent_name: str = ""
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        data: dict[str, Any],
        agent_name: str = "",
        execution_time_ms: float = 0.0,
    ) -> AgentResult:
        """Create a successful result.

        Args:
            data: Result data.
            agent_name: Name of the agent.
            execution_time_ms: Execution time.

        Returns:
            Successful agent result.
        """
        return cls(
            success=True,
            data=data,
            status=AgentStatus.SUCCESS,
            agent_name=agent_name,
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def failure_result(
        cls,
        error: str,
        agent_name: str = "",
        execution_time_ms: float = 0.0,
    ) -> AgentResult:
        """Create a failed result.

        Args:
            error: Error message.
            agent_name: Name of the agent.
            execution_time_ms: Execution time.

        Returns:
            Failed agent result.
        """
        return cls(
            success=False,
            error=error,
            status=AgentStatus.FAILED,
            agent_name=agent_name,
            execution_time_ms=execution_time_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "status": self.status.value,
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class AgentConfig(BaseModel):
    """Base configuration for agents.

    Attributes:
        name: Human-readable name for the agent.
        role: Role of the agent.
        description: Optional description.
        enabled: Whether the agent is enabled.
        timeout_seconds: Execution timeout in seconds.
        max_retries: Maximum number of retries.
        retry_delay_seconds: Delay between retries.
    """

    name: str = Field(default="BaseAgent", description="Agent name")
    role: AgentRole = Field(default=AgentRole.MONITOR, description="Agent role")
    description: str | None = Field(default=None, description="Agent description")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    timeout_seconds: float = Field(
        default=60.0, ge=1.0, description="Execution timeout"
    )
    max_retries: int = Field(default=3, ge=0, description="Maximum retries")
    retry_delay_seconds: float = Field(
        default=1.0, ge=0.0, description="Retry delay"
    )


class Agent(ABC):
    """Abstract base class for all agents.

    All agents in the system must inherit from this class and implement
the execute() method.

    Attributes:
        config: Agent configuration.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the agent.

        Args:
            config: Agent configuration. Uses defaults if None.
        """
        self.config = config or AgentConfig()
        self._status: AgentStatus = AgentStatus.IDLE

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main logic.

        Args:
            context: Execution context with incident data.

        Returns:
            Result of the execution.
        """
        ...

    def get_name(self) -> str:
        """Get the agent name.

        Returns:
            Agent name.
        """
        return self.config.name

    def get_role(self) -> AgentRole:
        """Get the agent role.

        Returns:
            Agent role.
        """
        return self.config.role

    def get_status(self) -> AgentStatus:
        """Get the current agent status.

        Returns:
            Current status.
        """
        return self._status

    def is_enabled(self) -> bool:
        """Check if the agent is enabled.

        Returns:
            True if agent is enabled.
        """
        return self.config.enabled

    def _set_status(self, status: AgentStatus) -> None:
        """Set the agent status.

        Args:
            status: New status to set.
        """
        self._status = status

    def can_execute(self, context: AgentContext) -> bool:
        """Check if the agent can execute given the context.

        Args:
            context: Execution context.

        Returns:
            True if agent can execute.
        """
        if not self.is_enabled():
            return False

        # Role-specific validation
        role = self.get_role()
        if role == AgentRole.ANALYZE:
            # Analyze agent needs anomaly data
            return bool(context.anomaly_data)
        elif role == AgentRole.DECIDE:
            # Decide agent needs root causes
            return bool(context.root_causes)
        elif role == AgentRole.EXECUTE:
            # Execute agent needs recovery actions
            return bool(context.recovery_actions)

        return True
