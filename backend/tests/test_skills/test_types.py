import pytest
from pathlib import Path
from app.skills.types import SkillMetadata, Skill

def test_skill_metadata_creation():
    metadata = SkillMetadata(
        name="test-skill",
        description="Test skill description",
        path=Path("/skills/test/SKILL.md")
    )
    assert metadata.name == "test-skill"
    assert metadata.description == "Test skill description"
    assert metadata.path == Path("/skills/test/SKILL.md")

def test_skill_creation():
    metadata = SkillMetadata(
        name="test-skill",
        description="Test skill description",
        path=Path("/skills/test/SKILL.md")
    )
    skill = Skill(
        metadata=metadata,
        content="# Test Skill\n\nContent here",
        supporting_files={"examples.md": "Example content"}
    )
    assert skill.metadata.name == "test-skill"
    assert skill.content == "# Test Skill\n\nContent here"
    assert skill.supporting_files["examples.md"] == "Example content"
