import re
from pathlib import Path
from typing import Optional, List, Dict
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

    def load_skill_content(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise SkillLoadError(f"Failed to read skill file {path}: {e}")

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
