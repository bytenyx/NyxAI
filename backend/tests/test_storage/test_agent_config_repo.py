import pytest
from app.storage.repositories.agent_config_repo import AgentConfigRepository
from app.models.agent_config import AgentConfigCreate, AgentConfigUpdate


@pytest.mark.asyncio
async def test_create_config(db_session):
    repo = AgentConfigRepository(db_session)
    config = await repo.create(AgentConfigCreate(
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="你是一个诊断专家",
        allowed_skills=["brainstorming"]
    ))
    
    assert config.id is not None
    assert config.agent_type == "diagnosis"
    assert config.is_active == True


@pytest.mark.asyncio
async def test_get_by_type(db_session):
    repo = AgentConfigRepository(db_session)
    await repo.create(AgentConfigCreate(
        agent_type="investigation",
        name="调查配置",
        system_prompt="你是一个调查专家",
        allowed_skills=[]
    ))
    
    config = await repo.get_by_type("investigation")
    assert config is not None
    assert config.agent_type == "investigation"


@pytest.mark.asyncio
async def test_update_creates_version(db_session):
    repo = AgentConfigRepository(db_session)
    created = await repo.create(AgentConfigCreate(
        agent_type="recovery",
        name="恢复配置",
        system_prompt="原始提示词",
        allowed_skills=[]
    ))
    
    updated = await repo.update(created.id, AgentConfigUpdate(
        system_prompt="更新后的提示词",
        change_reason="测试更新"
    ))
    
    assert updated.system_prompt == "更新后的提示词"
    
    versions = await repo.get_versions(created.id)
    assert len(versions) == 1
    assert versions[0].system_prompt == "原始提示词"
