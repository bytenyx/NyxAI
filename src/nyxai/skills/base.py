"""Base classes for NyxAI skills.

This module defines the abstract base classes and data models
for the skill system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from nyxai.types import AgentContext, AgentRole


class SkillStatus(str, Enum):
    """Status of a skill execution."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SkillContext:
    """Context passed to skill execution.

    Attributes:
        agent_context: Original agent execution context.
        skill_config: Skill-specific configuration.
        input_data: Input data for the skill.
        metadata: Additional metadata.
        execution_id: Unique execution identifier.
        started_at: Execution start timestamp.
    """

    agent_context: AgentContext
    skill_config: dict[str, Any] = field(default_factory=dict)
    input_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the context.
        """
        return {
            "agent_context": self.agent_context.to_dict(),
            "skill_config": self.skill_config,
            "input_data": self.input_data,
            "metadata": self.metadata,
            "execution_id": self.execution_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


@dataclass
class SkillResult:
    """Result of a skill execution.

    Attributes:
        success: Whether the execution was successful.
        data: Result data.
        error: Error message if failed.
        status: Execution status.
        skill_name: Name of the executing skill.
        execution_time_ms: Execution time in milliseconds.
        metadata: Additional result metadata.
    """

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    status: SkillStatus = SkillStatus.IDLE
    skill_name: str = ""
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        data: dict[str, Any],
        skill_name: str = "",
        execution_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> SkillResult:
        """Create a successful result.

        Args:
            data: Result data.
            skill_name: Name of the skill.
            execution_time_ms: Execution time.
            metadata: Additional metadata.

        Returns:
            Successful skill result.
        """
        return cls(
            success=True,
            data=data,
            status=SkillStatus.SUCCESS,
            skill_name=skill_name,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        error: str,
        skill_name: str = "",
        execution_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> SkillResult:
        """Create a failed result.

        Args:
            error: Error message.
            skill_name: Name of the skill.
            execution_time_ms: Execution time.
            metadata: Additional metadata.

        Returns:
            Failed skill result.
        """
        return cls(
            success=False,
            error=error,
            status=SkillStatus.FAILED,
            skill_name=skill_name,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
        )

    @classmethod
    def skipped_result(
        cls,
        reason: str,
        skill_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> SkillResult:
        """Create a skipped result.

        Args:
            reason: Reason for skipping.
            skill_name: Name of the skill.
            metadata: Additional metadata.

        Returns:
            Skipped skill result.
        """
        return cls(
            success=True,
            data={"skipped": True, "reason": reason},
            status=SkillStatus.SKIPPED,
            skill_name=skill_name,
            execution_time_ms=0.0,
            metadata=metadata or {},
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
            "skill_name": self.skill_name,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class SkillConfig(BaseModel):
    """Base configuration for skills.

    Attributes:
        enabled: Whether the skill is enabled.
        timeout_seconds: Execution timeout in seconds.
        max_retries: Maximum number of retries.
        retry_delay_seconds: Delay between retries.
        custom_params: Custom skill-specific parameters.
    """

    model_config = {"extra": "allow"}

    enabled: bool = Field(default=True, description="Whether skill is enabled")
    timeout_seconds: float = Field(
        default=60.0, ge=1.0, description="Execution timeout"
    )
    max_retries: int = Field(default=3, ge=0, description="Maximum retries")
    retry_delay_seconds: float = Field(
        default=1.0, ge=0.0, description="Retry delay"
    )
    custom_params: dict[str, Any] = Field(
        default_factory=dict, description="Custom parameters"
    )


class Skill(ABC):
    """Abstract base class for all skills.

    All skills in the system must inherit from this class and implement
    the execute() method.

    Attributes:
        config: Skill configuration.
    """

    def __init__(self, config: SkillConfig | None = None) -> None:
        """Initialize the skill.

        Args:
            config: Skill configuration. Uses defaults if None.
        """
        self.config = config or SkillConfig()
        self._status: SkillStatus = SkillStatus.IDLE

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the skill name.

        Returns:
            Skill name.
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the skill description.

        Returns:
            Skill description.
        """
        ...

    @property
    @abstractmethod
    def agent_role(self) -> AgentRole:
        """Get the target agent role for this skill.

        Returns:
            Agent role that can use this skill.
        """
        ...

    @property
    def version(self) -> str:
        """Get the skill version.

        Returns:
            Skill version string.
        """
        return "1.0.0"

    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill's main logic.

        Args:
            context: Execution context with input data.

        Returns:
            Result of the execution.
        """
        ...

    def can_execute(self, context: SkillContext) -> bool:
        """Check if the skill can execute given the context.

        Args:
            context: Execution context.

        Returns:
            True if skill can execute.
        """
        if not self.is_enabled():
            return False

        # Role validation - skill can only be used by matching agent role
        if context.agent_context.metadata.get("agent_role") != self.agent_role.value:
            return False

        return True

    def is_enabled(self) -> bool:
        """Check if the skill is enabled.

        Returns:
            True if skill is enabled.
        """
        return self.config.enabled

    def get_status(self) -> SkillStatus:
        """Get the current skill status.

        Returns:
            Current status.
        """
        return self._status

    def _set_status(self, status: SkillStatus) -> None:
        """Set the skill status.

        Args:
            status: New status to set.
        """
        self._status = status

    def to_dict(self) -> dict[str, Any]:
        """Convert skill info to dictionary.

        Returns:
            Dictionary with skill information.
        """
        return {
            "name": self.name,
            "description": self.description,
            "agent_role": self.agent_role.value,
            "version": self.version,
            "enabled": self.is_enabled(),
            "status": self._status.value,
        }
