import pytest
from app.models.agent_config import AgentConfig, AgentConfigCreate, AgentConfigUpdate


def test_agent_config_create():
    config = AgentConfigCreate(
        agent_type="diagnosis",
        name="测试配置",
        system_prompt="你是一个诊断专家",
        allowed_skills=["brainstorming"]
    )
    assert config.agent_type == "diagnosis"
    assert config.name == "测试配置"
    assert config.system_prompt == "你是一个诊断专家"
    assert config.allowed_skills == ["brainstorming"]


def test_agent_config_update():
    update = AgentConfigUpdate(
        system_prompt="更新后的提示词",
        change_reason="优化诊断"
    )
    assert update.system_prompt == "更新后的提示词"
    assert update.change_reason == "优化诊断"
    assert update.name is None


def test_agent_config_allowed_skills_default():
    config = AgentConfigCreate(
        agent_type="investigation",
        name="默认配置",
        system_prompt="测试"
    )
    assert config.allowed_skills == []
