from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent
from app.models.session import SessionStatus
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.evidence_repo import EvidenceRepository
import json
import asyncio

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str


class StreamStatus(BaseModel):
    stage: str
    message: str
    progress: int = 0100


class StreamEvent(BaseModel):
    type: str
    content: str
    data: Optional[dict] = None


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    
    if not request.session_id:
        session = await session_repo.create(
            trigger_type="chat",
            trigger_source="user-input",
            status=SessionStatus.INVESTIGATING,
        )
        session_id = session.id
    else:
        session_id = request.session_id
        session = await session_repo.get(session_id)
        if not session:
            session = await session_repo.create(
                trigger_type="chat",
                trigger_source="user-input",
                status=SessionStatus.INVESTIGATING,
            )
            session_id = session.id
    
    orchestrator = OrchestratorAgent(
        session_repo=session_repo,
        evidence_repo=evidence_repo,
    )
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


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    
    if not request.session_id:
        session = await session_repo.create(
            trigger_type="chat",
            trigger_source="user-input",
            status=SessionStatus.INVESTIGATING,
        )
        session_id = session.id
    else:
        session_id = request.session_id
        session = await session_repo.get(session_id)
        if not session:
            session = await session_repo.create(
                trigger_type="chat",
                trigger_source="user-input",
                status=SessionStatus.INVESTIGATING,
            )
            session_id = session.id
    
    async def generate():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n"
        
        yield f"data: {json.dumps({'type': 'status', 'stage': 'investigating', 'message': '正在调查问题...', 'progress': 10}, ensure_ascii=False)}\n"
        
        orchestrator = OrchestratorAgent(
            session_repo=session_repo,
            evidence_repo=evidence_repo,
        )
        context = AgentContext(
            session_id=session_id,
            query=request.message,
        )
        
        yield f"data: {json.dumps({'type': 'status', 'stage': 'diagnosing', 'message': '正在分析根因...', 'progress': 40}, ensure_ascii=False)}\n"
        
        result = await orchestrator.execute(context)
        
        yield f"data: {json.dumps({'type': 'status', 'stage': 'recovering', 'message': '正在制定恢复方案...', 'progress': 70}, ensure_ascii=False)}\n"
        
        if result.success:
            investigation = result.data.get("investigation", {})
            diagnosis = result.data.get("diagnosis", {})
            recovery = result.data.get("recovery", {})
            
            if investigation.get("summary"):
                yield f"data: {json.dumps({'type': 'investigation', 'summary': investigation['summary']}, ensure_ascii=False)}\n"
            
            anomalies = investigation.get("anomalies", [])
            if anomalies:
                for i, anomaly in enumerate(anomalies):
                    yield f"data: {json.dumps({'type': 'anomaly', 'anomaly': anomaly}, ensure_ascii=False)}\n"
            
            if diagnosis.get("root_cause"):
                yield f"data: {json.dumps({'type': 'diagnosis', 'root_cause': diagnosis['root_cause'], 'confidence': diagnosis.get('confidence', 0)}, ensure_ascii=False)}\n"
            
            evidence_chain = diagnosis.get("evidence_chain", [])
            if evidence_chain:
                yield f"data: {json.dumps({'type': 'evidence_chain', 'nodes': evidence_chain}, ensure_ascii=False)}\n"
            
            actions = recovery.get("actions", [])
            if actions:
                for i, action in enumerate(actions):
                    yield f"data: {json.dumps({'type': 'action', 'action': action}, ensure_ascii=False)}\n"
            
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'status': 'completed'}, ensure_ascii=False)}\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'error': result.error}, ensure_ascii=False)}\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )