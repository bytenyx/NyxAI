from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.storage.database import get_async_session
from app.storage.repositories.session_repo import SessionRepository

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    trigger_type: str
    trigger_source: str


@router.post("", response_model=Session)
async def create_session(
    request: CreateSessionRequest,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    return await repo.create(request.trigger_type, request.trigger_source)


@router.get("", response_model=List[Session])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    return await repo.list(limit, offset)


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_async_session),
):
    repo = SessionRepository(db_session)
    session = await repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
