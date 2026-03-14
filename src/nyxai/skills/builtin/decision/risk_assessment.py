"""Risk assessment skill for DecideAgent.

This skill assesses the risk of recovery actions.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.types import AgentRole
from nyxai.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus


class RiskAssessmentSkillConfig(SkillConfig):
    """Configuration for RiskAssessmentSkill.

    Attributes:
        auto_approve_threshold: Risk score threshold for auto-approval.
        critical_service_threshold: Additional threshold for critical services.
        require_approval_for_critical: Whether to require approval for critical services.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.auto_approve_threshold = kwargs.get("auto_approve_threshold", 0.3)
        self.critical_service_threshold = kwargs.get("critical_service_threshold", 0.2)
        self.require_approval_for_critical = kwargs.get("require_approval_for_critical", True)


class RiskAssessmentSkill(Skill):
    """Skill for assessing risk of recovery actions.

    This skill evaluates the risk level of proposed recovery actions
and determines if they require approval.
    """

    def __init__(self, config: RiskAssessmentSkillConfig | None = None) -> None:
        """Initialize the risk assessment skill.

        Args:
            config: Skill configuration.
        """
        super().__init__(config or RiskAssessmentSkillConfig())
        self._risk_config = config or RiskAssessmentSkillConfig()

    @property
    def name(self) -> str:
        """Get skill name."""
        return "risk_assessment"

    @property
    def description(self) -> str:
        """Get skill description."""
        return "Assesses risk of recovery actions and determines approval requirements"

    @property
    def agent_role(self) -> AgentRole:
        """Get target agent role."""
        return AgentRole.DECIDE

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute risk assessment.

        Args:
            context: Skill execution context.

        Returns:
            Skill execution result with risk assessments.
        """
        start_time = time.time()
        self._set_status(SkillStatus.RUNNING)

        try:
            # Get input data
            actions = context.input_data.get("actions", [])
            service_id = context.input_data.get("service_id", "unknown")
            service_criticality = context.input_data.get("service_criticality", "medium")

            if not actions:
                self._set_status(SkillStatus.SKIPPED)
                return SkillResult.skipped_result(
                    reason="No actions to assess",
                    skill_name=self.name,
                )

            # Assess each action
            assessed_actions = []
            for action in actions:
                assessment = self._assess_risk(
                    action=action,
                    service_id=service_id,
                    service_criticality=service_criticality,
                )
                assessed_actions.append({
                    "action": action,
                    "assessment": assessment,
                })

            self._set_status(SkillStatus.SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return SkillResult.success_result(
                data={
                    "service_id": service_id,
                    "assessed_actions": assessed_actions,
                    "action_count": len(assessed_actions),
                    "auto_approved": sum(
                        1 for a in assessed_actions
                        if a["assessment"].get("approved", False)
                    ),
                },
                skill_name=self.name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(SkillStatus.FAILED)
            return SkillResult.failure_result(
                error=f"Risk assessment failed: {str(e)}",
                skill_name=self.name,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _assess_risk(
        self,
        action: dict[str, Any],
        service_id: str,
        service_criticality: str,
    ) -> dict[str, Any]:
        """Assess risk for a single action.

        Args:
            action: Action data.
            service_id: Target service ID.
            service_criticality: Service criticality level.

        Returns:
            Risk assessment result.
        """
        action_type = action.get("action_type", "unknown")

        # Base risk scores for different action types
        base_risk_scores = {
            "restart": 0.3,
            "health_check": 0.1,
            "circuit_breaker": 0.2,
            "failover": 0.4,
            "scale_up": 0.25,
            "throttle": 0.15,
            "cache_warmup": 0.1,
            "optimize": 0.2,
            "rollback": 0.5,
            "custom": 0.4,
        }

        base_risk = base_risk_scores.get(action_type, 0.4)

        # Adjust for service criticality
        criticality_multiplier = {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8,
        }.get(service_criticality, 1.0)

        adjusted_risk = min(base_risk * criticality_multiplier, 1.0)

        # Determine approval requirement
        if service_criticality == "critical" and self._risk_config.require_approval_for_critical:
            approved = adjusted_risk <= self._risk_config.critical_service_threshold
        else:
            approved = adjusted_risk <= self._risk_config.auto_approve_threshold

        # Determine risk level
        if adjusted_risk >= 0.7:
            risk_level = "critical"
        elif adjusted_risk >= 0.5:
            risk_level = "high"
        elif adjusted_risk >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_score": adjusted_risk,
            "risk_level": risk_level,
            "approved": approved,
            "requires_approval": not approved,
            "service_criticality": service_criticality,
            "assessment_factors": {
                "action_type": action_type,
                "base_risk": base_risk,
                "criticality_multiplier": criticality_multiplier,
            },
        }

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
        return "actions" in context.input_data
