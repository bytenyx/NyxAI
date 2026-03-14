"""Skill registry for NyxAI.

This module provides a registry for managing and discovering skills.
"""

from __future__ import annotations

from typing import Any

from nyxai.skills.base import Skill
from nyxai.types import AgentRole


class SkillRegistry:
    """Registry for managing skills.

    This class provides a centralized registry for registering,
    discovering, and managing skills. Skills are organized by
    their target agent role.

    Attributes:
        _skills: Dictionary mapping skill names to skill instances.
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

        self._skills: dict[str, Skill] = {}
        self._skills_by_role: dict[AgentRole, set[str]] = {
            role: set() for role in AgentRole
        }
        self._initialized = True

    def register(self, skill: Skill) -> None:
        """Register a skill.

        Args:
            skill: Skill instance to register.

        Raises:
            ValueError: If skill with same name already exists.
        """
        skill_name = skill.name

        if skill_name in self._skills:
            raise ValueError(f"Skill '{skill_name}' is already registered")

        self._skills[skill_name] = skill
        self._skills_by_role[skill.agent_role].add(skill_name)

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill.

        Args:
            skill_name: Name of skill to unregister.

        Returns:
            True if skill was unregistered, False if not found.
        """
        if skill_name not in self._skills:
            return False

        skill = self._skills[skill_name]
        del self._skills[skill_name]
        self._skills_by_role[skill.agent_role].discard(skill_name)

        return True

    def get(self, skill_name: str) -> Skill | None:
        """Get a skill by name.

        Args:
            skill_name: Name of the skill.

        Returns:
            Skill instance or None if not found.
        """
        return self._skills.get(skill_name)

    def get_by_role(self, role: AgentRole) -> list[Skill]:
        """Get all skills for a specific agent role.

        Args:
            role: Agent role to filter by.

        Returns:
            List of skills for the role.
        """
        skill_names = self._skills_by_role.get(role, set())
        return [self._skills[name] for name in skill_names if name in self._skills]

    def list_all(self) -> list[str]:
        """List all registered skill names.

        Returns:
            List of skill names.
        """
        return list(self._skills.keys())

    def list_by_role(self, role: AgentRole) -> list[str]:
        """List skill names for a specific role.

        Args:
            role: Agent role to filter by.

        Returns:
            List of skill names.
        """
        return list(self._skills_by_role.get(role, set()))

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
        skill = self._skills.get(skill_name)
        if skill is None:
            return None

        return skill.to_dict()

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
                role.value: len(names)
                for role, names in self._skills_by_role.items()
            },
        }
