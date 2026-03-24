from typing import Any, Dict, List
import time

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.llm import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RecoveryAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="recovery")
        self.llm = llm_service or LLMService()

    async def execute(self, context: AgentContext) -> AgentResult:
        start_time = time.time()
        query = context.query or ""
        session_id = context.session_id
        root_cause = context.metadata.get("root_cause", "")
        confidence = context.metadata.get("confidence", 0.5)
        
        logger.info("=" * 60)
        logger.info(f"[RecoveryAgent] Starting recovery for session_id={session_id}")
        logger.info(f"[RecoveryAgent] Query: {query[:200]}{'...' if len(query) > 200 else ''}")
        logger.info(f"[RecoveryAgent] Root cause: {root_cause[:200]}{'...' if len(root_cause) > 200 else ''}")
        logger.info(f"[RecoveryAgent] Confidence: {confidence:.2f}")
        
        try:
            system_prompt = """你是一个故障恢复专家。你的任务是基于根因分析结果，
制定恢复方案，评估风险等级。

请严格返回JSON格式的结果（不要包含markdown代码块标记），包含：
{
    "actions": [
        {
            "action_type": "restart/scale/configure/investigate",
            "description": "操作描述",
            "risk_level": "low/medium/high",
            "target": "目标组件"
        }
    ],
    "risk_level": "low/medium/high",
    "requires_confirmation": true/false,
    "rollback_plan": "回滚方案描述",
    "estimated_impact": "影响评估"
}"""
            
            prompt = f"""请为以下问题制定恢复方案：
问题：{query}
根因：{root_cause}
置信度：{confidence}"""
            
            logger.debug(f"[RecoveryAgent] Calling LLM service")
            llm_start = time.time()
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                expect_json=True,
            )
            llm_duration = time.time() - llm_start
            logger.info(f"[RecoveryAgent] LLM call completed in {llm_duration:.2f}s")
            
            parsed = response.parsed_json or {}
            
            actions = parsed.get("actions", [])
            if not actions:
                logger.warning(f"[RecoveryAgent] No actions returned, creating default investigation action")
                actions = [
                    {
                        "action_type": "investigate",
                        "description": "需要进一步调查确认根因",
                        "risk_level": "low",
                        "target": "unknown",
                    }
                ]
            
            risk_level = parsed.get("risk_level", self._assess_risk(confidence))
            requires_confirmation = parsed.get("requires_confirmation", risk_level != "low")
            rollback_plan = parsed.get("rollback_plan", "暂无回滚方案")
            estimated_impact = parsed.get("estimated_impact", "需要评估")
            
            logger.info(f"[RecoveryAgent] Generated {len(actions)} recovery actions")
            for idx, action in enumerate(actions):
                logger.info(f"[RecoveryAgent] Action {idx+1}: {action.get('action_type')} - {action.get('description')[:100]}{'...' if len(action.get('description', '')) > 100 else ''} (risk: {action.get('risk_level')})")
            logger.info(f"[RecoveryAgent] Overall risk level: {risk_level}")
            logger.info(f"[RecoveryAgent] Requires confirmation: {requires_confirmation}")
            logger.info(f"[RecoveryAgent] Rollback plan: {rollback_plan[:200]}{'...' if len(rollback_plan) > 200 else ''}")
            logger.info(f"[RecoveryAgent] Estimated impact: {estimated_impact[:200]}{'...' if len(estimated_impact) > 200 else ''}")
            
            total_duration = time.time() - start_time
            logger.info(f"[RecoveryAgent] Recovery completed successfully in {total_duration:.2f}s")
            logger.info("=" * 60)
            
            return AgentResult(
                success=True,
                data={
                    "actions": actions,
                    "risk_level": risk_level,
                    "requires_confirmation": requires_confirmation,
                    "rollback_plan": rollback_plan,
                    "estimated_impact": estimated_impact,
                },
            )
        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"[RecoveryAgent] Recovery failed after {total_duration:.2f}s: {e}", exc_info=True)
            logger.error("=" * 60)
            raise

    def _assess_risk(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "low"
        elif confidence >= 0.5:
            return "medium"
        return "high"

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        knowledge = {}
        if "recovery_playbooks" in knowledge_types:
            knowledge["recovery_playbooks"] = "恢复操作手册"
        if "safety_guidelines" in knowledge_types:
            knowledge["safety_guidelines"] = "安全操作规范"
        return knowledge
