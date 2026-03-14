"""Analyze Agent for NyxAI.

This module implements the Analyze Agent that performs root cause analysis.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.agents.base import Agent, AgentConfig, AgentContext, AgentResult, AgentRole
from nyxai.llm.providers.base import LLMProvider
from nyxai.rca.topology.service_graph import ServiceGraph


class AnalyzeAgentConfig(AgentConfig):
    """Configuration for Analyze Agent.

    Attributes:
        use_llm: Whether to use LLM for analysis.
        max_root_causes: Maximum number of root causes to identify.
        include_topology_analysis: Whether to include topology analysis.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "AnalyzeAgent"
        self.role = AgentRole.ANALYZE
        self.description = "Performs root cause analysis"
        self.use_llm = True
        self.max_root_causes = 5
        self.include_topology_analysis = True


class AnalyzeAgent(Agent):
    """Agent responsible for root cause analysis.

    This agent analyzes detected anomalies and identifies root causes
    using service topology and optionally LLM assistance.

    Attributes:
        config: Analyze agent configuration.
        _service_graph: Service topology graph.
        _llm_provider: Optional LLM provider for analysis.
    """

    def __init__(
        self,
        service_graph: ServiceGraph,
        llm_provider: LLMProvider | None = None,
        config: AnalyzeAgentConfig | None = None,
    ) -> None:
        """Initialize the analyze agent.

        Args:
            service_graph: Service topology graph.
            llm_provider: Optional LLM provider for analysis.
            config: Agent configuration. Uses defaults if None.
        """
        super().__init__(config or AnalyzeAgentConfig())
        self.analyze_config = config or AnalyzeAgentConfig()
        self._service_graph = service_graph
        self._llm_provider = llm_provider

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute root cause analysis.

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
                    error="Agent cannot execute: no anomaly data in context",
                    agent_name=self.get_name(),
                )

            # Get anomaly data
            detected_anomalies = context.anomaly_data.get("detected_anomalies", [])
            service_id = context.anomaly_data.get("service_id", "unknown")

            if not detected_anomalies:
                return AgentResult.success_result(
                    data={"message": "No anomalies to analyze", "root_causes": []},
                    agent_name=self.get_name(),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            root_causes: list[dict[str, Any]] = []

            # Perform topology-based analysis
            if self.analyze_config.include_topology_analysis:
                topology_causes = self._analyze_topology(service_id)
                root_causes.extend(topology_causes)

            # Perform LLM-based analysis if enabled
            if self.analyze_config.use_llm and self._llm_provider:
                llm_causes = await self._analyze_with_llm(detected_anomalies, service_id)
                # Merge LLM results with topology results
                root_causes = self._merge_causes(root_causes, llm_causes)

            # Sort by confidence and limit results
            root_causes.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            root_causes = root_causes[: self.analyze_config.max_root_causes]

            # Update context with root causes
            context.update(root_causes=root_causes)

            self._set_status(self.get_status().SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult.success_result(
                data={
                    "root_causes": root_causes,
                    "analyzed_anomalies": len(detected_anomalies),
                    "service_id": service_id,
                },
                agent_name=self.get_name(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(self.get_status().FAILED)
            return AgentResult.failure_result(
                error=f"Analyze agent failed: {str(e)}",
                agent_name=self.get_name(),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _analyze_topology(self, service_id: str) -> list[dict[str, Any]]:
        """Analyze root causes using service topology.

        Args:
            service_id: ID of the affected service.

        Returns:
            List of root cause candidates.
        """
        causes = []

        # Get upstream services
        upstream = self._service_graph.get_upstream_services(service_id)

        # Get service info
        service = self._service_graph.get_service(service_id)
        if service:
            # Check service status
            if service.status.value in ["unhealthy", "degraded"]:
                causes.append({
                    "service_id": service_id,
                    "service_name": service.name,
                    "cause_type": "service_status",
                    "confidence": 0.8,
                    "description": f"Service {service.name} is {service.status.value}",
                    "metrics": service.metrics,
                })

        # Check upstream services
        for upstream_id, hops in upstream.items():
            upstream_service = self._service_graph.get_service(upstream_id)
            if upstream_service and upstream_service.status.value in [
                "unhealthy",
                "degraded",
            ]:
                # Calculate confidence based on distance
                confidence = max(0.9 - (hops * 0.1), 0.5)

                causes.append({
                    "service_id": upstream_id,
                    "service_name": upstream_service.name,
                    "cause_type": "upstream_failure",
                    "confidence": confidence,
                    "hops": hops,
                    "description": f"Upstream service {upstream_service.name} is {upstream_service.status.value}",
                    "metrics": upstream_service.metrics,
                })

        # Use graph analysis for root cause candidates
        graph_causes = self._service_graph.find_root_causes(service_id)
        for cause in graph_causes:
            if not any(c["service_id"] == cause["service_id"] for c in causes):
                causes.append({
                    "service_id": cause["service_id"],
                    "service_name": cause["service_name"],
                    "cause_type": "graph_analysis",
                    "confidence": cause["confidence"],
                    "hops": cause["hops"],
                    "description": f"Potential root cause identified by graph analysis",
                    "metrics": cause.get("metrics", {}),
                })

        return causes

    async def _analyze_with_llm(
        self,
        anomalies: list[dict[str, Any]],
        service_id: str,
    ) -> list[dict[str, Any]]:
        """Analyze root causes using LLM.

        Args:
            anomalies: List of detected anomalies.
            service_id: ID of the affected service.

        Returns:
            List of root cause candidates.
        """
        if not self._llm_provider:
            return []

        try:
            # Build prompt
            prompt = self._build_analysis_prompt(anomalies, service_id)

            # Get LLM response
            from nyxai.llm.providers.base import LLMMessage, MessageRole

            messages = [
                LLMMessage(
                    role=MessageRole.SYSTEM,
                    content="You are an expert SRE and systems analyst. Analyze the following anomalies and identify root causes.",
                ),
                LLMMessage(role=MessageRole.USER, content=prompt),
            ]

            response = await self._llm_provider.achat(messages)

            # Parse LLM response
            causes = self._parse_llm_response(response.content, service_id)

            return causes

        except Exception as e:
            # Return empty list on LLM error
            return []

    def _build_analysis_prompt(
        self,
        anomalies: list[dict[str, Any]],
        service_id: str,
    ) -> str:
        """Build analysis prompt for LLM.

        Args:
            anomalies: List of detected anomalies.
            service_id: ID of the affected service.

        Returns:
            Analysis prompt.
        """
        prompt = f"""Analyze the following anomalies detected in service '{service_id}':

Anomalies:
"""
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"\n{i}. {anomaly.get('title', 'Unknown')}\n"
            prompt += f"   Description: {anomaly.get('description', 'N/A')}\n"
            prompt += f"   Severity: {anomaly.get('severity', 'unknown')}\n"
            prompt += f"   Score: {anomaly.get('score', 0)}\n"

        prompt += """

Please identify the root causes in the following JSON format:
[
  {
    "cause_type": "type of root cause (e.g., resource_exhaustion, dependency_failure, configuration_error)",
    "confidence": 0.85,
    "description": "Detailed description of the root cause",
    "suggested_action": "Suggested remediation action"
  }
]

Provide at most 3 root causes, ordered by confidence (highest first).
"""
        return prompt

    def _parse_llm_response(
        self,
        content: str,
        service_id: str,
    ) -> list[dict[str, Any]]:
        """Parse LLM response to extract root causes.

        Args:
            content: LLM response content.
            service_id: Service ID.

        Returns:
            List of root cause candidates.
        """
        import json
        import re

        causes = []

        # Try to extract JSON from response
        try:
            # Look for JSON array in the response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list):
                    for item in data:
                        causes.append({
                            "service_id": service_id,
                            "service_name": service_id,
                            "cause_type": item.get("cause_type", "unknown"),
                            "confidence": item.get("confidence", 0.5),
                            "description": item.get("description", ""),
                            "suggested_action": item.get("suggested_action", ""),
                            "source": "llm_analysis",
                        })
        except (json.JSONDecodeError, Exception):
            # If JSON parsing fails, create a generic cause
            causes.append({
                "service_id": service_id,
                "service_name": service_id,
                "cause_type": "unknown",
                "confidence": 0.3,
                "description": f"LLM analysis: {content[:200]}...",
                "source": "llm_analysis",
            })

        return causes

    def _merge_causes(
        self,
        topology_causes: list[dict[str, Any]],
        llm_causes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge topology and LLM causes.

        Args:
            topology_causes: Causes from topology analysis.
            llm_causes: Causes from LLM analysis.

        Returns:
            Merged list of causes.
        """
        merged = topology_causes.copy()

        for llm_cause in llm_causes:
            # Check if similar cause already exists
            similar_exists = False
            for existing in merged:
                if (
                    existing.get("service_id") == llm_cause.get("service_id")
                    and existing.get("cause_type") == llm_cause.get("cause_type")
                ):
                    # Boost confidence of existing cause
                    existing["confidence"] = max(
                        existing.get("confidence", 0),
                        llm_cause.get("confidence", 0),
                    )
                    similar_exists = True
                    break

            if not similar_exists:
                merged.append(llm_cause)

        return merged
