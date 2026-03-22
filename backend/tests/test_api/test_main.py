import pytest
from app.main import app
from app.skills.registry import SkillRegistry


def test_registry_initialized():
    assert hasattr(app.state, "skill_registry")
    assert isinstance(app.state.skill_registry, SkillRegistry)
