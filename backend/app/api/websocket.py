import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.base import AgentContext
from app.agents.orchestrator import OrchestratorAgent
from app.storage.repositories.session_repo import SessionRepository
from app.storage.repositories.evidence_repo import EvidenceRepository

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._sequence: int = 0

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    def _get_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    async def send_event(
        self,
        session_id: str,
        event_type: str,
        payload: Any,
        agent: Optional[dict] = None,
    ):
        if session_id in self.active_connections:
            message = {
                "type": event_type,
                "agent": agent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": self._get_sequence(),
            }
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/api/v1/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    from app.storage.database import async_session_factory
    
    await manager.connect(session_id, websocket)
    try:
        async with async_session_factory() as db_session:
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "chat":
                    content = data.get("content", "")
                    await handle_chat_message(session_id, content, db_session)

                elif data.get("type") == "stop":
                    pass

                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)


async def handle_chat_message(session_id: str, content: str, db_session):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    
    orchestrator = OrchestratorAgent(
        session_repo=session_repo,
        evidence_repo=evidence_repo,
    )

    async for event in orchestrator.run_stream(session_id, content):
        await manager.send_event(
            session_id,
            event["type"],
            event.get("payload", {}),
            event.get("agent"),
        )
