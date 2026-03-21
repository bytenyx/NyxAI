from typing import Any, Dict, List

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.services.llm import LLMConfig, LLMService


class RecoveryAgent(BaseAgent):
    def __init__(self, llm_service: LLMService = None):
        super().__init__(name="recovery")
        self.llm = llm_service or LLMService(LLMConfig(provider="mock", model="mock"))

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query or ""
        root_cause = context.metadata.get("root_cause", "")
        confidence = context.metadata.get("confidence", 0.5)
        
        system_prompt = """你是一个故障恢复专家。你的任务是基于根因分析结果，
制定恢复方案，评估风险等级。

请返回JSON格式的结果，包含：
1. actions: 恢复操作列表
2. risk_level: 风险等级(low/medium/high)
3. requires_confirmation: 是否需要确认
4. rollback_plan: 回滚方案"""
        
        prompt = f"""请为以下问题制定恢复方案：
问题：{query}
根因：{root_cause}
置信度：{confidence}"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        risk_level = self._assess_risk(confidence)
        
        return AgentResult(
            success=True,
            data={
                "actions": [
                    {
                        "action_type": "investigate",
                        "description": "进一步调查确认",
                        "risk_level": "low",
                    }
                ],
                "risk_level": risk_level,
                "requires_confirmation": risk_level != "low",
                "rollback_plan": "暂无回滚方案",
                "estimated_impact": "低风险操作",
            },
        )

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
