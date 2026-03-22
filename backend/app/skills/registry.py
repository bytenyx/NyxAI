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

    def get_metadata(self, names: List[str]) -> List[SkillMetadata]:
        result = []
        for name in names:
            if name in self._metadata_index:
                result.append(self._metadata_index[name])
        return result

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
