# Skill System Integration Design

## Overview

Integrate Anthropic-style skill system into NyxAI backend, enabling agents to discover and use skills through progressive disclosure. Skills are reference guides for proven techniques that help agents apply effective approaches.

## Requirements Summary

- **Target Users**: Backend agents (diagnosis, investigation, orchestrator, recovery)
- **Trigger Method**: Hybrid mode - LLM auto-detects from allowed skills list
- **Storage Location**: `backend/skills/` directory
- **Disclosure**: Metadata-first loading, full content on demand
- **Invocation**: Prompt injection
- **Update Mode**: Static loading at startup

## Architecture

### Directory Structure

```
backend/
  app/
    skills/
      __init__.py        # Export main classes
      registry.py        # SkillRegistry core class
      loader.py          # File system loader
      types.py           # SkillMetadata, Skill dataclasses
    skills/              # Skill files storage
      .gitkeep
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Startup                           │   │
│  │  registry = SkillRegistry(skills_dir)               │   │
│  │  registry.scan()                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   BaseAgent                          │   │
│  │  - allowed_skills: List[str]                        │   │
│  │  - build_skill_prompt() -> str                      │   │
│  │  - load_skill(name) -> Skill                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   LLMService                         │   │
│  │  generate(prompt, system_prompt with skills)        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Types

### SkillMetadata

```python
@dataclass
class SkillMetadata:
    name: str           # Skill name (from YAML frontmatter)
    description: str    # Skill description (from YAML frontmatter)
    path: Path          # Path to SKILL.md file
```

### Skill

```python
@dataclass
class Skill:
    metadata: SkillMetadata
    content: str                      # Full SKILL.md content
    supporting_files: Dict[str, str]  # Supporting files {filename: content}
```

## Core Components

### SkillLoader

Responsible for file system operations:

```python
class SkillLoader:
    def __init__(self, skills_dir: Path):
        self._skills_dir = skills_dir
    
    def discover_skills(self) -> List[Path]:
        """Find all SKILL.md files in skills directory"""
        
    def parse_frontmatter(self, path: Path) -> Optional[SkillMetadata]:
        """Parse YAML frontmatter from SKILL.md"""
        
    def load_skill_content(self, path: Path) -> str:
        """Load full SKILL.md content"""
        
    def load_supporting_files(self, skill_dir: Path) -> Dict[str, str]:
        """Load all supporting files in skill directory"""
```

### SkillRegistry

Central registry for skill management:

```python
class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self._loader = SkillLoader(skills_dir)
        self._metadata_index: Dict[str, SkillMetadata] = {}
        self._skills_cache: Dict[str, Skill] = {}
    
    def scan(self) -> None:
        """Scan directory and load all skill metadata"""
        
    def list_metadata(self) -> List[SkillMetadata]:
        """Return all skill metadata"""
        
    def get_metadata(self, names: List[str]) -> List[SkillMetadata]:
        """Get metadata for specified skills"""
        
    def load_skill(self, name: str) -> Skill:
        """Load full skill content on demand"""
        
    def has_skill(self, name: str) -> bool:
        """Check if skill exists"""
```

## Agent Integration

### AgentContext Extension

```python
@dataclass
class AgentContext:
    session_id: str
    query: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_skills: List[str] = field(default_factory=list)  # NEW
```

### BaseAgent Extension

```python
class BaseAgent(ABC):
    def __init__(self, name: str, skill_registry: Optional[SkillRegistry] = None):
        self.name = name
        self._skill_registry = skill_registry
    
    def build_skill_prompt(self, allowed_skills: List[str]) -> str:
        """Build skill metadata prompt for injection"""
        if not self._skill_registry or not allowed_skills:
            return ""
        
        metadata_list = self._skill_registry.get_metadata(allowed_skills)
        # Format as prompt section
        
    def load_skill(self, name: str) -> Optional[Skill]:
        """Load full skill content"""
        if not self._skill_registry:
            return None
        return self._skill_registry.load_skill(name)
```

## Prompt Format

### Metadata Injection

When agent has allowed skills, inject this into system prompt:

```
## Available Skills

You have access to the following skills. Load a skill when its description matches your current task:

- **brainstorming**: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior.
- **systematic-debugging**: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes.
- **test-driven-development**: Use when implementing any feature or bugfix, before writing implementation code.

To use a skill, respond with: `LOAD_SKILL: <skill_name>`
```

### Full Skill Content

When LLM requests a skill, inject:

```
## Skill: brainstorming

[Full SKILL.md content]

[Supporting files content if applicable]
```

## Configuration

Add to existing Settings:

```python
class Settings(BaseSettings):
    # Existing settings...
    
    SKILLS_DIR: str = "backend/skills"
```

## Error Handling

| Error | Handling |
|-------|----------|
| Skills directory not found | Log warning, continue with empty registry |
| Invalid SKILL.md (no frontmatter) | Log warning, skip skill |
| Invalid YAML frontmatter | Log warning, skip skill |
| Skill not found on load | Return None, log warning |
| File read error | Raise SkillLoadError |

## Testing Strategy

### Unit Tests

1. **SkillLoader**
   - Test frontmatter parsing with valid/invalid YAML
   - Test skill discovery in nested directories
   - Test supporting file loading

2. **SkillRegistry**
   - Test metadata indexing
   - Test skill loading and caching
   - Test error handling for missing skills

3. **BaseAgent Integration**
   - Test skill prompt generation
   - Test skill loading through agent

### Integration Tests

1. End-to-end skill loading flow
2. Agent execution with skill injection
3. LLM response parsing for skill requests

## Implementation Order

1. Create `types.py` with data classes
2. Create `loader.py` with SkillLoader
3. Create `registry.py` with SkillRegistry
4. Update `config.py` with SKILLS_DIR
5. Update `base.py` with skill integration
6. Add unit tests
7. Add integration tests

## Success Criteria

- [ ] Skills directory scanned at startup
- [ ] All skill metadata loaded into registry
- [ ] Agent can access allowed skills metadata
- [ ] Agent can load full skill content on demand
- [ ] Skill content properly formatted in prompts
- [ ] Error handling works correctly
- [ ] Unit tests pass
- [ ] Integration tests pass
