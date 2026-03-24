from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.evidence import Evidence, EvidenceNode


class SessionStatus(str, Enum):
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Anomaly(BaseModel):
    id: str
    component: str = Field(..., description="Anomalous component")
    anomaly_type: str = Field(..., description="Anomaly type")
    severity: str = Field(..., description="Severity level")
    evidence_ids: List[str] = Field(..., description="Related evidence IDs")
    detected_at: datetime


class InvestigationResult(BaseModel):
    session_id: str
    anomalies: List[Anomaly]
    evidence: List[Evidence]
    summary: str = Field(..., description="Investigation summary")
    created_at: datetime


class RootCauseAnalysis(BaseModel):
    session_id: str
    root_cause: str = Field(..., description="Root cause description")
    confidence: float = Field(..., ge=0, le=1)
    evidence_chain: List[EvidenceNode] = Field(..., description="Evidence chain")
    affected_components: List[str]
    reasoning_report: str = Field(..., description="Reasoning report")
    similar_cases: List[str] = Field(default_factory=list, description="Similar case IDs")
    created_at: datetime


class RecoveryAction(BaseModel):
    id: str
    action_type: str
    target: str
    params: Dict[str, Any]
    description: str
    risk_level: RiskLevel
    evidence_based: bool = Field(..., description="Whether based on evidence")
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class RecoveryPlan(BaseModel):
    session_id: str
    actions: List[RecoveryAction]
    overall_risk_level: RiskLevel
    requires_confirmation: bool
    rollback_plan: Optional[str]
    estimated_impact: str


class Session(BaseModel):
    id: str
    title: Optional[str] = None
    trigger_type: str = Field(..., description="Trigger type: webhook/scheduled/chat")
    trigger_source: str = Field(..., description="Trigger source")
    status: SessionStatus
    message_count: int = 0
    last_message: Optional[str] = None
    investigation: Optional[Dict[str, Any]] = None
    root_cause: Optional[Dict[str, Any]] = None
    recovery_plan: Optional[Dict[str, Any]] = None
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
