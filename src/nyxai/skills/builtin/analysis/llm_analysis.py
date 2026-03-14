"""LLM analysis skill for AnalyzeAgent.

This skill performs root cause analysis using LLM assistance.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.types import AgentRole
from nyxai.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus


class LLMAnalysisSkillConfig(SkillConfig):
    """Configuration for LLMAnalysisSkill.

    Attributes:
        model_name: Name of the LLM model to use.
        max_tokens: Maximum tokens for LLM response.
        temperature: Temperature for LLM generation.
        language: Output language for analysis.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.model_name = kwargs.get("model_name", "gpt-4")
        self.max_tokens = kwargs.get("max_tokens", 2000)
        self.temperature = kwargs.get("temperature", 0.3)
        self.language = kwargs.get("language", "zh")


class LLMAnalysisSkill(Skill):
    """Skill for analyzing root causes using LLM.

    This skill uses LLM to perform intelligent root cause analysis
based on anomaly data and service context.
    """

    def __init__(self, config: LLMAnalysisSkillConfig | None = None) -> None:
        """Initialize the LLM analysis skill.

        Args:
            config: Skill configuration.
        """
        super().__init__(config or LLMAnalysisSkillConfig())
        self._llm_config = config or LLMAnalysisSkillConfig()

    @property
    def name(self) -> str:
        """Get skill name."""
        return "llm_analysis"

    @property
    def description(self) -> str:
        """Get skill description."""
        return "Performs root cause analysis using LLM assistance"

    @property
    def agent_role(self) -> AgentRole:
        """Get target agent role."""
        return AgentRole.ANALYZE

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute LLM analysis.

        Args:
            context: Skill execution context.

        Returns:
            Skill execution result with LLM analysis results.
        """
        start_time = time.time()
        self._set_status(SkillStatus.RUNNING)

        try:
            # Get input data
            service_id = context.input_data.get("service_id", "unknown")
            anomalies = context.input_data.get("anomalies", [])
            service_context = context.input_data.get("service_context", {})

            if not anomalies:
                self._set_status(SkillStatus.SKIPPED)
                return SkillResult.skipped_result(
                    reason="No anomalies to analyze",
                    skill_name=self.name,
                )

            # Build prompt for LLM
            prompt = self._build_analysis_prompt(
                service_id=service_id,
                anomalies=anomalies,
                service_context=service_context,
            )

            # Call LLM (placeholder)
            llm_response = await self._call_llm(prompt)

            # Parse LLM response
            root_causes = self._parse_llm_response(llm_response)

            self._set_status(SkillStatus.SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return SkillResult.success_result(
                data={
                    "service_id": service_id,
                    "root_causes": root_causes,
                    "cause_count": len(root_causes),
                    "analysis_method": "llm",
                    "model_used": self._llm_config.model_name,
                },
                skill_name=self.name,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(SkillStatus.FAILED)
            return SkillResult.failure_result(
                error=f"LLM analysis failed: {str(e)}",
                skill_name=self.name,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _build_analysis_prompt(
        self,
        service_id: str,
        anomalies: list[dict[str, Any]],
        service_context: dict[str, Any],
    ) -> str:
        """Build analysis prompt for LLM.

        Args:
            service_id: ID of the affected service.
            anomalies: List of detected anomalies.
            service_context: Service context information.

        Returns:
            Formatted prompt string.
        """
        language = self._llm_config.language

        if language == "zh":
            prompt = f"""请分析以下异常并识别根因:

服务ID: {service_id}

异常信息:
"""
            for i, anomaly in enumerate(anomalies, 1):
                prompt += f"\n{i}. 指标: {anomaly.get('metric_name', 'unknown')}\n"
                prompt += f"   严重程度: {anomaly.get('severity', 'unknown')}\n"
                prompt += f"   得分: {anomaly.get('score', 0)}\n"

            prompt += """
请提供:
1. 可能的根因
2. 每个根因的置信度(0-1)
3. 建议的修复操作
4. 预防措施
"""
        else:
            prompt = f"""Please analyze the following anomalies and identify root causes:

Service ID: {service_id}

Anomaly Information:
"""
            for i, anomaly in enumerate(anomalies, 1):
                prompt += f"\n{i}. Metric: {anomaly.get('metric_name', 'unknown')}\n"
                prompt += f"   Severity: {anomaly.get('severity', 'unknown')}\n"
                prompt += f"   Score: {anomaly.get('score', 0)}\n"

            prompt += """
Please provide:
1. Possible root causes
2. Confidence level for each cause (0-1)
3. Suggested remediation actions
4. Prevention measures
"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with the analysis prompt.

        Args:
            prompt: Analysis prompt.

        Returns:
            LLM response text.
        """
        # Placeholder implementation
        # In real implementation, this would call the LLM provider
        return "LLM analysis response placeholder"

    def _parse_llm_response(self, response: str) -> list[dict[str, Any]]:
        """Parse LLM response into structured root causes.

        Args:
            response: Raw LLM response.

        Returns:
            List of parsed root causes.
        """
        # Placeholder implementation
        # In real implementation, this would parse structured output
        return [
            {
                "service_id": "unknown",
                "cause_type": "llm_analysis",
                "confidence": 0.7,
                "description": "LLM identified potential root cause",
                "suggested_action": "Review service logs",
                "source": "llm_analysis",
            }
        ]

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
        return "anomalies" in context.input_data
