"""Root Cause Analysis Prompts for NyxAI.

This module provides optimized prompts for LLM-based root cause analysis.
The prompts are designed to maximize accuracy and provide actionable insights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RCAPromptTemplate(str, Enum):
    """Available RCA prompt templates."""

    STANDARD = "standard"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


@dataclass
class RCAPromptConfig:
    """Configuration for RCA prompt generation.

    Attributes:
        template: Prompt template style to use.
        max_root_causes: Maximum number of root causes to identify.
        include_metrics: Whether to include metric analysis.
        include_topology: Whether to include topology context.
        include_timeline: Whether to include incident timeline.
        include_recommendations: Whether to include recommendations.
        language: Output language (en, zh, etc.).
        detail_level: Level of detail (low, medium, high).
    """

    template: RCAPromptTemplate = RCAPromptTemplate.STANDARD
    max_root_causes: int = 3
    include_metrics: bool = True
    include_topology: bool = True
    include_timeline: bool = True
    include_recommendations: bool = True
    language: str = "zh"
    detail_level: str = "high"


@dataclass
class AnomalyContext:
    """Context information about an anomaly.

    Attributes:
        metric_name: Name of the affected metric.
        metric_value: Current metric value.
        expected_value: Expected/baseline metric value.
        deviation_percent: Deviation percentage.
        severity: Severity level (critical, high, medium, low).
        duration_minutes: Duration of the anomaly.
        detection_time: Time when anomaly was detected.
    """

    metric_name: str
    metric_value: float
    expected_value: float
    deviation_percent: float
    severity: str
    duration_minutes: int = 0
    detection_time: str = ""


@dataclass
class ServiceContext:
    """Context information about a service.

    Attributes:
        service_id: Service identifier.
        service_name: Human-readable service name.
        service_type: Type of service (api, database, cache, etc.).
        team: Owning team.
        environment: Environment (prod, staging, dev).
        dependencies: List of upstream dependencies.
        recent_deployments: Recent deployment information.
    """

    service_id: str
    service_name: str = ""
    service_type: str = ""
    team: str = ""
    environment: str = "prod"
    dependencies: list[str] = field(default_factory=list)
    recent_deployments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DimensionContext:
    """Context about dimension attribution analysis.

    Attributes:
        top_dimensions: Top contributing dimensions.
        dimension_breakdown: Breakdown by dimension values.
        comparison_data: Comparison with baseline period.
    """

    top_dimensions: list[dict[str, Any]] = field(default_factory=list)
    dimension_breakdown: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    comparison_data: dict[str, Any] = field(default_factory=dict)


class RCAPromptBuilder:
    """Builder for optimized RCA prompts.

    This class constructs highly effective prompts for LLM-based root cause
    analysis, incorporating best practices for prompt engineering.
    """

    # System prompts optimized for different contexts
    SYSTEM_PROMPTS = {
        "zh": {
            "standard": """你是一位资深的 SRE (站点可靠性工程师) 和系统架构专家，擅长分析复杂的分布式系统故障。

你的任务是分析系统异常，识别根本原因，并提供可操作的修复建议。

分析原则：
1. 基于数据驱动，避免主观臆测
2. 考虑系统间的依赖关系
3. 区分直接原因和根本原因
4. 评估影响范围和严重程度
5. 提供具体、可执行的修复步骤

输出格式要求：
- 使用结构化 JSON 格式
- 每个根因包含类型、置信度、详细描述和建议操作
- 按置信度降序排列""",
            "detailed": """你是一位资深的 SRE (站点可靠性工程师) 和系统架构专家，拥有丰富的分布式系统故障排查经验。

你的任务是深入分析系统异常，运用系统性思维识别根本原因，并提供全面的修复建议。

分析框架：
1. 现象分析：理解异常的表现形式和特征
2. 影响评估：评估对业务和用户的实际影响
3. 依赖分析：检查上下游服务的健康状况
4. 变更关联：关联近期的部署、配置变更
5. 资源检查：分析 CPU、内存、网络、磁盘等资源使用
6. 日志分析：从日志中提取关键错误信息
7. 根因定位：区分直接原因和深层根本原因
8. 修复建议：提供短期缓解和长期解决方案

