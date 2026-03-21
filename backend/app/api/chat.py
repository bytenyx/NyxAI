from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    
    if not request.session_id:
        from app.models.session import SessionStatus
        session = await repo.create(
            trigger_type="chat",
            trigger_source="user-input",
            status=SessionStatus.INVESTIGATING,
        )
        session_id = session.id
    else:
        session_id = request.session_id
        session = await repo.get(session_id)
        if not session:
            from app.models.session import SessionStatus
            session = await repo.create(
                trigger_type="chat",
                trigger_source="user-input",
                status=SessionStatus.INVESTIGATING,
            )
            session_id = session.id
    
    orchestrator = OrchestratorAgent()
    context = AgentContext(
        session_id=session_id,
        query=request.message,
    )
    
    result = await orchestrator.execute(context)
    
    if result.success:
        recovery = result.data.get("recovery", {})
        response_text = recovery.get("actions", [{}])[0].get("description", "处理完成") if recovery.get("actions") else "处理完成"
        if result.data.get("diagnosis", {}).get("root_cause"):
            response_text = f"根因分析: {result.data['diagnosis']['root_cause'][:200]}\n建议: {response_text}"
    else:
        response_text = f"处理失败: {result.error}"
    
    return ChatResponse(
        session_id=session_id,
        response=response_text,
        status=result.data.get("status", "unknown"),
    )
