"""Skills system for NyxAI agents.

This module provides a flexible skill system that allows agents to dynamically
load, manage, and execute various skills from the file system (.trae/skills/).
"""

from __future__ import annotations

from nyxai.skills.loader import SkillDefinition, SkillLoader
from nyxai.skills.registry import SkillRegistry

__all__ = [
    "SkillDefinition",
    "SkillLoader",
    "SkillRegistry",
]
