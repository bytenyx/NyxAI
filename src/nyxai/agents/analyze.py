"""Analyze Agent for NyxAI.

This module implements the Analyze Agent that performs root cause analysis.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.agents.base import Agent, AgentConfig, AgentResult
from nyxai.types import AgentContext, AgentRole
from nyxai.llm.providers.base import LLMProvider
from nyxai.llm.prompts import RCAPromptBuilder, RCAPromptConfig, RCAPromptTemplate
from nyxai.llm.prompts.rca_prompts import (
    AnomalyContext,
    DimensionContext,
    ServiceContext,
)
from nyxai.rca.topology.service_graph import ServiceGraph


class AnalyzeAgentConfig(AgentConfig):
    """Configuration for Analyze Agent.

    Attributes:
        use_llm: Whether to use LLM for analysis.
        max_root_causes: Maximum number of root causes to identify.
        include_topology_analysis: Whether to include topology analysis.
        prompt_template: LLM prompt template to use.
        prompt_language: Output language for prompts.
        include_dimension_analysis: Whether to include dimension attribution.
        include_historical_context: Whether to include historical incidents.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "AnalyzeAgent"
        self.role = AgentRole.ANALYZE
        self.description = "Performs root cause analysis"
        self.use_llm = True
        self.max_root_causes = 5
        self.include_topology_analysis = True
        self.prompt_template = RCAPromptTemplate.STANDARD
        self.prompt_language = "zh"
        self.include_dimension_analysis = True
        self.include_historical_context = True


