"""Skill loader for NyxAI.

This module provides functionality for dynamically loading skills
from module paths.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any, TypeVar

from nyxai.skills.base import Skill

T = TypeVar("T", bound=Skill)


class SkillLoader:
    """Loader for dynamically loading skills.

    This class provides methods for loading skills from module paths,
    validating skill classes, and instantiating skill objects.
    """

    @staticmethod
    def load_from_module(module_path: str, class_name: str | None = None) -> type[Skill]:
        """Load a skill class from a module.

        Args:
            module_path: Python module path (e.g., 'my_module.skills').
            class_name: Specific class name to load. If None, loads the
                       first Skill subclass found.

        Returns:
            Skill class.

        Raises:
            ImportError: If module cannot be imported.
            ValueError: If skill class cannot be found.
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(f"Failed to import module '{module_path}': {e}") from e

        if class_name:
            # Load specific class
            if not hasattr(module, class_name):
                raise ValueError(
                    f"Class '{class_name}' not found in module '{module_path}'"
                )

            skill_class = getattr(module, class_name)
            if not inspect.isclass(skill_class) or not issubclass(skill_class, Skill):
                raise ValueError(
                    f"Class '{class_name}' is not a valid Skill subclass"
                )

            return skill_class

        # Find first Skill subclass
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Skill)
                and obj is not Skill
            ):
                return obj

        raise ValueError(f"No Skill subclass found in module '{module_path}'")

    @staticmethod
    def load_and_create(
        module_path: str,
        class_name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> Skill:
        """Load and instantiate a skill.

        Args:
            module_path: Python module path.
            class_name: Specific class name to load.
            config: Configuration dictionary for the skill.

        Returns:
            Instantiated skill.
        """
        skill_class = SkillLoader.load_from_module(module_path, class_name)

        from nyxai.skills.base import SkillConfig

        skill_config = SkillConfig(**(config or {}))
        return skill_class(config=skill_config)

    @staticmethod
    def discover_skills(module_path: str) -> list[type[Skill]]:
        """Discover all skill classes in a module.

        Args:
            module_path: Python module path.

        Returns:
            List of skill classes.
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            return []

        skills = []
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Skill)
                and obj is not Skill
            ):
                skills.append(obj)

        return skills

    @staticmethod
    def validate_skill(skill_class: type[Skill]) -> list[str]:
        """Validate a skill class.

        Args:
            skill_class: Skill class to validate.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors = []

        if not inspect.isclass(skill_class):
            errors.append("Not a class")
            return errors

        if not issubclass(skill_class, Skill):
            errors.append("Not a Skill subclass")
            return errors

        # Check required properties
        required_properties = ["name", "description", "agent_role"]
        for prop in required_properties:
            if not hasattr(skill_class, prop):
                errors.append(f"Missing required property: {prop}")

        # Check execute method
        if not hasattr(skill_class, "execute"):
            errors.append("Missing execute method")
        elif not inspect.iscoroutinefunction(getattr(skill_class, "execute")):
            errors.append("execute method must be async")

        return errors

    @staticmethod
    def load_builtin_skills() -> list[Skill]:
        """Load all built-in skills.

        Returns:
            List of instantiated built-in skills.
        """
        skills = []

        # Define built-in skill modules
        builtin_modules = [
            "nyxai.skills.builtin.monitoring.metric_collection",
            "nyxai.skills.builtin.monitoring.anomaly_detection",
            "nyxai.skills.builtin.analysis.topology_analysis",
            "nyxai.skills.builtin.analysis.llm_analysis",
            "nyxai.skills.builtin.decision.strategy_matching",
            "nyxai.skills.builtin.execution.action_execution",
        ]

        for module_path in builtin_modules:
            try:
                skill_classes = SkillLoader.discover_skills(module_path)
                for skill_class in skill_classes:
                    skills.append(skill_class())
            except (ImportError, ValueError):
                # Skip modules that don't exist or have no skills
                continue

        return skills
