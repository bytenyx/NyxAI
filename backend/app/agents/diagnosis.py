from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models.evidence import Evidence, EvidenceNode, EvidenceType
from app.services.llm import LLMConfig, LLMService


class DiagnosisAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="diagnosis")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        investigation_summary = context.metadata.get("investigation_summary", "")
        
        system_prompt = """你是一个根因分析专家。你的任务是基于调查结果，
进行因果推理，确定根本原因，并生成证据链。

请返回JSON格式的结果，包含：
1. root_cause: 根因描述
2. confidence: 置信度(0-1)
3. evidence_chain: 证据链
4. affected_components: 受影响组件
5. reasoning_report: 推理报告"""
        
        prompt = f"""请分析以下问题的根因：
问题：{query}
调查摘要：{investigation_summary}"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        evidence_node = EvidenceNode(
            id=str(uuid.uuid4()),
            description="根因推理节点",
            evidence=Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description="推理证据",
                source_data={"reasoning": response.content},
                source_system="diagnosis_agent",
                timestamp=datetime.now(),
                confidence=0.85,
            ),
            inference_step="基于调查结果进行因果推理",
        )
        
        return AgentResult(
            success=True,
            data={
                "root_cause": response.content[:200] if response.content else "未知原因",
                "confidence": 0.85,
                "evidence_chain": [evidence_node.model_dump()],
                "affected_components": [],
                "reasoning_report": response.content,
            },
            evidence=[evidence_node.evidence],
        )

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        knowledge = {}
        if "fault_patterns" in knowledge_types:
            knowledge["fault_patterns"] = "故障模式知识"
        if "causal_rules" in knowledge_types:
            knowledge["causal_rules"] = "因果推理规则"
        return knowledge
