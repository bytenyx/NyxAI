import pytest
import tempfile
from pathlib import Path
from app.skills.registry import SkillRegistry


def test_registry_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = SkillRegistry(Path(tmpdir))
        assert registry.list_metadata() == []
        assert not registry.has_skill("any-skill")


def test_scan_skills():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        (skills_dir / "brainstorming").mkdir()
        (skills_dir / "brainstorming" / "SKILL.md").write_text(
            "---\nname: brainstorming\ndescription: Use before creative work\n---\n"
        )
        
        (skills_dir / "debugging").mkdir()
        (skills_dir / "debugging" / "SKILL.md").write_text(
            "---\nname: systematic-debugging\ndescription: Use for debugging\n---\n"
        )
        
        registry = SkillRegistry(skills_dir)
        registry.scan()
        
        metadata_list = registry.list_metadata()
        assert len(metadata_list) == 2
        assert registry.has_skill("brainstorming")
        assert registry.has_skill("systematic-debugging")


def test_get_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        (skills_dir / "test").mkdir()
        (skills_dir / "test" / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test skill\n---\n"
        )
        
        registry = SkillRegistry(skills_dir)
        registry.scan()
        
        metadata_list = registry.get_metadata(["test", "nonexistent"])
        assert len(metadata_list) == 1
        assert metadata_list[0].name == "test"


def test_load_skill():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        skill_dir = skills_dir / "test"
        skill_dir.mkdir()
        skill_dir.joinpath("SKILL.md").write_text(
            "---\nname: test\ndescription: Test skill\n---\n# Test Skill\n\nContent"
        )
        skill_dir.joinpath("examples.md").write_text("Example content")
        
        registry = SkillRegistry(skills_dir)
        registry.scan()
        
        skill = registry.load_skill("test")
        assert skill is not None
        assert skill.metadata.name == "test"
        assert "# Test Skill" in skill.content
        assert skill.supporting_files["examples.md"] == "Example content"
