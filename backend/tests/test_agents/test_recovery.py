import pytest

from app.agents.base import AgentContext, AgentResult
from app.agents.recovery import RecoveryAgent
from app.services.llm import LLMService, LLMConfig


class TestRecoveryAgent:
    @pytest.fixture
    def llm_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

    @pytest.fixture
    def agent(self, llm_service):
        return RecoveryAgent(llm_service=llm_service)

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
            metadata={
                "root_cause": "测试根因",
                "confidence": 0.8,
            },
        )
        result = await agent.execute(context)
        
        assert result.success is True
        assert "actions" in result.data
        assert "risk_level" in result.data
        assert "requires_confirmation" in result.data

    @pytest.mark.asyncio
    async def test_execute_returns_actions(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="CPU使用率过高",
            metadata={
                "root_cause": "内存泄漏导致频繁GC",
                "confidence": 0.85,
            },
        )
        result = await agent.execute(context)
        
        assert len(result.data["actions"]) > 0
        assert "action_type" in result.data["actions"][0]
        assert "description" in result.data["actions"][0]

    @pytest.mark.asyncio
    async def test_assess_risk_high_confidence(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试",
            metadata={
                "root_cause": "已知问题",
                "confidence": 0.9,
            },
        )
        result = await agent.execute(context)
        
        assert result.data["risk_level"] == "low"

    def test_assess_risk_medium_confidence(self, agent):
        assert agent._assess_risk(0.6) == "medium"
        assert agent._assess_risk(0.5) == "medium"
        assert agent._assess_risk(0.7) == "medium"

    def test_assess_risk_low_confidence(self, agent):
        assert agent._assess_risk(0.3) == "high"
        assert agent._assess_risk(0.1) == "high"
        assert agent._assess_risk(0.49) == "high"

    @pytest.mark.asyncio
    async def test_load_knowledge(self, agent):
        knowledge = await agent.load_knowledge(["recovery_playbooks", "safety_guidelines"])
        
        assert "recovery_playbooks" in knowledge
        assert "safety_guidelines" in knowledge
