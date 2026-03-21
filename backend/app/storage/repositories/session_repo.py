import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.storage.models import SessionDB


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, trigger_type: str, trigger_source: str, status: SessionStatus = SessionStatus.INVESTIGATING
    ) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        db_session = SessionDB(
            id=session_id,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status.value,
        )
        self.session.add(db_session)
        await self.session.flush()
        
        return Session(
            id=session_id,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status,
            created_at=now,
            updated_at=now,
        )

    async def get(self, session_id: str) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        return Session(
            id=db_session.id,
            trigger_type=db_session.trigger_type,
            trigger_source=db_session.trigger_source,
            status=SessionStatus(db_session.status),
            investigation=db_session.investigation,
            root_cause=db_session.root_cause,
            recovery_plan=db_session.recovery_plan,
            execution_results=db_session.execution_results or [],
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    async def list(self, limit: int = 50, offset: int = 0) -> List[Session]:
        result = await self.session.execute(
            select(SessionDB).order_by(SessionDB.created_at.desc()).limit(limit).offset(offset)
        )
        db_sessions = result.scalars().all()
        
        return [
            Session(
                id=s.id,
                trigger_type=s.trigger_type,
                trigger_source=s.trigger_source,
                status=SessionStatus(s.status),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in db_sessions
        ]

    async def update_status(self, session_id: str, status: SessionStatus) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.status = status.value
        await self.session.flush()
        
        return await self.get(session_id)
