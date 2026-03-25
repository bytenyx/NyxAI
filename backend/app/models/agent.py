from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel


class AgentIdentity(BaseModel):
    id: str
    name: str
    display_name: str
    type: Literal["investigation", "diagnosis", "recovery", "orchestrator"]
    icon: Optional[str] = None


class ToolCallRecord(BaseModel):
    tool: str
    params: dict
    result: Optional[Any] = None
    status: Literal["pending", "running", "success", "error"] = "pending"
    timestamp: str


class AgentExecutionBase(BaseModel):
    session_id: str
    agent: AgentIdentity
    status: Literal["idle", "running", "completed", "failed"] = "running"


class AgentExecutionCreate(AgentExecutionBase):
    pass


class AgentExecution(AgentExecutionBase):
    id: str
    thoughts: List[str] = []
    tool_calls: List[ToolCallRecord] = []
    result: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


class ServerMessage(BaseModel):
    type: str
    session_id: Optional[str] = None
    agent: Optional[AgentIdentity] = None
    payload: Any
    timestamp: str
    sequence: int
