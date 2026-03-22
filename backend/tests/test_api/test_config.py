import pytest
from app.config import get_settings


def test_skills_dir_config():
    settings = get_settings()
    assert hasattr(settings, "SKILLS_DIR")
    assert settings.SKILLS_DIR == "backend/skills"
