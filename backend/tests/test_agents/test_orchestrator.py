import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.base import AgentContext, AgentResult
from app.agents.orchestrator import OrchestratorAgent
from app.agents.investigation import InvestigationAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.recovery import RecoveryAgent
from app.models.session import SessionStatus
from app.services.llm import LLMService, LLMConfig


class TestOrchestratorAgent:
    @pytest.fixture
    def llm_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

    @pytest.fixture
    def mock_session_repo(self):
        repo = MagicMock()
        repo.update_status = AsyncMock()
        repo.update_session = AsyncMock()
        return repo

    @pytest.fixture
    def mock_evidence_repo(self):
        repo = MagicMock()
        repo.create_batch = AsyncMock()
        return repo

    @pytest.fixture
    def agent(self, llm_service, mock_session_repo, mock_evidence_repo):
        return OrchestratorAgent(
            session_repo=mock_session_repo,
            evidence_repo=mock_evidence_repo,
            investigation_agent=InvestigationAgent(llm_service=llm_service),
            diagnosis_agent=DiagnosisAgent(llm_service=llm_service),
            recovery_agent=RecoveryAgent(llm_service=llm_service),
        )

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        result = await agent.execute(context)
        
        assert result.success is True
        assert result.data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_updates_session_status(self, agent, mock_session_repo):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        await agent.execute(context)
        
        mock_session_repo.update_session.assert_called()
        
        calls = mock_session_repo.update_session.call_args_list
        status_values = [call.kwargs.get('status') for call in calls if call.kwargs.get('status')]
        
        assert SessionStatus.DIAGNOSING in status_values
        assert SessionStatus.RECOVERING in status_values
        assert SessionStatus.COMPLETED in status_values

    @pytest.mark.asyncio
    async def test_execute_persists_evidence(self, agent, mock_evidence_repo):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        await agent.execute(context)
        
        assert mock_evidence_repo.create_batch.call_count >= 2

    @pytest.mark.asyncio
    async def test_execute_returns_all_results(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        result = await agent.execute(context)
        
        assert "investigation" in result.data
        assert "diagnosis" in result.data
        assert "recovery" in result.data

    @pytest.mark.asyncio
    async def test_execute_collects_evidence(self, agent):
        context = AgentContext(
            session_id="test-session",
            query="测试问题",
        )
        result = await agent.execute(context)
        
        assert len(result.evidence) > 0

    @pytest.mark.asyncio
    async def test_agent_dependency_injection(self, llm_service):
        custom_investigation = InvestigationAgent(llm_service=llm_service)
        custom_diagnosis = DiagnosisAgent(llm_service=llm_service)
        custom_recovery = RecoveryAgent(llm_service=llm_service)
        
        orchestrator = OrchestratorAgent(
            investigation_agent=custom_investigation,
            diagnosis_agent=custom_diagnosis,
            recovery_agent=custom_recovery,
        )
        
        assert orchestrator.investigation is custom_investigation
        assert orchestrator.diagnosis is custom_diagnosis
        assert orchestrator.recovery is custom_recovery
