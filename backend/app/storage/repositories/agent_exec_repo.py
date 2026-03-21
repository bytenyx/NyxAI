import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentExecution, AgentExecutionCreate
from app.storage.models import AgentExecutionDB


class AgentExecutionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_session(self, session_id: str) -> List[AgentExecution]:
        result = await self.session.execute(
            select(AgentExecutionDB)
            .where(AgentExecutionDB.session_id == session_id)
            .order_by(AgentExecutionDB.started_at)
        )
        db_execs = result.scalars().all()
        return [self._to_model(e) for e in db_execs]

    async def get_by_id(self, exec_id: str) -> Optional[AgentExecution]:
        result = await self.session.execute(
            select(AgentExecutionDB).where(AgentExecutionDB.id == exec_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        return self._to_model(db_obj)

    async def create(self, data: AgentExecutionCreate) -> AgentExecution:
        exec_id = str(uuid.uuid4())
        
        db_obj = AgentExecutionDB(
            id=exec_id,
            session_id=data.session_id,
            agent_name=data.agent.name,
            agent_display_name=data.agent.display_name,
            agent_type=data.agent.type,
            status=data.status,
        )
        self.session.add(db_obj)
        await self.session.flush()
        
        return self._to_model(db_obj)

    async def add_thought(self, exec_id: str, thought: str) -> Optional[AgentExecution]:
        result = await self.session.execute(
            select(AgentExecutionDB).where(AgentExecutionDB.id == exec_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        
        thoughts = db_obj.thoughts or []
        thoughts.append(thought)
        db_obj.thoughts = thoughts
        
        await self.session.flush()
        return self._to_model(db_obj)

    async def add_tool_call(
        self, exec_id: str, tool_call: dict
    ) -> Optional[AgentExecution]:
        result = await self.session.execute(
            select(AgentExecutionDB).where(AgentExecutionDB.id == exec_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        
        tool_calls = db_obj.tool_calls or []
        tool_calls.append(tool_call)
        db_obj.tool_calls = tool_calls
        
        await self.session.flush()
        return self._to_model(db_obj)

    async def complete(
        self, exec_id: str, result: str, status: str = "completed"
    ) -> Optional[AgentExecution]:
        db_result = await self.session.execute(
            select(AgentExecutionDB).where(AgentExecutionDB.id == exec_id)
        )
        db_obj = db_result.scalar_one_or_none()
        if not db_obj:
            return None
        
        db_obj.result = result
        db_obj.status = status
        db_obj.completed_at = datetime.now()
        db_obj.duration_ms = int(
            (db_obj.completed_at - db_obj.started_at).total_seconds() * 1000
        )
        
        await self.session.flush()
        return self._to_model(db_obj)

    def _to_model(self, db_obj: AgentExecutionDB) -> AgentExecution:
        from app.models.agent import AgentIdentity
        
        return AgentExecution(
            id=db_obj.id,
            session_id=db_obj.session_id,
            agent=AgentIdentity(
                id=db_obj.id,
                name=db_obj.agent_name,
                display_name=db_obj.agent_display_name,
                type=db_obj.agent_type,
            ),
            status=db_obj.status,
            thoughts=db_obj.thoughts or [],
            tool_calls=db_obj.tool_calls or [],
            result=db_obj.result,
            started_at=db_obj.started_at,
            completed_at=db_obj.completed_at,
            duration_ms=db_obj.duration_ms,
        )
