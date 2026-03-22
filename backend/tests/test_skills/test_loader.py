import pytest
import tempfile
from pathlib import Path
from app.skills.loader import SkillLoader
from app.skills.types import SkillMetadata


def test_parse_frontmatter_valid():
    loader = SkillLoader(Path("/tmp/skills"))
    test_content = """---
name: test-skill
description: Test skill for parsing
---
# Skill Content
"""
    metadata = loader.parse_frontmatter(test_content)
    assert metadata is not None
    assert metadata.name == "test-skill"
    assert metadata.description == "Test skill for parsing"


def test_parse_frontmatter_invalid():
    loader = SkillLoader(Path("/tmp/skills"))
    
    assert loader.parse_frontmatter("No frontmatter here") is None
    assert loader.parse_frontmatter("---\ninvalid yaml\n---\n") is None
    assert loader.parse_frontmatter("---\nname: only-name\n---\n") is None


def test_discover_skills():
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()
        
        (skills_dir / "skill1").mkdir()
        (skills_dir / "skill1" / "SKILL.md").write_text("---\nname: skill1\ndescription: Test\n---\n")
        
        (skills_dir / "skill2").mkdir()
        (skills_dir / "skill2" / "SKILL.md").write_text("---\nname: skill2\ndescription: Test 2\n---\n")
        
        (skills_dir / "no-skill").mkdir()
        (skills_dir / "no-skill" / "README.md").write_text("No skill here")
        
        loader = SkillLoader(skills_dir)
        skill_files = loader.discover_skills()
        
        assert len(skill_files) == 2
        assert any("skill1" in str(f) for f in skill_files)
        assert any("skill2" in str(f) for f in skill_files)


def test_load_skill_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nContent here")
        
        loader = SkillLoader(Path(tmpdir))
        content = loader.load_skill_content(skill_file)
        
        assert content == "# Test Skill\n\nContent here"


def test_load_supporting_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        
        (skill_dir / "examples.md").write_text("Example content")
        (skill_dir / "reference.md").write_text("Reference content")
        (skill_dir / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n")
        
        loader = SkillLoader(Path(tmpdir))
        files = loader.load_supporting_files(skill_dir)
        
        assert len(files) == 2
        assert files["examples.md"] == "Example content"
        assert files["reference.md"] == "Reference content"
