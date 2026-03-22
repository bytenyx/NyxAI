# Skill System Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Anthropic-style skill system into NyxAI backend, enabling agents to discover and use skills through progressive disclosure.

**Architecture:** Lightweight Skill Registry with metadata-first loading. Skills are stored in `backend/skills/`, metadata indexed at startup, full content loaded on demand via prompt injection.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest

---

### Task 1: Create Skill Data Types

**Files:**
- Create: `backend/app/skills/__init__.py`
- Create: `backend/app/skills/types.py`
- Test: `backend/tests/test_skills/__init__.py`
- Test: `backend/tests/test_skills/test_types.py`

- [ ] **Step 1: Create skills package init file**

```python
from .types import Skill, SkillMetadata, SkillLoadError
from .loader import SkillLoader
from .registry import SkillRegistry

__all__ = ["Skill", "SkillMetadata", "SkillLoadError", "SkillLoader", "SkillRegistry"]
```

- [ ] **Step 2: Write failing test for SkillMetadata**

```python
import pytest
from pathlib import Path
from app.skills.types import SkillMetadata

def test_skill_metadata_creation():
    metadata = SkillMetadata(
        name="test-skill",
        description="Test skill description",
        path=Path("/skills/test/SKILL.md")
    )
    assert metadata.name == "test-skill"
    assert metadata.description == "Test skill description"
    assert str(metadata.path) == "/skills/test/SKILL.md"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_types.py::test_skill_metadata_creation -v`
Expected: FAIL with "cannot import 'SkillMetadata' from 'app.skills.types'"

- [ ] **Step 4: Implement SkillMetadata and Skill dataclasses**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class SkillLoadError(Exception):
    pass


@dataclass
class SkillMetadata:
    name: str
    description: str
    path: Path


@dataclass
class Skill:
    metadata: SkillMetadata
    content: str
    supporting_files: Dict[str, str] = field(default_factory=dict)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_types.py::test_skill_metadata_creation -v`
Expected: PASS

- [ ] **Step 6: Write test for Skill dataclass**

```python
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
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_types.py::test_skill_creation -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/skills/__init__.py backend/app/skills/types.py backend/tests/test_skills/__init__.py backend/tests/test_skills/test_types.py
git commit -m "feat: add skill data types (SkillMetadata, Skill, SkillLoadError)"
```

---

### Task 2: Implement SkillLoader

**Files:**
- Create: `backend/app/skills/loader.py`
- Test: `backend/tests/test_skills/test_loader.py`

- [ ] **Step 1: Write failing test for frontmatter parsing**

```python
import pytest
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_loader.py::test_parse_frontmatter_valid -v`
Expected: FAIL with "cannot import 'SkillLoader' from 'app.skills.loader'"

- [ ] **Step 3: Implement SkillLoader.parse_frontmatter**

```python
import re
from pathlib import Path
from typing import Optional, List
from app.skills.types import SkillMetadata, SkillLoadError


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self._skills_dir = skills_dir

    def parse_frontmatter(self, content: str) -> Optional[SkillMetadata]:
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None

        yaml_content = match.group(1)
        try:
            import yaml
            data = yaml.safe_load(yaml_content)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None

        name = data.get("name")
        description = data.get("description")

        if not name or not description:
            return None

        return SkillMetadata(name=name, description=description, path=Path())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_loader.py::test_parse_frontmatter_valid -v`
Expected: PASS

- [ ] **Step 5: Write test for invalid frontmatter**

```python
def test_parse_frontmatter_invalid():
    loader = SkillLoader(Path("/tmp/skills"))
    
    assert loader.parse_frontmatter("No frontmatter here") is None
    assert loader.parse_frontmatter("---\ninvalid yaml\n---\n") is None
    assert loader.parse_frontmatter("---\nname: only-name\n---\n") is None
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_loader.py::test_parse_frontmatter_invalid -v`
Expected: PASS

- [ ] **Step 7: Write test for discover_skills**

```python
import tempfile
import os

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
```

- [ ] **Step 8: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_loader.py::test_discover_skills -v`
Expected: FAIL with "SkillLoader has no attribute 'discover_skills'"

- [ ] **Step 9: Implement SkillLoader.discover_skills**

```python
def discover_skills(self) -> List[Path]:
    if not self._skills_dir.exists():
        return []
    
    skill_files = []
    for skill_dir in self._skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill_files.append(skill_file)
    
    return skill_files
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_loader.py::test_discover_skills -v`
Expected: PASS

