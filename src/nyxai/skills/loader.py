"""Skill loader for NyxAI.

This module provides functionality for dynamically loading skills
from the file system (.trae/skills/<skill-name>/SKILL.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SkillDefinition:
    """Definition of a skill loaded from SKILL.md file.

    Attributes:
        name: Skill name (unique identifier).
        description: Skill description.
        agent_role: Target agent role for this skill.
        version: Skill version.
        content: Full markdown content of the skill.
        metadata: Additional metadata from frontmatter.
        path: Path to the SKILL.md file.
    """

    name: str
    description: str
    agent_role: str
    version: str
    content: str
    metadata: dict[str, Any]
    path: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with skill definition.
        """
        return {
            "name": self.name,
            "description": self.description,
            "agent_role": self.agent_role,
            "version": self.version,
            "metadata": self.metadata,
            "path": self.path,
        }


class SkillLoader:
    """Loader for dynamically loading skills from file system.

    This class provides methods for discovering and loading skills
    from the .trae/skills/ directory structure.
    """

    DEFAULT_SKILLS_DIR = ".trae/skills"

    @staticmethod
    def parse_skill_file(file_path: str | Path) -> SkillDefinition | None:
        """Parse a SKILL.md file.

        Args:
            file_path: Path to the SKILL.md file.

        Returns:
            SkillDefinition if valid, None otherwise.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse frontmatter and content
            frontmatter, markdown_content = SkillLoader._parse_frontmatter(content)

            # Extract required fields
            name = frontmatter.get("name")
            description = frontmatter.get("description", "")
            agent_role = frontmatter.get("agent_role", "")
            version = frontmatter.get("version", "1.0.0")

            if not name:
                return None

            return SkillDefinition(
                name=name,
                description=description,
                agent_role=agent_role,
                version=version,
                content=markdown_content,
                metadata=frontmatter,
                path=str(file_path),
            )

        except Exception:
            return None

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content with frontmatter.

        Returns:
            Tuple of (frontmatter dict, markdown content).
        """
        frontmatter = {}
        markdown = content

        if content.startswith("---"):
            # Find the end of frontmatter
            end_match = content.find("---", 3)
            if end_match != -1:
                yaml_content = content[3:end_match].strip()
                markdown = content[end_match + 3:].strip()

                try:
                    frontmatter = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError:
                    frontmatter = {}

        return frontmatter, markdown

    @staticmethod
    def discover_skills(skills_dir: str | Path | None = None) -> list[SkillDefinition]:
        """Discover all skills in the skills directory.

        Args:
            skills_dir: Directory to search for skills. Defaults to .trae/skills.

        Returns:
            List of skill definitions.
        """
        if skills_dir is None:
            # Try to find .trae/skills directory
            skills_dir = SkillLoader._find_skills_dir()

        skills_dir = Path(skills_dir)

        if not skills_dir.exists():
            return []

        skills = []

        # Iterate through subdirectories
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill_def = SkillLoader.parse_skill_file(skill_file)
                    if skill_def:
                        skills.append(skill_def)

        return skills

    @staticmethod
    def load_skill(skill_name: str, skills_dir: str | Path | None = None) -> SkillDefinition | None:
        """Load a specific skill by name.

        Args:
            skill_name: Name of the skill to load.
            skills_dir: Directory to search for skills. Defaults to .trae/skills.

        Returns:
            SkillDefinition if found, None otherwise.
        """
        if skills_dir is None:
            skills_dir = SkillLoader._find_skills_dir()

        skills_dir = Path(skills_dir)
        skill_file = skills_dir / skill_name / "SKILL.md"

        if skill_file.exists():
            return SkillLoader.parse_skill_file(skill_file)

        return None

    @staticmethod
    def _find_skills_dir() -> Path:
        """Find the skills directory.

        Searches for .trae/skills directory starting from current directory
        and going up the directory tree.

        Returns:
            Path to skills directory.
        """
        current = Path.cwd()

        while current != current.parent:
            skills_dir = current / ".trae" / "skills"
            if skills_dir.exists():
                return skills_dir
            current = current.parent

        # Default to current directory/.trae/skills
        return Path.cwd() / ".trae" / "skills"

    @staticmethod
    def get_skill_names(skills_dir: str | Path | None = None) -> list[str]:
        """Get list of available skill names.

        Args:
            skills_dir: Directory to search for skills.

        Returns:
            List of skill names.
        """
        skills = SkillLoader.discover_skills(skills_dir)
        return [s.name for s in skills]

    @staticmethod
    def validate_skill(skill_def: SkillDefinition) -> list[str]:
        """Validate a skill definition.

        Args:
            skill_def: Skill definition to validate.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors = []

        if not skill_def.name:
            errors.append("Skill name is required")

        if not skill_def.description:
            errors.append("Skill description is required")

        if not skill_def.agent_role:
            errors.append("Agent role is required")
        else:
            valid_roles = ["monitor", "analyze", "decide", "execute"]
            if skill_def.agent_role not in valid_roles:
                errors.append(f"Invalid agent role: {skill_def.agent_role}")

        return errors
