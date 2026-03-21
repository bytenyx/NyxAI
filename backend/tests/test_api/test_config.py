import pytest
from app.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.APP_NAME == "NyxAI"
    assert settings.DEBUG is False
    assert settings.DATABASE_URL is not None


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    settings = Settings()
    assert settings.DEBUG is True
    assert "test.db" in settings.DATABASE_URL
