from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class SkillLoadError(Exception):
    pass


@dataclass
class SkillMetadata:
    name: str
    description: str
    path: Path


@dataclass
class Skill:
    metadata: SkillMetadata
    content: str
    supporting_files: Dict[str, str] = field(default_factory=dict)