输出要求：
- 详细的根因分析，包含证据链
- 明确区分直接原因和根本原因
- 提供具体的修复步骤和验证方法
- 包含预防措施建议""",
            "technical": """你是一位技术专家，专注于分布式系统的深度故障分析。

请使用专业的技术视角分析以下系统异常，重点关注：
- 架构层面的设计缺陷
- 代码层面的潜在问题
- 配置错误或不合理之处
- 资源竞争或瓶颈
- 并发或时序问题
- 网络或通信故障

分析应基于技术事实，提供可验证的假设和排查路径。""",
            "executive": """你是一位技术管理专家，需要从业务影响角度分析系统故障。

请提供：
1. 业务影响评估（用户影响、收入影响、品牌影响）
2. 故障严重程度分级
3. 关键恢复时间节点
4. 资源调配建议
5. 沟通策略建议

分析应简洁明了，便于向非技术利益相关者传达。""",
        },
        "en": {
            "standard": """You are a senior SRE (Site Reliability Engineer) and systems architecture expert, specializing in analyzing complex distributed system failures.

Your task is to analyze system anomalies, identify root causes, and provide actionable remediation recommendations.

Analysis principles:
1. Data-driven, avoid speculation
2. Consider system dependencies
3. Distinguish between direct causes and root causes
4. Assess impact scope and severity
5. Provide specific, executable remediation steps

Output format requirements:
- Use structured JSON format
- Each root cause includes type, confidence, detailed description, and suggested actions
- Ordered by confidence (highest first)""",
            "detailed": """You are a senior SRE and systems architecture expert with extensive experience in distributed system troubleshooting.

Your task is to deeply analyze system anomalies using systematic thinking to identify root causes and provide comprehensive remediation recommendations.

Analysis framework:
1. Phenomenon analysis: Understand anomaly manifestations
2. Impact assessment: Evaluate business and user impact
3. Dependency analysis: Check upstream/downstream service health
4. Change correlation: Link to recent deployments or configuration changes
5. Resource check: Analyze CPU, memory, network, disk usage
6. Log analysis: Extract key error information
7. Root cause identification: Distinguish direct vs. deep root causes
8. Remediation: Provide short-term mitigation and long-term solutions

Output requirements:
- Detailed root cause analysis with evidence chain
- Clear distinction between direct and root causes
- Specific remediation steps and validation methods
- Include preventive measures""",
            "technical": """You are a technical expert focused on deep fault analysis of distributed systems.

Please analyze the following system anomalies from a technical perspective, focusing on:
- Architecture-level design flaws
- Code-level potential issues
- Configuration errors or unreasonable settings
- Resource contention or bottlenecks
- Concurrency or timing issues
- Network or communication failures

Analysis should be based on technical facts, providing verifiable hypotheses and investigation paths.""",
            "executive": """You are a technical management expert who needs to analyze system failures from a business impact perspective.

Please provide:
1. Business impact assessment (user impact, revenue impact, brand impact)
2. Failure severity classification
3. Key recovery timeline milestones
4. Resource allocation recommendations
5. Communication strategy recommendations

