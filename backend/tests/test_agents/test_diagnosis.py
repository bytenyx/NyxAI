import pytest

from app.agents.base import AgentContext, AgentResult
from app.agents.diagnosis import DiagnosisAgent
from app.services.llm import LLMService, LLMConfig


class TestDiagnosisAgent:
    @pytest.fixture
    def llm_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

    @pytest.fixture
    def agent(self, llm_service):
        return DiagnosisAgent(llm_service=llm_service)

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
            metadata={
                "investigation_summary": "发现异常",
                "confidence": 0.8,
            },
        )
        result = await agent.execute(context)
        
        assert result.success is True
        assert "root_cause" in result.data
        assert "confidence" in result.data
        assert "evidence_chain" in result.data
        assert "affected_components" in result.data

    @pytest.mark.asyncio
    async def test_execute_returns_evidence_chain(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="CPU使用率过高",
            metadata={
                "investigation_summary": "发现CPU异常",
            },
        )
        result = await agent.execute(context)
        
        assert len(result.data["evidence_chain"]) > 0
        assert len(result.evidence) > 0

    @pytest.mark.asyncio
    async def test_execute_with_investigation_context(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="服务响应慢",
            metadata={
                "investigation_summary": "数据库查询慢",
                "anomalies": [{"name": "slow_query", "severity": "high"}],
                "confidence": 0.9,
            },
        )
        result = await agent.execute(context)
        
        assert result.success is True
        assert result.data["confidence"] >= 0
        assert result.data["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_load_knowledge(self, agent):
        knowledge = await agent.load_knowledge(["fault_patterns", "causal_rules"])
        
        assert "fault_patterns" in knowledge
        assert "causal_rules" in knowledge
