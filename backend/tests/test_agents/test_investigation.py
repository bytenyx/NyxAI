import pytest
from datetime import datetime

from app.agents.base import AgentContext, AgentResult
from app.agents.investigation import InvestigationAgent
from app.services.llm import LLMService, LLMConfig


class TestInvestigationAgent:
    @pytest.fixture
    def llm_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

    @pytest.fixture
    def agent(self, llm_service):
        return InvestigationAgent(llm_service=llm_service)

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        result = await agent.execute(context)
        
        assert result.success is True
        assert "summary" in result.data
        assert "anomalies" in result.data
        assert "confidence" in result.data
        assert len(result.evidence) > 0

    @pytest.mark.asyncio
    async def test_execute_with_empty_query(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="",
        )
        result = await agent.execute(context)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_returns_evidence(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="CPU使用率过高",
        )
        result = await agent.execute(context)
        
        assert len(result.evidence) > 0
        assert result.evidence[0].source_system == "investigation_agent"

    @pytest.mark.asyncio
    async def test_load_knowledge(self, agent):
        knowledge = await agent.load_knowledge(["metric_definitions", "log_patterns"])
        
        assert "metric_definitions" in knowledge
        assert "log_patterns" in knowledge