Analysis should be concise and clear for communication to non-technical stakeholders.""",
        },
    }

    # Cause type classifications
    CAUSE_TYPES = {
        "zh": {
            "resource_exhaustion": "资源耗尽",
            "dependency_failure": "依赖故障",
            "configuration_error": "配置错误",
            "deployment_issue": "部署问题",
            "network_issue": "网络问题",
            "database_issue": "数据库问题",
            "code_bug": "代码缺陷",
            "traffic_spike": "流量突增",
            "cascading_failure": "级联故障",
            "external_dependency": "外部依赖",
            "infrastructure_issue": "基础设施问题",
            "security_issue": "安全问题",
            "unknown": "未知原因",
        },
        "en": {
            "resource_exhaustion": "Resource Exhaustion",
            "dependency_failure": "Dependency Failure",
            "configuration_error": "Configuration Error",
            "deployment_issue": "Deployment Issue",
            "network_issue": "Network Issue",
            "database_issue": "Database Issue",
            "code_bug": "Code Bug",
            "traffic_spike": "Traffic Spike",
            "cascading_failure": "Cascading Failure",
            "external_dependency": "External Dependency",
            "infrastructure_issue": "Infrastructure Issue",
            "security_issue": "Security Issue",
            "unknown": "Unknown",
        },
    }

    def __init__(self, config: RCAPromptConfig | None = None) -> None:
        """Initialize the prompt builder.

        Args:
            config: Prompt configuration. Uses defaults if None.
        """
        self.config = config or RCAPromptConfig()

    def build_system_prompt(self) -> str:
        """Build the system prompt.

        Returns:
            System prompt string.
        """
        lang = self.config.language
        template = self.config.template.value

        if lang not in self.SYSTEM_PROMPTS:
            lang = "en"

        return self.SYSTEM_PROMPTS[lang].get(
            template, self.SYSTEM_PROMPTS[lang]["standard"]
        )

    def build_user_prompt(
        self,
        anomalies: list[dict[str, Any]],
        service_context: ServiceContext | None = None,
        anomaly_contexts: list[AnomalyContext] | None = None,
        dimension_context: DimensionContext | None = None,
        topology_context: dict[str, Any] | None = None,
        historical_incidents: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build the user prompt with comprehensive context.

        Args:
            anomalies: List of detected anomalies.
            service_context: Service context information.
            anomaly_contexts: Detailed anomaly contexts.
            dimension_context: Dimension attribution context.
            topology_context: Service topology context.
            historical_incidents: Similar historical incidents.

        Returns:
            User prompt string.
        """
        lang = self.config.language
        sections = []

        # Header
        sections.append(self._build_header(lang))

        # Service context
        if service_context:
            sections.append(self._build_service_section(service_context, lang))

        # Anomaly details
        sections.append(self._build_anomaly_section(anomalies, anomaly_contexts, lang))

        # Dimension attribution
        if dimension_context and self.config.include_metrics:
            sections.append(self._build_dimension_section(dimension_context, lang))

        # Topology context
        if topology_context and self.config.include_topology:
            sections.append(self._build_topology_section(topology_context, lang))

        # Historical incidents
        if historical_incidents:
            sections.append(self._build_historical_section(historical_incidents, lang))

        # Output format instructions
        sections.append(self._build_output_format(lang))

        return "\n\n".join(sections)

    def _build_header(self, lang: str) -> str:
        """Build the prompt header.

        Args:
            lang: Language code.

        Returns:
            Header section.
        """
        if lang == "zh":
            return "## 故障分析请求\n\n请分析以下系统异常，识别根本原因。"
        return "## Root Cause Analysis Request\n\nPlease analyze the following system anomalies and identify root causes."

    def _build_service_section(
        self, context: ServiceContext, lang: str
    ) -> str:
        """Build the service context section.

        Args:
            context: Service context.
            lang: Language code.

        Returns:
            Service section.
        """
        if lang == "zh":
            lines = ["### 服务信息", ""]
            lines.append(f"- **服务ID**: {context.service_id}")
            if context.service_name:
                lines.append(f"- **服务名称**: {context.service_name}")
            if context.service_type:
                lines.append(f"- **服务类型**: {context.service_type}")
            if context.team:
                lines.append(f"- **负责团队**: {context.team}")
            lines.append(f"- **环境**: {context.environment}")

            if context.dependencies:
                lines.append(f"- **依赖服务**: {', '.join(context.dependencies)}")

            if context.recent_deployments:
                lines.append("\n**近期部署**:")
                for dep in context.recent_deployments[-3:]:  # Last 3 deployments
                    lines.append(f"- {dep.get('time', 'Unknown')}: {dep.get('version', 'Unknown')}")
        else:
            lines = ["### Service Information", ""]
            lines.append(f"- **Service ID**: {context.service_id}")
            if context.service_name:
                lines.append(f"- **Service Name**: {context.service_name}")
            if context.service_type:
                lines.append(f"- **Service Type**: {context.service_type}")
            if context.team:
                lines.append(f"- **Team**: {context.team}")
            lines.append(f"- **Environment**: {context.environment}")

            if context.dependencies:
                lines.append(f"- **Dependencies**: {', '.join(context.dependencies)}")

            if context.recent_deployments:
                lines.append("\n**Recent Deployments**:")
                for dep in context.recent_deployments[-3:]:
                    lines.append(f"- {dep.get('time', 'Unknown')}: {dep.get('version', 'Unknown')}")

        return "\n".join(lines)

    def _build_anomaly_section(
        self,
        anomalies: list[dict[str, Any]],
        contexts: list[AnomalyContext] | None,
        lang: str,
    ) -> str:
        """Build the anomaly details section.

        Args:
            anomalies: List of anomalies.
            contexts: Detailed anomaly contexts.
            lang: Language code.

        Returns:
            Anomaly section.
        """
        if lang == "zh":
            lines = ["### 异常详情", ""]
        else:
            lines = ["### Anomaly Details", ""]

        for i, anomaly in enumerate(anomalies, 1):
            lines.append(f"**异常 #{i}**")
            lines.append(f"- 指标: {anomaly.get('metric_name', 'Unknown')}")
            lines.append(f"- 严重程度: {anomaly.get('severity', 'unknown')}")
            lines.append(f"- 检测时间: {anomaly.get('detected_at', 'Unknown')}")

            if contexts and i <= len(contexts):
                ctx = contexts[i - 1]
                lines.append(f"- 当前值: {ctx.metric_value:.2f}")
                lines.append(f"- 期望值: {ctx.expected_value:.2f}")
                lines.append(f"- 偏差: {ctx.deviation_percent:+.1f}%")
                if ctx.duration_minutes > 0:
                    lines.append(f"- 持续时间: {ctx.duration_minutes} 分钟")

            lines.append("")

        return "\n".join(lines)

    def _build_dimension_section(
        self, context: DimensionContext, lang: str
    ) -> str:
        """Build the dimension attribution section.

        Args:
            context: Dimension context.
            lang: Language code.

        Returns:
            Dimension section.
        """
        if lang == "zh":
            lines = ["### 维度归因分析", ""]
            lines.append("根据维度分析，以下维度对异常贡献最大：")
        else:
            lines = ["### Dimension Attribution Analysis", ""]
            lines.append("Based on dimension analysis, the following dimensions contribute most to the anomaly:")

        for dim in context.top_dimensions[:5]:  # Top 5 dimensions
            name = dim.get("dimension_name", "Unknown")
            value = dim.get("dimension_value", "Unknown")
            score = dim.get("contribution_score", 0)
            actual = dim.get("actual_value", 0)
            expected = dim.get("expected_value", 0)

            if lang == "zh":
                lines.append(f"\n- **{name}={value}** (贡献度: {score:.1%})")
                lines.append(f"  - 实际值: {actual:.2f}, 期望值: {expected:.2f}")
            else:
                lines.append(f"\n- **{name}={value}** (Contribution: {score:.1%})")
                lines.append(f"  - Actual: {actual:.2f}, Expected: {expected:.2f}")

        return "\n".join(lines)

    def _build_topology_section(
        self, context: dict[str, Any], lang: str
    ) -> str:
        """Build the topology context section.

        Args:
            context: Topology context.
            lang: Language code.

        Returns:
            Topology section.
        """
        if lang == "zh":
            lines = ["### 服务拓扑信息", ""]
        else:
            lines = ["### Service Topology Information", ""]

        upstream = context.get("upstream_services", [])
        downstream = context.get("downstream_services", [])

        if upstream:
            if lang == "zh":
                lines.append("**上游服务状态**:")
            else:
                lines.append("**Upstream Services**:")

            for svc in upstream[:5]:
                status = svc.get("status", "unknown")
                name = svc.get("name", "Unknown")
                lines.append(f"- {name}: {status}")

        if downstream:
            if lang == "zh":
                lines.append("\n**下游服务状态**:")
            else:
                lines.append("\n**Downstream Services**:")

            for svc in downstream[:5]:
                status = svc.get("status", "unknown")
                name = svc.get("name", "Unknown")
                lines.append(f"- {name}: {status}")

        return "\n".join(lines)

    def _build_historical_section(
        self, incidents: list[dict[str, Any]], lang: str
    ) -> str:
        """Build the historical incidents section.

        Args:
            incidents: Historical incidents.
            lang: Language code.

        Returns:
            Historical section.
        """
        if lang == "zh":
            lines = ["### 相似历史事件", ""]
            lines.append("以下历史事件可能提供参考：")
        else:
            lines = ["### Similar Historical Incidents", ""]
            lines.append("The following historical incidents may provide reference:")

        for incident in incidents[:3]:  # Top 3 similar incidents
            title = incident.get("title", "Unknown")
            root_cause = incident.get("root_cause", "Unknown")
            resolution = incident.get("resolution", "")

            if lang == "zh":
                lines.append(f"\n- **{title}**")
                lines.append(f"  - 根因: {root_cause}")
                if resolution:
                    lines.append(f"  - 解决方案: {resolution}")
            else:
                lines.append(f"\n- **{title}**")
                lines.append(f"  - Root Cause: {root_cause}")
                if resolution:
                    lines.append(f"  - Resolution: {resolution}")

        return "\n".join(lines)

    def _build_output_format(self, lang: str) -> str:
        """Build the output format instructions.

        Args:
            lang: Language code.

        Returns:
            Output format section.
        """
        max_causes = self.config.max_root_causes

        if lang == "zh":
            return f"""### 输出格式

请以以下 JSON 格式输出分析结果，最多 {max_causes} 个根因，按置信度降序排列：

```json
{{
  "analysis_summary": "对故障的简要总结",
  "root_causes": [
    {{
      "rank": 1,
      "cause_type": "根因类型 (如: resource_exhaustion, dependency_failure, configuration_error)",
      "confidence": 0.95,
      "title": "根因标题",
      "description": "详细的根因描述，包含证据链和分析逻辑",
      "affected_scope": "影响范围",
      "evidence": ["证据1", "证据2"],
      "suggested_action": "建议的修复操作",
      "prevention": "预防措施建议"
    }}
  ],
  "impact_assessment": {{
    "severity": "严重级别",
    "affected_users": "受影响用户估计",
    "business_impact": "业务影响描述"
  }},
  "timeline": [
    {{"time": "时间", "event": "事件描述"}}
  ]
}}
```

根因类型可选值: {', '.join(self.CAUSE_TYPES['zh'].values())}

注意：
1. confidence 必须是 0-1 之间的数值
2. 提供具体的证据支持你的分析
3. suggested_action 应该是具体可执行的操作
4. 区分直接原因和根本原因"""
        else:
            return f"""### Output Format

Please output the analysis result in the following JSON format, with at most {max_causes} root causes, ordered by confidence (highest first):

```json
{{
  "analysis_summary": "Brief summary of the incident",
  "root_causes": [
    {{
      "rank": 1,
      "cause_type": "Root cause type (e.g., resource_exhaustion, dependency_failure, configuration_error)",
      "confidence": 0.95,
      "title": "Root cause title",
      "description": "Detailed root cause description with evidence chain and analysis logic",
      "affected_scope": "Scope of impact",
      "evidence": ["Evidence 1", "Evidence 2"],
      "suggested_action": "Suggested remediation action",
      "prevention": "Prevention measures"
    }}
  ],
  "impact_assessment": {{
    "severity": "Severity level",
    "affected_users": "Estimated affected users",
    "business_impact": "Business impact description"
  }},
  "timeline": [
    {{"time": "Timestamp", "event": "Event description"}}
  ]
}}
```

Available cause types: {', '.join(self.CAUSE_TYPES['en'].values())}

Notes:
1. confidence must be a value between 0-1
2. Provide specific evidence supporting your analysis
3. suggested_action should be specific and executable
4. Distinguish between direct causes and root causes"""

    def parse_response(self, content: str) -> dict[str, Any]:
        """Parse the LLM response.

        Args:
            content: LLM response content.

        Returns:
            Parsed response as dictionary.
        """
        import json
        import re

        try:
            # Try to extract JSON from the response
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find JSON without markdown
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Return raw content if no JSON found
            return {"raw_response": content}

        except json.JSONDecodeError:
            return {"parse_error": True, "raw_response": content}
