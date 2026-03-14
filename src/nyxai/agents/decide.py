"""Decide Agent for NyxAI.

This module implements the Decide Agent that makes recovery decisions
based on root cause analysis.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.agents.base import Agent, AgentConfig, AgentContext, AgentResult, AgentRole
from nyxai.knowledge_base.incident_kb import IncidentKnowledgeBase
from nyxai.recovery.risk.assessor import RiskAssessor
from nyxai.recovery.strategies.base import RecoveryAction
from nyxai.recovery.strategies.manager import StrategyManager


class DecideAgentConfig(AgentConfig):
    """Configuration for Decide Agent.

    Attributes:
        auto_approve_low_risk: Whether to auto-approve low-risk actions.
        risk_threshold: Risk score threshold for auto-approval.
        max_actions: Maximum number of recovery actions to generate.
        use_knowledge_base: Whether to use knowledge base for decisions.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "DecideAgent"
        self.role = AgentRole.DECIDE
        self.description = "Makes recovery decisions based on root cause analysis"
        self.auto_approve_low_risk = True
        self.risk_threshold = 0.3
        self.max_actions = 3
        self.use_knowledge_base = True


class DecideAgent(Agent):
    """Agent responsible for making recovery decisions.

    This agent analyzes root causes and generates appropriate
    recovery actions using strategies and knowledge base.

    Attributes:
        config: Decide agent configuration.
        _strategy_manager: Manager for recovery strategies.
        _risk_assessor: Risk assessor for actions.
        _knowledge_base: Optional knowledge base for similar incidents.
    """

    def __init__(
        self,
        strategy_manager: StrategyManager,
        risk_assessor: RiskAssessor,
        knowledge_base: IncidentKnowledgeBase | None = None,
        config: DecideAgentConfig | None = None,
    ) -> None:
        """Initialize the decide agent.

        Args:
            strategy_manager: Manager for recovery strategies.
            risk_assessor: Risk assessor for actions.
            knowledge_base: Optional knowledge base.
            config: Agent configuration. Uses defaults if None.
        """
        super().__init__(config or DecideAgentConfig())
        self.decide_config = config or DecideAgentConfig()
        self._strategy_manager = strategy_manager
        self._risk_assessor = risk_assessor
        self._knowledge_base = knowledge_base

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute recovery decision making.

        Args:
            context: Execution context.

        Returns:
            Agent execution result.
        """
        start_time = time.time()
        self._set_status(self.get_status().RUNNING)

        try:
            # Check if we can execute
            if not self.can_execute(context):
                return AgentResult.failure_result(
                    error="Agent cannot execute: no root causes in context",
                    agent_name=self.get_name(),
                )

            root_causes = context.root_causes
            service_id = context.anomaly_data.get("service_id", "unknown")

            if not root_causes:
                return AgentResult.success_result(
                    data={"message": "No root causes to analyze", "actions": []},
                    agent_name=self.get_name(),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Search knowledge base for similar incidents
            similar_solutions = []
            if (
                self.decide_config.use_knowledge_base
                and self._knowledge_base
            ):
                similar_solutions = await self._search_knowledge_base(
                    root_causes, service_id
                )

            # Generate recovery actions
            actions = self._generate_actions(root_causes, service_id, similar_solutions)

            # Assess risk for each action
            assessed_actions = []
            for action in actions:
                # Build context for risk assessment
                risk_context = {
                    "service_criticality": self._get_service_criticality(service_id),
                    "affected_service_count": len(root_causes),
                    "historical_success_rate": 0.9,  # Default
                }

                assessment = self._risk_assessor.assess(action, risk_context)

                # Auto-approve if low risk and enabled
                if (
                    self.decide_config.auto_approve_low_risk
                    and assessment.approved
                ):
                    action.requires_approval = False

                assessed_actions.append({
                    "action": action.to_dict(),
                    "risk_assessment": assessment.to_dict(),
                })

            # Update context with recovery actions
            context.update(recovery_actions=assessed_actions)

            self._set_status(self.get_status().SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult.success_result(
                data={
                    "actions": assessed_actions,
                    "root_causes_analyzed": len(root_causes),
                    "similar_solutions_found": len(similar_solutions),
                    "service_id": service_id,
                },
                agent_name=self.get_name(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(self.get_status().FAILED)
            return AgentResult.failure_result(
                error=f"Decide agent failed: {str(e)}",
                agent_name=self.get_name(),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _generate_actions(
        self,
        root_causes: list[dict[str, Any]],
        service_id: str,
        similar_solutions: list[dict[str, Any]],
    ) -> list[RecoveryAction]:
        """Generate recovery actions based on root causes.

        Args:
            root_causes: List of root causes.
            service_id: Affected service ID.
            similar_solutions: Similar solutions from knowledge base.

        Returns:
            List of recovery actions.
        """
        actions: list[RecoveryAction] = []

        # Map cause types to anomaly types for strategy matching
        cause_to_anomaly = {
            "service_status": "unhealthy",
            "upstream_failure": "dependency_failure",
            "graph_analysis": "unknown",
            "resource_exhaustion": "resource_exhaustion",
            "memory_leak": "memory_leak",
            "high_cpu": "high_cpu",
            "high_latency": "high_latency",
        }

        # Generate actions for each root cause
        for cause in root_causes:
            cause_type = cause.get("cause_type", "unknown")
            anomaly_type = cause_to_anomaly.get(cause_type, cause_type)

            # Create context for strategy matching
            strategy_context = {
                "root_cause": cause,
                "service_id": service_id,
                "similar_solutions": similar_solutions,
            }

            # Find matching strategies
            matching_actions = self._strategy_manager.create_actions(
                anomaly_type=anomaly_type,
                service_id=service_id,
                context=strategy_context,
                max_actions=2,  # Max 2 actions per cause
            )

            actions.extend(matching_actions)

        # Limit total actions
        return actions[: self.decide_config.max_actions]

    async def _search_knowledge_base(
        self,
        root_causes: list[dict[str, Any]],
        service_id: str,
    ) -> list[dict[str, Any]]:
        """Search knowledge base for similar incidents.

        Args:
            root_causes: List of root causes.
            service_id: Affected service ID.

        Returns:
            List of similar solutions.
        """
        if not self._knowledge_base:
            return []

        solutions = []

        # Search by service
        service_incidents = self._knowledge_base.search_by_service(service_id)
        for incident in service_incidents:
            if incident.solution:
                solutions.append({
                    "incident_id": incident.id,
                    "title": incident.title,
                    "solution": incident.solution,
                    "similarity": 0.8,  # High similarity for same service
                })

        # Search by tags
        for cause in root_causes:
            cause_type = cause.get("cause_type", "")
            if cause_type:
                tagged_incidents = self._knowledge_base.search_by_tags([cause_type])
                for incident in tagged_incidents:
                    if incident.solution and incident.id not in [
                        s["incident_id"] for s in solutions
                    ]:
                        solutions.append({
                            "incident_id": incident.id,
                            "title": incident.title,
                            "solution": incident.solution,
                            "similarity": 0.6,
                        })

        # Sort by similarity and return top results
        solutions.sort(key=lambda x: x["similarity"], reverse=True)
        return solutions[:5]

    def _get_service_criticality(self, service_id: str) -> str:
        """Get criticality level for a service.

        Args:
            service_id: Service ID.

        Returns:
            Criticality level (critical, high, medium, low).
        """
        # This could be fetched from a service registry
        # For now, return a default value
        return "medium"
