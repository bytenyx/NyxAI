"""Base classes for NyxAI agents.

This module defines the abstract base classes and data models
for the agent orchestration system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from nyxai.types import AgentContext, AgentRole, AgentStatus


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
        skills: List of skill names to enable for this agent.
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
    skills: list[str] = Field(
        default_factory=list, description="List of enabled skill names"
    )


class Agent(ABC):
    """Abstract base class for all agents.

    All agents in the system must inherit from this class and implement
the execute() method.

    Attributes:
        config: Agent configuration.
        _skills: Dictionary of registered skills.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the agent.

        Args:
            config: Agent configuration. Uses defaults if None.
        """
        self.config = config or AgentConfig()
        self._status: AgentStatus = AgentStatus.IDLE
        self._skills: dict[str, Any] = {}

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

    # Skills management methods

    def register_skill(self, skill: Any) -> None:
        """Register a skill with this agent.

        Args:
            skill: Skill instance to register.

        Raises:
            ValueError: If skill is not compatible with this agent's role.
        """
        from nyxai.skills.base import Skill

        if not isinstance(skill, Skill):
            raise ValueError("Skill must be an instance of Skill")

        if skill.agent_role != self.get_role():
            raise ValueError(
                f"Skill '{skill.name}' is for role '{skill.agent_role.value}', "
                f"but agent '{self.get_name()}' has role '{self.get_role().value}'"
            )

        self._skills[skill.name] = skill

    def unregister_skill(self, skill_name: str) -> bool:
        """Unregister a skill.

        Args:
            skill_name: Name of skill to unregister.

        Returns:
            True if skill was unregistered, False if not found.
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            return True
        return False

    def get_skill(self, skill_name: str) -> Any | None:
        """Get a registered skill by name.

        Args:
            skill_name: Name of the skill.

        Returns:
            Skill instance or None if not found.
        """
        return self._skills.get(skill_name)

    def get_skills(self) -> list[Any]:
        """Get all registered skills.

        Returns:
            List of registered skills.
        """
        return list(self._skills.values())

    def list_skills(self) -> list[str]:
        """List names of all registered skills.

        Returns:
            List of skill names.
        """
        return list(self._skills.keys())

    def has_skill(self, skill_name: str) -> bool:
        """Check if a skill is registered.

        Args:
            skill_name: Name of the skill.

        Returns:
            True if skill is registered.
        """
        return skill_name in self._skills

    async def execute_skill(
        self,
        skill_name: str,
        context: AgentContext,
        skill_config: dict[str, Any] | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a specific skill.

        Args:
            skill_name: Name of skill to execute.
            context: Agent execution context.
            skill_config: Optional skill-specific configuration.
            input_data: Optional input data for the skill.

        Returns:
            Skill execution result.
        """
        import time
        import uuid

        from nyxai.skills.base import SkillContext, SkillResult

        skill = self._skills.get(skill_name)
        if skill is None:
            return SkillResult.failure_result(
                error=f"Skill '{skill_name}' is not registered",
                skill_name=skill_name,
            )

        start_time = time.time()

        # Create skill context
        skill_context = SkillContext(
            agent_context=context,
            skill_config=skill_config or {},
            input_data=input_data or {},
            execution_id=str(uuid.uuid4()),
        )

        # Check if skill can execute
        if not skill.can_execute(skill_context):
            from nyxai.skills.base import SkillResult

            return SkillResult.skipped_result(
                reason="Skill cannot execute with current context",
                skill_name=skill_name,
            )

        try:
            # Execute the skill
            result = await skill.execute(skill_context)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return SkillResult.failure_result(
                error=f"Skill execution failed: {str(e)}",
                skill_name=skill_name,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def execute_all_skills(
        self,
        context: AgentContext,
        skill_configs: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Execute all registered skills.

        Args:
            context: Agent execution context.
            skill_configs: Optional mapping of skill names to their configs.

        Returns:
            Dictionary mapping skill names to their results.
        """
        results = {}
        skill_configs = skill_configs or {}

        for skill_name in self._skills:
            config = skill_configs.get(skill_name, {})
            result = await self.execute_skill(skill_name, context, config)
            results[skill_name] = result

        return results

    def load_skills_from_config(self) -> None:
        """Load skills specified in agent configuration.

        This method loads and registers skills listed in the config.skills field.
        """
        from nyxai.skills.registry import SkillRegistry

        registry = SkillRegistry()

        for skill_name in self.config.skills:
            skill = registry.get(skill_name)
            if skill is not None:
                try:
                    self.register_skill(skill)
                except ValueError:
                    # Skip skills that are not compatible with this agent's role
                    continue

    def get_skill_info(self) -> list[dict[str, Any]]:
        """Get information about all registered skills.

        Returns:
            List of dictionaries with skill information.
        """
        return [skill.to_dict() for skill in self._skills.values()]
