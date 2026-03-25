import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.agents.diagnosis import DiagnosisAgent
from app.agents.investigation import InvestigationAgent
from app.agents.recovery import RecoveryAgent
from app.models.agent_config import AgentConfig


@pytest.mark.asyncio
async def test_diagnosis_agent_uses_config_prompt():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=AgentConfig(
        id="test-id",
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="自定义诊断提示词",
        allowed_skills=["brainstorming"],
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    
    agent = DiagnosisAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "自定义诊断提示词"


@pytest.mark.asyncio
async def test_diagnosis_agent_uses_default_when_no_config():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=None)
    
    agent = DiagnosisAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "默认提示词"


@pytest.mark.asyncio
async def test_investigation_agent_uses_config_prompt():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=AgentConfig(
        id="test-id-2",
        agent_type="investigation",
        name="调查配置",
        system_prompt="自定义调查提示词",
        allowed_skills=[],
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    
    agent = InvestigationAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "自定义调查提示词"


@pytest.mark.asyncio
async def test_recovery_agent_uses_config_prompt():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=AgentConfig(
        id="test-id-3",
        agent_type="recovery",
        name="恢复配置",
        system_prompt="自定义恢复提示词",
        allowed_skills=["systematic-debugging"],
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    
    agent = RecoveryAgent(config_repo=mock_repo)
    await agent.load_config()
    
    prompt = agent.get_system_prompt("默认提示词")
    assert prompt == "自定义恢复提示词"


@pytest.mark.asyncio
async def test_agent_get_allowed_skills_from_config():
    mock_repo = MagicMock()
    mock_repo.get_by_type = AsyncMock(return_value=AgentConfig(
        id="test-id-4",
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="提示词",
        allowed_skills=["brainstorming", "systematic-debugging"],
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ))
    
    agent = DiagnosisAgent(config_repo=mock_repo)
    await agent.load_config()
    
    skills = agent.get_allowed_skills()
    assert skills == ["brainstorming", "systematic-debugging"]
