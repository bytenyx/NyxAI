"""Skills system for NyxAI agents.

This module provides a flexible skill system that allows agents to dynamically
load, manage, and execute various skills. Skills are pluggable functional modules
that can extend agent capabilities.
"""

from __future__ import annotations

from nyxai.skills.base import (
    Skill,
    SkillConfig,
    SkillContext,
    SkillResult,
    SkillStatus,
)
from nyxai.skills.registry import SkillRegistry
from nyxai.skills.loader import SkillLoader

__all__ = [
    "Skill",
    "SkillConfig",
    "SkillContext",
    "SkillResult",
    "SkillStatus",
    "SkillRegistry",
    "SkillLoader",
]
