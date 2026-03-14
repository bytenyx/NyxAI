"""Strategy matching skill for DecideAgent.

This skill matches root causes to appropriate recovery strategies.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.types import AgentRole
from nyxai.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus


class StrategyMatchingSkillConfig(SkillConfig):
    """Configuration for StrategyMatchingSkill.

    Attributes:
        max_actions: Maximum number of actions to generate.
        prioritize_builtin: Whether to prioritize built-in strategies.
        match_threshold: Minimum match score for strategy selection.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_actions = kwargs.get("max_actions", 3)
        self.prioritize_builtin = kwargs.get("prioritize_builtin", True)
        self.match_threshold = kwargs.get("match_threshold", 0.6)


class StrategyMatchingSkill(Skill):
    """Skill for matching root causes to recovery strategies.

    This skill analyzes root causes and generates appropriate
recovery actions using strategy matching.
    """

    def __init__(self, config: StrategyMatchingSkillConfig | None = None) -> None:
        """Initialize the strategy matching skill.

        Args:
            config: Skill configuration.
        """
        super().__init__(config or StrategyMatchingSkillConfig())
        self._matching_config = config or StrategyMatchingSkillConfig()

    @property
    def name(self) -> str:
        """Get skill name."""
        return "strategy_matching"

    @property
    def description(self) -> str:
        """Get skill description."""
        return "Matches root causes to appropriate recovery strategies"

    @property
    def agent_role(self) -> AgentRole:
        """Get target agent role."""
        return AgentRole.DECIDE

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute strategy matching.

        Args:
            context: Skill execution context.

        Returns:
            Skill execution result with matched strategies.
        """
        start_time = time.time()
        self._set_status(SkillStatus.RUNNING)

        try:
            # Get input data
            root_causes = context.input_data.get("root_causes", [])
            service_id = context.input_data.get("service_id", "unknown")

            if not root_causes:
                self._set_status(SkillStatus.SKIPPED)
                return SkillResult.skipped_result(
                    reason="No root causes to match strategies",
                    skill_name=self.name,
                )

            # Match strategies for each root cause
            all_actions = []
            for cause in root_causes:
                actions = self._match_strategies(cause, service_id)
                all_actions.extend(actions)

            # Sort by match score and limit
            all_actions.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            limited_actions = all_actions[: self._matching_config.max_actions]

            self._set_status(SkillStatus.SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return SkillResult.success_result(
                data={
                    "service_id": service_id,
                    "actions": limited_actions,
                    "action_count": len(limited_actions),
                    "root_causes_analyzed": len(root_causes),
                },
                skill_name=self.name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(SkillStatus.FAILED)
            return SkillResult.failure_result(
                error=f"Strategy matching failed: {str(e)}",
                skill_name=self.name,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _match_strategies(
        self,
        root_cause: dict[str, Any],
        service_id: str,
    ) -> list[dict[str, Any]]:
        """Match strategies for a root cause.

        Args:
            root_cause: Root cause data.
            service_id: Affected service ID.

        Returns:
            List of matched actions.
        """
        actions = []

        cause_type = root_cause.get("cause_type", "unknown")

        # Map cause types to strategies
        cause_to_strategy = {
            "service_status": [
                {
                    "action_type": "restart",
                    "description": "Restart the affected service",
                    "match_score": 0.9,
                },
                {
                    "action_type": "health_check",
                    "description": "Perform health check",
                    "match_score": 0.7,
                },
            ],
            "upstream_failure": [
                {
                    "action_type": "circuit_breaker",
                    "description": "Enable circuit breaker",
                    "match_score": 0.85,
                },
                {
                    "action_type": "failover",
                    "description": "Switch to backup service",
                    "match_score": 0.8,
                },
            ],
            "resource_exhaustion": [
                {
                    "action_type": "scale_up",
                    "description": "Scale up resources",
                    "match_score": 0.9,
                },
                {
                    "action_type": "throttle",
                    "description": "Apply rate limiting",
                    "match_score": 0.75,
                },
            ],
            "high_latency": [
                {
                    "action_type": "cache_warmup",
                    "description": "Warm up caches",
                    "match_score": 0.8,
                },
                {
                    "action_type": "optimize",
                    "description": "Optimize queries",
                    "match_score": 0.75,
                },
            ],
        }

        strategies = cause_to_strategy.get(cause_type, [])

        for strategy in strategies:
            if strategy["match_score"] >= self._matching_config.match_threshold:
                actions.append({
                    **strategy,
                    "target_service": service_id,
                    "root_cause": root_cause,
                    "requires_approval": strategy["match_score"] < 0.85,
                })

        return actions

    def can_execute(self, context: SkillContext) -> bool:
        """Check if skill can execute.

        Args:
            context: Execution context.

        Returns:
            True if skill can execute.
        """
        if not super().can_execute(context):
            return False

        # Check for required input data
        return "root_causes" in context.input_data
