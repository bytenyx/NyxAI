import pytest
from app.skills.registry import SkillRegistry


def test_registry_basic_functionality():
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = SkillRegistry(Path(tmpdir))
        assert registry.list_metadata() == []
        assert not registry.has_skill("any-skill")
        assert registry.get_metadata([]) == []
        assert registry.load_skill("nonexistent") is None