class AnalyzeAgent(Agent):
    """Agent responsible for root cause analysis.

    This agent analyzes detected anomalies and identifies root causes
    using service topology and optionally LLM assistance.

    Attributes:
        config: Analyze agent configuration.
        _service_graph: Service topology graph.
        _llm_provider: Optional LLM provider for analysis.
        _prompt_builder: Builder for RCA prompts.
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

        # Initialize prompt builder with config
        prompt_config = RCAPromptConfig(
            template=self.analyze_config.prompt_template,
            max_root_causes=self.analyze_config.max_root_causes,
            include_metrics=self.analyze_config.include_dimension_analysis,
            include_topology=self.analyze_config.include_topology_analysis,
            language=self.analyze_config.prompt_language,
        )
        self._prompt_builder = RCAPromptBuilder(prompt_config)

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
                llm_result = await self._analyze_with_llm(
                    detected_anomalies, service_id, context
                )
                llm_causes = llm_result.get("root_causes", [])
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
        context: AgentContext,
    ) -> dict[str, Any]:
        """Analyze root causes using LLM with optimized prompts.

        Args:
            anomalies: List of detected anomalies.
            service_id: ID of the affected service.
            context: Agent execution context.

        Returns:
            Dictionary containing root causes and analysis summary.
        """
        if not self._llm_provider:
            return {"root_causes": []}

        try:
            # Build comprehensive contexts
            service_context = self._build_service_context(service_id)
            anomaly_contexts = self._build_anomaly_contexts(anomalies)
            dimension_context = self._build_dimension_context(context)
            topology_context = self._build_topology_context(service_id)
            historical_incidents = self._get_historical_incidents(anomalies)

            # Build optimized prompts
            system_prompt = self._prompt_builder.build_system_prompt()
            user_prompt = self._prompt_builder.build_user_prompt(
                anomalies=anomalies,
                service_context=service_context,
                anomaly_contexts=anomaly_contexts,
                dimension_context=dimension_context,
                topology_context=topology_context,
                historical_incidents=historical_incidents,
            )

            # Get LLM response
            from nyxai.llm.providers.base import LLMMessage, MessageRole

            messages = [
                LLMMessage(role=MessageRole.SYSTEM, content=system_prompt),
                LLMMessage(role=MessageRole.USER, content=user_prompt),
            ]

            response = await self._llm_provider.achat(messages)

            # Parse LLM response using the optimized parser
            parsed_result = self._prompt_builder.parse_response(response.content)

            # Transform to standard format
            return self._transform_llm_result(parsed_result, service_id)

        except Exception as e:
            # Return empty result on LLM error
            return {"root_causes": [], "error": str(e)}

    def _build_service_context(self, service_id: str) -> ServiceContext:
        """Build service context for prompt.

        Args:
            service_id: Service identifier.

        Returns:
            Service context.
        """
        service = self._service_graph.get_service(service_id)

        if service:
            # Get dependencies
            upstream = self._service_graph.get_upstream_services(service_id)
            dependencies = list(upstream.keys())

            return ServiceContext(
                service_id=service_id,
                service_name=service.name,
                service_type=service.service_type.value,
                environment="prod",  # Could be derived from metadata
                dependencies=dependencies,
                recent_deployments=[],  # Could be populated from deployment data
            )

        return ServiceContext(service_id=service_id)

    def _build_anomaly_contexts(
        self, anomalies: list[dict[str, Any]]
    ) -> list[AnomalyContext]:
        """Build anomaly contexts for prompt.

        Args:
            anomalies: List of anomalies.

        Returns:
            List of anomaly contexts.
        """
        contexts = []

        for anomaly in anomalies:
            metric_value = anomaly.get("current_value", 0)
            expected_value = anomaly.get("expected_value", 0)

            # Calculate deviation
            if expected_value > 0:
                deviation = ((metric_value - expected_value) / expected_value) * 100
            else:
                deviation = 0

            ctx = AnomalyContext(
                metric_name=anomaly.get("metric_name", "unknown"),
                metric_value=metric_value,
                expected_value=expected_value,
                deviation_percent=deviation,
                severity=anomaly.get("severity", "medium"),
                duration_minutes=anomaly.get("duration_minutes", 0),
                detection_time=anomaly.get("detected_at", ""),
            )
            contexts.append(ctx)

        return contexts

    def _build_dimension_context(
        self, context: AgentContext
    ) -> DimensionContext | None:
        """Build dimension attribution context for prompt.

        Args:
            context: Agent execution context.

        Returns:
            Dimension context or None.
        """
        # Get dimension attribution data from context if available
        dim_data = context.anomaly_data.get("dimension_attribution")

        if dim_data:
            return DimensionContext(
                top_dimensions=dim_data.get("top_contributors", []),
                dimension_breakdown=dim_data.get("breakdown", {}),
                comparison_data=dim_data.get("comparison", {}),
            )

        return None

    def _build_topology_context(self, service_id: str) -> dict[str, Any]:
        """Build topology context for prompt.

        Args:
            service_id: Service identifier.

        Returns:
            Topology context dictionary.
        """
        upstream = self._service_graph.get_upstream_services(service_id)
        downstream = self._service_graph.get_downstream_services(service_id)

        upstream_services = []
        for uid, hops in upstream.items():
            svc = self._service_graph.get_service(uid)
            if svc:
                upstream_services.append({
                    "id": uid,
                    "name": svc.name,
                    "status": svc.status.value,
                    "hops": hops,
                })

        downstream_services = []
        for did, hops in downstream.items():
            svc = self._service_graph.get_service(did)
            if svc:
                downstream_services.append({
                    "id": did,
                    "name": svc.name,
                    "status": svc.status.value,
                    "hops": hops,
                })

        return {
            "upstream_services": upstream_services,
            "downstream_services": downstream_services,
        }

    def _get_historical_incidents(
        self, anomalies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Get similar historical incidents.

        Args:
            anomalies: Current anomalies.

        Returns:
            List of historical incidents.
        """
        # This could be enhanced to query the knowledge base
        # For now, return empty list
        return []

    def _transform_llm_result(
        self, parsed_result: dict[str, Any], service_id: str
    ) -> dict[str, Any]:
        """Transform parsed LLM result to standard format.

        Args:
            parsed_result: Parsed LLM response.
            service_id: Service identifier.

        Returns:
            Standardized result dictionary.
        """
        root_causes = []

        # Extract root causes from parsed result
        causes = parsed_result.get("root_causes", [])

        for cause in causes:
            root_causes.append({
                "service_id": service_id,
                "service_name": cause.get("service_name", service_id),
                "cause_type": cause.get("cause_type", "unknown"),
                "confidence": cause.get("confidence", 0.5),
                "description": cause.get("description", ""),
                "suggested_action": cause.get("suggested_action", ""),
                "evidence": cause.get("evidence", []),
                "prevention": cause.get("prevention", ""),
                "source": "llm_analysis",
            })

        return {
            "root_causes": root_causes,
            "analysis_summary": parsed_result.get("analysis_summary", ""),
            "impact_assessment": parsed_result.get("impact_assessment", {}),
            "timeline": parsed_result.get("timeline", []),
        }

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
                    # Merge evidence
                    if "evidence" in llm_cause:
                        existing_evidence = existing.get("evidence", [])
                        existing_evidence.extend(llm_cause.get("evidence", []))
                        existing["evidence"] = list(set(existing_evidence))
                    similar_exists = True
                    break

            if not similar_exists:
                merged.append(llm_cause)

        return merged
