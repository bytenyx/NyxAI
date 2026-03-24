import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.storage.models import SessionDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, trigger_type: str, trigger_source: str, status: SessionStatus = SessionStatus.INVESTIGATING, title: Optional[str] = None
    ) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        logger.debug(f"[DB] Creating session session_id={session_id} trigger_type={trigger_type} trigger_source={trigger_source}")
        
        db_session = SessionDB(
            id=session_id,
            title=title or "新会话",
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status.value,
            message_count=0,
        )
        self.session.add(db_session)
        await self.session.flush()
        
        logger.info(f"[DB] Session created successfully session_id={session_id}")
        
        return Session(
            id=session_id,
            title=title or "新会话",
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            status=status,
            message_count=0,
            created_at=now,
            updated_at=now,
        )

    async def get(self, session_id: str) -> Optional[Session]:
        logger.debug(f"[DB] Getting session session_id={session_id}")
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            logger.warning(f"[DB] Session not found session_id={session_id}")
            return None
        
        logger.debug(f"[DB] Session retrieved successfully session_id={session_id}")
        
        return Session(
            id=db_session.id,
            title=db_session.title,
            trigger_type=db_session.trigger_type,
            trigger_source=db_session.trigger_source,
            status=SessionStatus(db_session.status),
            message_count=db_session.message_count or 0,
            last_message=db_session.last_message,
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

    async def update_status(self, session_id: str, status: SessionStatus) -> Optional[Session]:
        logger.debug(f"[DB] Updating session status session_id={session_id} status={status.value}")
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            logger.warning(f"[DB] Session not found for status update session_id={session_id}")
            return None
        
        db_session.status = status.value
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        logger.info(f"[DB] Session status updated session_id={session_id} status={status.value}")
        
        return await self.get(session_id)

    async def update_investigation(
        self, session_id: str, investigation_data: Dict[str, Any]
    ) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.investigation = investigation_data
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        return await self.get(session_id)

    async def update_root_cause(
        self, session_id: str, root_cause_data: Dict[str, Any]
    ) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.root_cause = root_cause_data
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        return await self.get(session_id)

    async def update_recovery_plan(
        self, session_id: str, recovery_plan_data: Dict[str, Any]
    ) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.recovery_plan = recovery_plan_data
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        return await self.get(session_id)

    async def update_execution_results(
        self, session_id: str, execution_results: List[Dict[str, Any]]
    ) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        db_session.execution_results = execution_results
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        return await self.get(session_id)

    async def update_session(
        self,
        session_id: str,
        status: Optional[SessionStatus] = None,
        investigation: Optional[Dict[str, Any]] = None,
        root_cause: Optional[Dict[str, Any]] = None,
        recovery_plan: Optional[Dict[str, Any]] = None,
    ) -> Optional[Session]:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None
        
        if status is not None:
            db_session.status = status.value
        if investigation is not None:
            db_session.investigation = investigation
        if root_cause is not None:
            db_session.root_cause = root_cause
        if recovery_plan is not None:
            db_session.recovery_plan = recovery_plan
        
        db_session.updated_at = datetime.now()
        await self.session.flush()
        
        return await self.get(session_id)

    async def delete(self, session_id: str) -> bool:
        result = await self.session.execute(
            select(SessionDB).where(SessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return False
        
        await self.session.delete(db_session)
        await self.session.flush()
        
        return True
