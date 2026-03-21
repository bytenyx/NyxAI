from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    KNOWLEDGE = "knowledge"


class Evidence(BaseModel):
    id: str = Field(..., description="Evidence unique identifier")
    evidence_type: EvidenceType
    description: str = Field(..., description="Evidence description")
    source_data: Dict[str, Any] = Field(..., description="Raw data")
    source_system: str = Field(..., description="Source system")
    timestamp: datetime
    confidence: float = Field(..., ge=0, le=1, description="Evidence confidence")


class EvidenceNode(BaseModel):
    id: str
    description: str
    evidence: Evidence
    supports: List[str] = Field(default_factory=list, description="Supporting evidence node IDs")
    contradicts: List[str] = Field(default_factory=list, description="Contradicting evidence node IDs")
    inference_step: str = Field(..., description="Inference step explanation")
