from datetime import datetime
from typing import Any, Dict, List
import uuid
import time

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.models.evidence import Evidence, EvidenceType
from app.services.llm import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InvestigationAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="investigation")
        self.llm = llm_service or LLMService()

    async def execute(self, context: AgentContext) -> AgentResult:
        start_time = time.time()
        query = context.query or ""
        session_id = context.session_id
        
        logger.info("=" * 60)
        logger.info(f"[InvestigationAgent] Starting investigation for session_id={session_id}")
        logger.info(f"[InvestigationAgent] Query: {query[:200]}{'...' if len(query) > 200 else ''}")
        
        try:
            system_prompt = """你是一个运维调查专家。你的任务是分析告警或问题描述，
识别可能的异常点，并收集相关证据。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "anomalies": [{"name": "异常名称", "severity": "high/medium/low", "description": "描述"}],
    "evidence": [{"description": "证据描述", "source": "来源系统"}],
    "summary": "调查摘要",
    "confidence": 0.0-1.0
}"""
            
            logger.debug(f"[InvestigationAgent] Calling LLM service")
            llm_start = time.time()
            response = await self.llm.generate(
                prompt=f"请调查以下问题：{query}",
                system_prompt=system_prompt,
                expect_json=True,
            )
            llm_duration = time.time() - llm_start
            logger.info(f"[InvestigationAgent] LLM call completed in {llm_duration:.2f}s")
            
            parsed = response.parsed_json or {}
            anomalies = parsed.get("anomalies", [])
            evidence_list = parsed.get("evidence", [])
            summary = parsed.get("summary", response.content)
            confidence = parsed.get("confidence", 0.7)
            
            logger.info(f"[InvestigationAgent] Found {len(anomalies)} anomalies, {len(evidence_list)} evidence items")
            logger.debug(f"[InvestigationAgent] Anomalies: {[a.get('name', 'unknown') for a in anomalies]}")
            logger.debug(f"[InvestigationAgent] Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}")
            
            evidence = [
                Evidence(
                    id=str(uuid.uuid4()),
                    evidence_type=EvidenceType.KNOWLEDGE,
                    description=f"调查查询: {query}",
                    source_data={"query": query, "anomalies": anomalies},
                    source_system="investigation_agent",
                    timestamp=datetime.now(),
                    confidence=confidence,
                )
            ]
            
            for ev in evidence_list:
                evidence.append(Evidence(
                    id=str(uuid.uuid4()),
                    evidence_type=EvidenceType.KNOWLEDGE,
                    description=ev.get("description", ""),
                    source_data=ev,
                    source_system=ev.get("source", "unknown"),
                    timestamp=datetime.now(),
                    confidence=confidence,
                ))
            
            total_duration = time.time() - start_time
            logger.info(f"[InvestigationAgent] Investigation completed successfully in {total_duration:.2f}s")
            logger.info(f"[InvestigationAgent] Collected {len(evidence)} total evidence items")
            logger.info("=" * 60)
            
            return AgentResult(
                success=True,
                data={
                    "anomalies": anomalies,
                    "summary": summary,
                    "confidence": confidence,
                },
                evidence=evidence,
            )
        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"[InvestigationAgent] Investigation failed after {total_duration:.2f}s: {e}", exc_info=True)
            logger.error("=" * 60)
            raise

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        knowledge = {}
        if "metric_definitions" in knowledge_types:
            knowledge["metric_definitions"] = "指标定义知识"
        if "log_patterns" in knowledge_types:
            knowledge["log_patterns"] = "日志模式知识"
        return knowledge
