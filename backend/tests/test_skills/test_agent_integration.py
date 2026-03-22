import pytest
import tempfile
from pathlib import Path
from app.agents.base import AgentContext, BaseAgent
from app.skills.registry import SkillRegistry


def test_agent_context_allowed_skills():
    context = AgentContext(
        session_id="test-session",
        allowed_skills=["brainstorming", "debugging"]
    )
    assert context.allowed_skills == ["brainstorming", "debugging"]


def test_base_agent_skill_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        (skills_dir / "test").mkdir()
        (skills_dir / "test" / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test skill description\n---\n"
        )
        
        registry = SkillRegistry(skills_dir)
        registry.scan()
        
        agent = BaseAgent("test-agent", skill_registry=registry)
        prompt = agent.build_skill_prompt(["test"])
        
        assert "test" in prompt
        assert "Test skill description" in prompt


def test_base_agent_load_skill():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        skill_dir = skills_dir / "test"
        skill_dir.mkdir()
        skill_dir.joinpath("SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n# Test Skill"
        )
        
        registry = SkillRegistry(skills_dir)
        registry.scan()
        
        agent = BaseAgent("test-agent", skill_registry=registry)
        skill = agent.load_skill("test")
        
        assert skill is not None
        assert skill.metadata.name == "test"
        assert "# Test Skill" in skill.content
