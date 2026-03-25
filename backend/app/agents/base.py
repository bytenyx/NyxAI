from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from app.skills.registry import SkillRegistry
from app.skills.types import Skill

if TYPE_CHECKING:
    from app.models.agent_config import AgentConfig
    from app.storage.repositories.agent_config_repo import AgentConfigRepository


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
    def __init__(
        self,
        name: str,
        skill_registry: Optional[SkillRegistry] = None,
        config_repo: Optional["AgentConfigRepository"] = None,
    ):
        self.name = name
        self._skill_registry = skill_registry
        self._config_repo = config_repo
        self._config: Optional["AgentConfig"] = None

    async def load_config(self) -> Optional["AgentConfig"]:
        if not self._config_repo:
            return None
        config = await self._config_repo.get_by_type(self.name)
        if config:
            self._config = config
        return config

    def get_system_prompt(self, default: str = "") -> str:
        if self._config:
            return self._config.system_prompt
        return default

    def get_allowed_skills(self, default: List[str] = None) -> List[str]:
        if self._config:
            return self._config.allowed_skills
        return default or []

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    async def load_knowledge(self, knowledge_types: List[str]) -> Dict[str, Any]:
        return {}

    def build_skill_prompt(self, allowed_skills: List[str] = None) -> str:
        skills = allowed_skills or self.get_allowed_skills()
        if not self._skill_registry or not skills:
            return ""
        
        metadata_list = self._skill_registry.get_metadata(skills)
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
