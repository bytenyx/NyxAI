from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models.evidence import Evidence, EvidenceType
from app.services.llm import LLMConfig, LLMService


class InvestigationAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="investigation")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        
        system_prompt = """你是一个运维调查专家。你的任务是分析告警或问题描述，
识别可能的异常点，并收集相关证据。

请返回JSON格式的结果，包含：
1. anomalies: 识别的异常列表
2. evidence: 收集的证据列表
3. summary: 调查摘要"""
        
        response = await self.llm.generate(
            prompt=f"请调查以下问题：{query}",
            system_prompt=system_prompt,
        )
        
        evidence = [
            Evidence(
                id=str(uuid.uuid4()),
                evidence_type=EvidenceType.KNOWLEDGE,
                description=f"调查查询: {query}",
                source_data={"query": query},
                source_system="investigation_agent",
                timestamp=datetime.now(),
                confidence=0.8,
            )
        ]
        
        return AgentResult(
            success=True,
            data={
                "anomalies": [],
                "summary": response.content,
            },
            evidence=evidence,
        )

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        knowledge = {}
        if "metric_definitions" in knowledge_types:
            knowledge["metric_definitions"] = "指标定义知识"
        if "log_patterns" in knowledge_types:
            knowledge["log_patterns"] = "日志模式知识"
        return knowledge
