from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models.evidence import Evidence, EvidenceNode, EvidenceType
from app.services.llm import LLMService


class DiagnosisAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="diagnosis")
        self.llm = llm_service or LLMService()

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        investigation_summary = context.metadata.get("investigation_summary", "")
        investigation_confidence = context.metadata.get("confidence", 0.7)
        
        system_prompt = """你是一个根因分析专家。你的任务是基于调查结果，
进行因果推理，确定根本原因，并生成证据链。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "root_cause": "根因描述",
    "confidence": 0.0-1.0,
    "affected_components": ["组件1", "组件2"],
    "reasoning_report": "详细推理报告",
    "evidence_chain": [{"description": "证据描述", "inference": "推理步骤"}]
}"""
        
        prompt = f"""请分析以下问题的根因：
问题：{query}
调查摘要：{investigation_summary}
调查置信度：{investigation_confidence}"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            expect_json=True,
        )
        
        parsed = response.parsed_json or {}
        root_cause = parsed.get("root_cause", "未知原因")
        confidence = parsed.get("confidence", 0.7)
        affected_components = parsed.get("affected_components", [])
        reasoning_report = parsed.get("reasoning_report", response.content)
        evidence_chain_data = parsed.get("evidence_chain", [])
        
        evidence_nodes = []
        evidence_list = []
        
        for idx, chain_item in enumerate(evidence_chain_data):
            evidence = Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description=chain_item.get("description", f"证据{idx+1}"),
                source_data={"inference": chain_item.get("inference", "")},
                source_system="diagnosis_agent",
                timestamp=datetime.now(),
                confidence=confidence,
            )
            evidence_list.append(evidence)
            
            evidence_nodes.append(EvidenceNode(
                id=str(uuid.uuid4()),
                description=chain_item.get("description", f"推理节点{idx+1}"),
                evidence=evidence,
                inference_step=chain_item.get("inference", ""),
            ))
        
        if not evidence_nodes:
            evidence = Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description="根因推理证据",
                source_data={"reasoning": reasoning_report},
                source_system="diagnosis_agent",
                timestamp=datetime.now(),
                confidence=confidence,
            )
            evidence_list.append(evidence)
            evidence_nodes.append(EvidenceNode(
                id=str(uuid.uuid4()),
                description="根因推理节点",
                evidence=evidence,
                inference_step="基于调查结果进行因果推理",
            ))
        
        return AgentResult(
            success=True,
            data={
                "root_cause": root_cause,
                "confidence": confidence,
                "evidence_chain": [node.model_dump(mode='json') for node in evidence_nodes],
                "affected_components": affected_components,
                "reasoning_report": reasoning_report,
            },
            evidence=evidence_list,
        )

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        knowledge = {}
        if "fault_patterns" in knowledge_types:
            knowledge["fault_patterns"] = "故障模式知识"
        if "causal_rules" in knowledge_types:
            knowledge["causal_rules"] = "因果推理规则"
        return knowledge
