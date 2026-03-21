from typing import Any, Dict, List, Optional

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

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=10000)


class AnomalyInfo(BaseModel):
    name: str
    severity: str
    description: Optional[str] = None


class ActionInfo(BaseModel):
    action_type: str
    description: str
    risk_level: str
    target: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str
    investigation: Optional[Dict[str, Any]] = None
    diagnosis: Optional[Dict[str, Any]] = None
    recovery: Optional[Dict[str, Any]] = None


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
        investigation = result.data.get("investigation", {})
        diagnosis = result.data.get("diagnosis", {})
        recovery = result.data.get("recovery", {})
        
        response_parts = []
        
        if investigation.get("summary"):
            response_parts.append(f"【调查摘要】\n{investigation['summary']}")
        
        anomalies = investigation.get("anomalies", [])
        if anomalies:
            anomaly_text = "\n".join([
                f"  - {a.get('name', '未知')}: {a.get('description', '')} (严重性: {a.get('severity', 'unknown')})"
                for a in anomalies
            ])
            response_parts.append(f"【发现异常】\n{anomaly_text}")
        
        if diagnosis.get("root_cause"):
            response_parts.append(f"【根因分析】\n{diagnosis['root_cause']}")
            if diagnosis.get("confidence"):
                response_parts.append(f"置信度: {diagnosis['confidence']:.0%}")
        
        actions = recovery.get("actions", [])
        if actions:
            action_text = "\n".join([
                f"  {i+1}. {a.get('description', '')} (风险: {a.get('risk_level', 'unknown')}, 目标: {a.get('target', 'unknown')})"
                for i, a in enumerate(actions)
            ])
            response_parts.append(f"【建议操作】\n{action_text}")
        
        if recovery.get("rollback_plan"):
            response_parts.append(f"【回滚方案】\n{recovery['rollback_plan']}")
        
        response_text = "\n\n".join(response_parts) if response_parts else "分析完成"
    else:
        response_text = f"处理失败: {result.error}"
        investigation = None
        diagnosis = None
        recovery = None
    
    return ChatResponse(
        session_id=session_id,
        response=response_text,
        status=result.data.get("status", "unknown") if result.success else "failed",
        investigation=investigation if result.success else None,
        diagnosis=diagnosis if result.success else None,
        recovery=recovery if result.success else None,
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
                for anomaly in anomalies:
                    yield f"data: {json.dumps({'type': 'anomaly', 'anomaly': anomaly}, ensure_ascii=False)}\n"
            
            if diagnosis.get("root_cause"):
                yield f"data: {json.dumps({'type': 'diagnosis', 'root_cause': diagnosis['root_cause'], 'confidence': diagnosis.get('confidence', 0)}, ensure_ascii=False)}\n"
            
            evidence_chain = diagnosis.get("evidence_chain", [])
            if evidence_chain:
                yield f"data: {json.dumps({'type': 'evidence_chain', 'nodes': evidence_chain}, ensure_ascii=False)}\n"
            
            actions = recovery.get("actions", [])
            if actions:
                for action in actions:
                    yield f"data: {json.dumps({'type': 'action', 'action': action}, ensure_ascii=False)}\n"
            
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'status': 'completed'}, ensure_ascii=False)}\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'error': result.error}, ensure_ascii=False)}\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.get("/{session_id}/evidence")
async def get_session_evidence(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    evidence_repo = EvidenceRepository(db_session)
    evidence_list = await evidence_repo.get_by_session(session_id)
    
    return {
        "session_id": session_id,
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "description": e.description,
                "source_data": e.source_data,
                "source_system": e.source_system,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "confidence": e.confidence,
            }
            for e in evidence_list
        ],
    }
