"""Topology analysis skill for AnalyzeAgent.

This skill performs root cause analysis using service topology.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.types import AgentRole
from nyxai.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus


class TopologyAnalysisSkillConfig(SkillConfig):
    """Configuration for TopologyAnalysisSkill.

    Attributes:
        max_hops: Maximum number of hops to traverse in topology.
        include_downstream: Whether to include downstream services.
        min_confidence: Minimum confidence threshold for root causes.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_hops = kwargs.get("max_hops", 3)
        self.include_downstream = kwargs.get("include_downstream", False)
        self.min_confidence = kwargs.get("min_confidence", 0.5)


class TopologyAnalysisSkill(Skill):
    """Skill for analyzing root causes using service topology.

    This skill traverses the service topology graph to identify
potential root causes of anomalies.
    """

    def __init__(self, config: TopologyAnalysisSkillConfig | None = None) -> None:
        """Initialize the topology analysis skill.

        Args:
            config: Skill configuration.
        """
        super().__init__(config or TopologyAnalysisSkillConfig())
        self._topology_config = config or TopologyAnalysisSkillConfig()

    @property
    def name(self) -> str:
        """Get skill name."""
        return "topology_analysis"

    @property
    def description(self) -> str:
        """Get skill description."""
        return "Analyzes root causes using service topology graph"

    @property
    def agent_role(self) -> AgentRole:
        """Get target agent role."""
        return AgentRole.ANALYZE

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute topology analysis.

        Args:
            context: Skill execution context.

        Returns:
            Skill execution result with identified root causes.
        """
        start_time = time.time()
        self._set_status(SkillStatus.RUNNING)

        try:
            # Get input data
            service_id = context.input_data.get("service_id", "unknown")
            service_graph = context.input_data.get("service_graph", {})
            anomalies = context.input_data.get("anomalies", [])

            if not service_graph:
                self._set_status(SkillStatus.SKIPPED)
                return SkillResult.skipped_result(
                    reason="No service graph available for analysis",
                    skill_name=self.name,
                )

            # Analyze topology
            root_causes = self._analyze_topology(
                service_id=service_id,
                service_graph=service_graph,
                anomalies=anomalies,
            )

            # Filter by confidence
            filtered_causes = [
                c for c in root_causes
                if c.get("confidence", 0) >= self._topology_config.min_confidence
            ]

            # Sort by confidence
            filtered_causes.sort(key=lambda x: x.get("confidence", 0), reverse=True)

            self._set_status(SkillStatus.SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return SkillResult.success_result(
                data={
                    "service_id": service_id,
                    "root_causes": filtered_causes,
                    "cause_count": len(filtered_causes),
                    "analysis_method": "topology",
                },
                skill_name=self.name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(SkillStatus.FAILED)
            return SkillResult.failure_result(
                error=f"Topology analysis failed: {str(e)}",
                skill_name=self.name,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _analyze_topology(
        self,
        service_id: str,
        service_graph: dict[str, Any],
        anomalies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Analyze service topology for root causes.

        Args:
            service_id: ID of the affected service.
            service_graph: Service topology graph data.
            anomalies: List of detected anomalies.

        Returns:
            List of identified root causes.
        """
        causes = []

        # Get upstream services
        upstream = service_graph.get("upstream", {})
        services = service_graph.get("services", {})

        # Check current service status
        current_service = services.get(service_id, {})
        if current_service.get("status") in ["unhealthy", "degraded"]:
            causes.append({
                "service_id": service_id,
                "service_name": current_service.get("name", service_id),
                "cause_type": "service_status",
                "confidence": 0.8,
                "hops": 0,
                "description": f"Service {service_id} is {current_service.get('status')}",
                "metrics": current_service.get("metrics", {}),
            })

        # Check upstream services
        for upstream_id, hops in upstream.items():
            if hops > self._topology_config.max_hops:
                continue

            upstream_service = services.get(upstream_id, {})
            if upstream_service.get("status") in ["unhealthy", "degraded"]:
                # Calculate confidence based on distance
                confidence = max(0.9 - (hops * 0.1), 0.5)

                causes.append({
                    "service_id": upstream_id,
                    "service_name": upstream_service.get("name", upstream_id),
                    "cause_type": "upstream_failure",
                    "confidence": confidence,
                    "hops": hops,
                    "description": f"Upstream service {upstream_id} is {upstream_service.get('status')}",
                    "metrics": upstream_service.get("metrics", {}),
                })

        return causes

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
        return "service_id" in context.input_data
