from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ApiResponse, PaginatedResponse
from app.models.session import Session, SessionStatus
from app.models.agent import AgentExecution
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.agent_exec_repo import AgentExecutionRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    trigger_type: str
    trigger_source: str
    title: str | None = None


@router.post("", response_model=ApiResponse[Session])
async def create_session(
    request: CreateSessionRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"[API] POST /api/v1/sessions - Creating session trigger_type={request.trigger_type} trigger_source={request.trigger_source}")
    try:
        repo = SessionRepository(db_session)
        session = await repo.create(request.trigger_type, request.trigger_source, title=request.title)
        logger.info(f"[API] Session created successfully session_id={session.id}")
        return ApiResponse.success_response(data=session, message="会话创建成功")
    except Exception as e:
        logger.error(f"[API] Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("", response_model=PaginatedResponse[Session])
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: SessionStatus | None = Query(None, description="按状态筛选"),
    db_session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"[API] GET /api/v1/sessions - Listing sessions page={page} page_size={page_size} status={status}")
    from app.storage.models import SessionDB
    try:
        repo = SessionRepository(db_session)
        
        offset = (page - 1) * page_size
        
        if status:
            result = await db_session.execute(
                select(func.count())
                .select_from(SessionDB)
                .where(SessionDB.status == status.value)
            )
            total = result.scalar()
            
            result = await db_session.execute(
                select(SessionDB)
                .where(SessionDB.status == status.value)
                .order_by(SessionDB.created_at.desc())
                .limit(page_size)
                .offset(offset)
            )
            db_sessions = result.scalars().all()
        else:
            result = await db_session.execute(
                select(func.count()).select_from(SessionDB)
            )
            total = result.scalar()
            
            sessions = await repo.list(page_size, offset)
            logger.info(f"[API] Retrieved {len(sessions)} sessions (total={total})")
            return PaginatedResponse.create(
                items=sessions,
                total=total,
                page=page,
                page_size=page_size,
            )
        
        sessions = [
            Session(
                id=s.id,
                title=s.title,
                trigger_type=s.trigger_type,
                trigger_source=s.trigger_source,
                status=SessionStatus(s.status),
                message_count=s.message_count or 0,
                last_message=s.last_message,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in db_sessions
        ]
        
        logger.info(f"[API] Retrieved {len(sessions)} sessions (total={total})")
        return PaginatedResponse.create(
            items=sessions,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"[API] Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/{session_id}", response_model=ApiResponse[Session])
async def get_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    logger.info(f"[API] GET /api/v1/sessions/{session_id} - Getting session")
    try:
        repo = SessionRepository(db_session)
        session = await repo.get(session_id)
        if not session:
            logger.warning(f"[API] Session not found session_id={session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        logger.info(f"[API] Session retrieved successfully session_id={session_id}")
        return ApiResponse.success_response(data=session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Failed to get session session_id={session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.get("/{session_id}/executions", response_model=ApiResponse[list[AgentExecution]])
async def get_session_executions(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    try:
        agent_exec_repo = AgentExecutionRepository(db_session)
        executions = await agent_exec_repo.get_by_session(session_id)
        return ApiResponse.success_response(data=executions, message="获取执行记录成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行记录失败: {str(e)}")


@router.delete("/{session_id}", response_model=ApiResponse[None])
async def delete_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    try:
        repo = SessionRepository(db_session)
        success = await repo.delete(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return ApiResponse.success_response(data=None, message="会话删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")
