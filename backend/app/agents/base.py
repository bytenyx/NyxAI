from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.skills.registry import SkillRegistry
from app.skills.types import Skill


@dataclass
class AgentContext:
    session_id: str
    query: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_skills: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    evidence: List[Any] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(self, name: str, skill_registry: Optional[SkillRegistry] = None):
        self.name = name
        self._skill_registry = skill_registry

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        return {}

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

    def load_skill(self, name: str) -> Optional[Skill]:
        if not self._skill_registry:
            return None
        return self._skill_registry.load_skill(name)
