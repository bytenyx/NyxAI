from pathlib import Path
from typing import Dict, List, Optional
from app.skills.loader import SkillLoader
from app.skills.types import Skill, SkillMetadata, SkillLoadError
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        logger.info(f"[SkillRegistry] Scanning skills directory: {self._skills_dir}")
        if not self._skills_dir.exists():
            logger.warning(f"[SkillRegistry] Skills directory does not exist: {self._skills_dir}")
            return
        
        skill_files = self._loader.discover_skills()
        logger.info(f"[SkillRegistry] Found {len(skill_files)} skill files")
        
        loaded_count = 0
        failed_count = 0
        
        for skill_file in skill_files:
            try:
                content = self._loader.load_skill_content(skill_file)
                metadata = self._loader.parse_frontmatter(content)
                if metadata:
                    metadata.path = skill_file
                    self._metadata_index[metadata.name] = metadata
                    loaded_count += 1
                    logger.debug(f"[SkillRegistry] Loaded skill: {metadata.name} from {skill_file}")
                else:
                    logger.warning(f"[SkillRegistry] No metadata found in skill file: {skill_file}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"[SkillRegistry] Failed to load skill from {skill_file}: {e}", exc_info=True)
                failed_count += 1
        
        logger.info(f"[SkillRegistry] Scan completed: {loaded_count} skills loaded, {failed_count} failed")

    def get_metadata(self, names: List[str]) -> List[SkillMetadata]:
        result = []
        for name in names:
            if name in self._metadata_index:
                result.append(self._metadata_index[name])
        return result

    def load_skill(self, name: str) -> Optional[Skill]:
        logger.debug(f"[SkillRegistry] Loading skill: {name}")
        
        if name not in self._metadata_index:
            logger.warning(f"[SkillRegistry] Skill not found in metadata index: {name}")
            return None
        
        if name in self._skills_cache:
            logger.debug(f"[SkillRegistry] Returning cached skill: {name}")
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
            logger.info(f"[SkillRegistry] Skill loaded successfully: {name} with {len(supporting_files)} supporting files")
            return skill
        except SkillLoadError as e:
            logger.error(f"[SkillRegistry] Failed to load skill {name}: {e}", exc_info=True)
            return None
