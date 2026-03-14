"""Skill registry for NyxAI.

This module provides a registry for managing and discovering skills
loaded from the file system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyxai.skills.loader import SkillDefinition, SkillLoader
from nyxai.types import AgentRole


class SkillRegistry:
    """Registry for managing skills.

    This class provides a centralized registry for registering,
    discovering, and managing skills loaded from the file system.

    Attributes:
        _skills: Dictionary mapping skill names to skill definitions.
        _skills_by_role: Dictionary mapping agent roles to skill names.
    """

    _instance: SkillRegistry | None = None

    def __new__(cls) -> SkillRegistry:
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry."""
        if self._initialized:
            return

        self._skills: dict[str, SkillDefinition] = {}
        self._skills_by_role: dict[str, set[str]] = {
            role.value: set() for role in AgentRole
        }
        self._initialized = True

    def register(self, skill_def: SkillDefinition) -> None:
        """Register a skill definition.

        Args:
            skill_def: Skill definition to register.

        Raises:
            ValueError: If skill with same name already exists.
        """
        skill_name = skill_def.name

        if skill_name in self._skills:
            raise ValueError(f"Skill '{skill_name}' is already registered")

        self._skills[skill_name] = skill_def

        # Register by role
        role = skill_def.agent_role
        if role in self._skills_by_role:
            self._skills_by_role[role].add(skill_name)

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill.

        Args:
            skill_name: Name of skill to unregister.

        Returns:
            True if skill was unregistered, False if not found.
        """
        if skill_name not in self._skills:
            return False

        skill_def = self._skills[skill_name]
        del self._skills[skill_name]

        # Remove from role mapping
        role = skill_def.agent_role
        if role in self._skills_by_role:
            self._skills_by_role[role].discard(skill_name)

        return True

    def get(self, skill_name: str) -> SkillDefinition | None:
        """Get a skill by name.

        Args:
            skill_name: Name of the skill.

        Returns:
            Skill definition or None if not found.
        """
        return self._skills.get(skill_name)

    def get_by_role(self, role: AgentRole | str) -> list[SkillDefinition]:
        """Get all skills for a specific agent role.

        Args:
            role: Agent role to filter by.

        Returns:
            List of skills for the role.
        """
        role_value = role.value if isinstance(role, AgentRole) else role
        skill_names = self._skills_by_role.get(role_value, set())
        return [self._skills[name] for name in skill_names if name in self._skills]

    def list_all(self) -> list[str]:
        """List all registered skill names.

        Returns:
            List of skill names.
        """
        return list(self._skills.keys())

    def list_by_role(self, role: AgentRole | str) -> list[str]:
        """List skill names for a specific role.

        Args:
            role: Agent role to filter by.

        Returns:
            List of skill names.
        """
        role_value = role.value if isinstance(role, AgentRole) else role
        return list(self._skills_by_role.get(role_value, set()))

    def is_registered(self, skill_name: str) -> bool:
        """Check if a skill is registered.

        Args:
            skill_name: Name of the skill.

        Returns:
            True if skill is registered.
        """
        return skill_name in self._skills

    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()
        for role in self._skills_by_role:
            self._skills_by_role[role].clear()

    def get_skill_info(self, skill_name: str) -> dict[str, Any] | None:
        """Get information about a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            Dictionary with skill info or None if not found.
        """
        skill_def = self._skills.get(skill_name)
        if skill_def is None:
            return None

        return skill_def.to_dict()

    def get_all_skills_info(self) -> list[dict[str, Any]]:
        """Get information about all registered skills.

        Returns:
            List of dictionaries with skill info.
        """
        return [skill.to_dict() for skill in self._skills.values()]

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry statistics.
        """
        return {
            "total_skills": len(self._skills),
            "skills_by_role": {
                role: len(names)
                for role, names in self._skills_by_role.items()
            },
        }

    def load_from_directory(self, skills_dir: str | Path | None = None) -> int:
        """Load and register all skills from directory.

        Args:
            skills_dir: Directory to load skills from. Defaults to .trae/skills.

        Returns:
            Number of skills loaded.
        """
        skills = SkillLoader.discover_skills(skills_dir)
        loaded_count = 0

        for skill_def in skills:
            try:
                # Validate skill
                errors = SkillLoader.validate_skill(skill_def)
                if errors:
                    continue

                self.register(skill_def)
                loaded_count += 1
            except ValueError:
                # Skip duplicate skills
                continue

        return loaded_count

    def reload_skill(self, skill_name: str) -> bool:
        """Reload a skill from file.

        Args:
            skill_name: Name of skill to reload.

        Returns:
            True if reloaded successfully.
        """
        skill_def = SkillLoader.load_skill(skill_name)
        if skill_def is None:
            return False

        # Unregister if exists
        if skill_name in self._skills:
            self.unregister(skill_name)

        # Register new version
        try:
            self.register(skill_def)
            return True
        except ValueError:
            return False
