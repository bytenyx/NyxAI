from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ApiResponse, PaginatedResponse
from app.models.session import Session, SessionStatus
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository

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
    try:
        repo = SessionRepository(db_session)
        session = await repo.create(request.trigger_type, request.trigger_source, title=request.title)
        return ApiResponse.success_response(data=session, message="会话创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("", response_model=PaginatedResponse[Session])
async def list_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: SessionStatus | None = Query(None, description="按状态筛选"),
    db_session: AsyncSession = Depends(get_async_session),
):
    try:
        repo = SessionRepository(db_session)
        
        offset = (page - 1) * page_size
        
        if status:
            from app.storage.models import SessionDB
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
                select(func.count()).select_from(SessionDB.__table__)
            )
            total = result.scalar()
            
            sessions = await repo.list(page_size, offset)
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
        
        return PaginatedResponse.create(
            items=sessions,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/{session_id}", response_model=ApiResponse[Session])
async def get_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    try:
        repo = SessionRepository(db_session)
        session = await repo.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return ApiResponse.success_response(data=session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")