- [ ] **Step 11: Write test for load_skill_content**

```python
def test_load_skill_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nContent here")
        
        loader = SkillLoader(Path(tmpdir))
        content = loader.load_skill_content(skill_file)
        
        assert content == "# Test Skill\n\nContent here"
```

- [ ] **Step 12: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_loader.py::test_load_skill_content -v`
Expected: FAIL with "SkillLoader has no attribute 'load_skill_content'"

- [ ] **Step 13: Implement SkillLoader.load_skill_content**

```python
def load_skill_content(self, path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise SkillLoadError(f"Failed to read skill file {path}: {e}")
```

- [ ] **Step 14: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_loader.py::test_load_skill_content -v`
Expected: PASS

- [ ] **Step 15: Write test for load_supporting_files**

```python
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
```

- [ ] **Step 16: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_loader.py::test_load_supporting_files -v`
Expected: FAIL with "SkillLoader has no attribute 'load_supporting_files'"

- [ ] **Step 17: Implement SkillLoader.load_supporting_files**

```python
def load_supporting_files(self, skill_dir: Path) -> Dict[str, str]:
    if not skill_dir.exists():
        return {}
    
    supporting_files = {}
    for file_path in skill_dir.iterdir():
        if file_path.is_file() and file_path.name != "SKILL.md":
            try:
                supporting_files[file_path.name] = file_path.read_text(encoding="utf-8")
            except Exception:
                pass
    
    return supporting_files
```

- [ ] **Step 18: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_loader.py::test_load_supporting_files -v`
Expected: PASS

- [ ] **Step 19: Commit**

```bash
git add backend/app/skills/loader.py backend/tests/test_skills/test_loader.py
git commit -m "feat: implement SkillLoader with frontmatter parsing and file loading"
```

---

### Task 3: Implement SkillRegistry

**Files:**
- Create: `backend/app/skills/registry.py`
- Test: `backend/tests/test_skills/test_registry.py`

- [ ] **Step 1: Write failing test for registry initialization**

```python
import pytest
import tempfile
from pathlib import Path
from app.skills.registry import SkillRegistry

def test_registry_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = SkillRegistry(Path(tmpdir))
        assert registry.list_metadata() == []
        assert not registry.has_skill("any-skill")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_registry.py::test_registry_initialization -v`
Expected: FAIL with "cannot import 'SkillRegistry' from 'app.skills.registry'"

- [ ] **Step 3: Implement SkillRegistry.__init__ and basic methods**

```python
from pathlib import Path
from typing import Dict, List, Optional
from app.skills.loader import SkillLoader
from app.skills.types import Skill, SkillMetadata, SkillLoadError


class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self._skills_dir = skills_dir
        self._loader = SkillLoader(skills_dir)
        self._metadata_index: Dict[str, SkillMetadata] = {}
        self._skills_cache: Dict[str, Skill] = {}

    def list_metadata(self) -> List[SkillMetadata]:
        return list(self._metadata_index.values())

    def has_skill(self, name: str) -> bool:
        return name in self._metadata_index
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_registry.py::test_registry_initialization -v`
Expected: PASS

- [ ] **Step 5: Write test for scan method**

```python
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
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_registry.py::test_scan_skills -v`
Expected: FAIL with "SkillRegistry has no attribute 'scan'"

- [ ] **Step 7: Implement SkillRegistry.scan**

```python
def scan(self) -> None:
    if not self._skills_dir.exists():
        return
    
    skill_files = self._loader.discover_skills()
    for skill_file in skill_files:
        try:
            content = self._loader.load_skill_content(skill_file)
            metadata = self._loader.parse_frontmatter(content)
            if metadata:
                metadata.path = skill_file
                self._metadata_index[metadata.name] = metadata
        except Exception:
            pass
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_registry.py::test_scan_skills -v`
Expected: PASS

- [ ] **Step 9: Write test for get_metadata**

```python
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
```

- [ ] **Step 10: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_registry.py::test_get_metadata -v`
Expected: FAIL with "SkillRegistry has no attribute 'get_metadata'"

- [ ] **Step 11: Implement SkillRegistry.get_metadata**

```python
def get_metadata(self, names: List[str]) -> List[SkillMetadata]:
    result = []
    for name in names:
        if name in self._metadata_index:
            result.append(self._metadata_index[name])
    return result
```

- [ ] **Step 12: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_registry.py::test_get_metadata -v`
Expected: PASS

- [ ] **Step 13: Write test for load_skill**

```python
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
```

- [ ] **Step 14: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_registry.py::test_load_skill -v`
Expected: FAIL with "SkillRegistry has no attribute 'load_skill'"

- [ ] **Step 15: Implement SkillRegistry.load_skill**

```python
def load_skill(self, name: str) -> Optional[Skill]:
    if name not in self._metadata_index:
        return None
    
    if name in self._skills_cache:
        return self._skills_cache[name]
    
    metadata = self._metadata_index[name]
    try:
        content = self._loader.load_skill_content(metadata.path)
        skill_dir = metadata.path.parent
        supporting_files = self._loader.load_supporting_files(skill_dir)
        
        skill = Skill(
            metadata=metadata,
            content=content,
            supporting_files=supporting_files
        )
        self._skills_cache[name] = skill
        return skill
    except SkillLoadError:
        return None
```

- [ ] **Step 16: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_registry.py::test_load_skill -v`
Expected: PASS

- [ ] **Step 17: Commit**

```bash
git add backend/app/skills/registry.py backend/tests/test_skills/test_registry.py
git commit -m "feat: implement SkillRegistry with metadata indexing and skill loading"
```

---

### Task 4: Add Configuration

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Write failing test for SKILLS_DIR config**

```python
from app.config import get_settings

def test_skills_dir_config():
    settings = get_settings()
    assert hasattr(settings, "SKILLS_DIR")
    assert settings.SKILLS_DIR == "backend/skills"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_api/test_config.py::test_skills_dir_config -v`
Expected: FAIL with "Settings object has no attribute 'SKILLS_DIR'"

- [ ] **Step 3: Add SKILLS_DIR to Settings class**

```python
class Settings(BaseSettings):
    APP_NAME: str = "NyxAI"
    ENVIRONMENT: str = "development"
    
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    
    SKILLS_DIR: str = "backend/skills"
    
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_api/test_config.py::test_skills_dir_config -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_api/test_config.py
git commit -m "feat: add SKILLS_DIR configuration"
```

---

### Task 5: Integrate with BaseAgent

**Files:**
- Modify: `backend/app/agents/base.py`
- Test: `backend/tests/test_skills/test_agent_integration.py`

- [ ] **Step 1: Write failing test for AgentContext.allowed_skills**

```python
from app.agents.base import AgentContext

def test_agent_context_allowed_skills():
    context = AgentContext(
        session_id="test-session",
        allowed_skills=["brainstorming", "debugging"]
    )
    assert context.allowed_skills == ["brainstorming", "debugging"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_agent_context_allowed_skills -v`
Expected: FAIL with "AgentContext object has no attribute 'allowed_skills'"

- [ ] **Step 3: Add allowed_skills to AgentContext**

```python
@dataclass
class AgentContext:
    session_id: str
    query: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_skills: List[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_agent_context_allowed_skills -v`
Expected: PASS

- [ ] **Step 5: Write failing test for BaseAgent skill integration**

```python
from app.agents.base import BaseAgent
from app.skills.registry import SkillRegistry
import tempfile
from pathlib import Path

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
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_base_agent_skill_prompt -v`
Expected: FAIL with "BaseAgent.__init__() got an unexpected keyword argument 'skill_registry'"

- [ ] **Step 7: Add skill_registry to BaseAgent**

```python
from typing import Optional
from app.skills.registry import SkillRegistry
from app.skills.types import Skill

class BaseAgent(ABC):
    def __init__(self, name: str, skill_registry: Optional[SkillRegistry] = None):
        self.name = name
        self._skill_registry = skill_registry
```

- [ ] **Step 8: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_base_agent_skill_prompt -v`
Expected: FAIL with "BaseAgent has no attribute 'build_skill_prompt'"

- [ ] **Step 9: Implement BaseAgent.build_skill_prompt**

```python
def build_skill_prompt(self, allowed_skills: List[str]) -> str:
    if not self._skill_registry or not allowed_skills:
        return ""
    
    metadata_list = self._skill_registry.get_metadata(allowed_skills)
    if not metadata_list:
        return ""
    
    lines = ["## Available Skills", ""]
    lines.append("You have access to the following skills. Load a skill when its description matches your current task:")
    lines.append("")
    
    for metadata in metadata_list:
        lines.append(f"- **{metadata.name}**: {metadata.description}")
    
    lines.append("")
    lines.append("To use a skill, respond with: `LOAD_SKILL: <skill_name>`")
    
    return "\n".join(lines)
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_base_agent_skill_prompt -v`
Expected: PASS

- [ ] **Step 11: Write test for load_skill method**

```python
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
```

- [ ] **Step 12: Run test to verify it fails**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_base_agent_load_skill -v`
Expected: FAIL with "BaseAgent has no attribute 'load_skill'"

- [ ] **Step 13: Implement BaseAgent.load_skill**

```python
def load_skill(self, name: str) -> Optional[Skill]:
    if not self._skill_registry:
        return None
    return self._skill_registry.load_skill(name)
```

- [ ] **Step 14: Run test to verify it passes**

Run: `pytest backend/tests/test_skills/test_agent_integration.py::test_base_agent_load_skill -v`
Expected: PASS

- [ ] **Step 15: Commit**

```bash
git add backend/app/agents/base.py backend/tests/test_skills/test_agent_integration.py
git commit -m "feat: integrate skill system with BaseAgent"
```

---

### Task 6: Initialize Registry in FastAPI App

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/skills/.gitkeep`

- [ ] **Step 1: Create skills directory placeholder**

```bash
mkdir -p backend/skills
touch backend/skills/.gitkeep
```

- [ ] **Step 2: Write failing test for registry initialization**

```python
from app.main import app
from app.skills.registry import SkillRegistry

def test_registry_initialized():
    assert hasattr(app.state, "skill_registry")
    assert isinstance(app.state.skill_registry, SkillRegistry)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest backend/tests/test_api/test_main.py::test_registry_initialized -v`
Expected: FAIL with "App state has no attribute 'skill_registry'"

- [ ] **Step 4: Initialize SkillRegistry in lifespan**

```python
from app.skills.registry import SkillRegistry
from app.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    settings = get_settings()
    skills_dir = Path(settings.SKILLS_DIR)
    skill_registry = SkillRegistry(skills_dir)
    skill_registry.scan()
    app.state.skill_registry = skill_registry
    
    yield
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest backend/tests/test_api/test_main.py::test_registry_initialized -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/skills/.gitkeep backend/tests/test_api/test_main.py
git commit -m "feat: initialize SkillRegistry in FastAPI app lifespan"
```

---

### Task 7: Add Sample Skills

**Files:**
- Create: `backend/skills/brainstorming/SKILL.md`
- Create: `backend/skills/systematic-debugging/SKILL.md`

- [ ] **Step 1: Create brainstorming skill**

```bash
mkdir -p backend/skills/brainstorming
```

```markdown
---
name: brainstorming
description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea.
```

- [ ] **Step 2: Create systematic-debugging skill**

```bash
mkdir -p backend/skills/systematic-debugging
```

```markdown
---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes.
---

# Systematic Debugging

Follow a structured approach to identify root causes of bugs and failures.

1. Reproduce the issue
2. Gather evidence
3. Form hypotheses
4. Test hypotheses
5. Verify fix
```

- [ ] **Step 3: Commit**

```bash
git add backend/skills/brainstorming/SKILL.md backend/skills/systematic-debugging/SKILL.md
git commit -m "feat: add sample skills (brainstorming, systematic-debugging)"
```

---

### Task 8: Run All Tests

**Files:**
- No new files

- [ ] **Step 1: Run all skill-related tests**

Run: `pytest backend/tests/test_skills/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run all backend tests**

Run: `pytest backend/tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Verify FastAPI app starts**

Run: `cd backend && python -m uvicorn app.main:app --reload`
Expected: App starts without errors, health check returns 200

- [ ] **Step 4: Commit**

```bash
git commit --allow-empty -m "test: verify all tests pass and app starts successfully"
```

---

## Success Criteria Verification

- [ ] Skills directory scanned at startup
- [ ] All skill metadata loaded into registry
- [ ] Agent can access allowed skills metadata
- [ ] Agent can load full skill content on demand
- [ ] Skill content properly formatted in prompts
- [ ] Error handling works correctly
- [ ] Unit tests pass
- [ ] Integration tests pass
