import asyncio
import json
import time
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
        self._last_ping: Dict[str, float] = {}
        self._connection_start: Dict[str, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._timeout_check_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30
        self._connection_timeout = 300

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self._last_ping[session_id] = time.time()
        self._connection_start[session_id] = time.time()

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            try:
                asyncio.create_task(self.active_connections[session_id].close())
            except Exception:
                pass
            del self.active_connections[session_id]
        if session_id in self._last_ping:
            del self._last_ping[session_id]
        if session_id in self._connection_start:
            del self._connection_start[session_id]

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
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                await self.disconnect(session_id)

    async def send_heartbeat(self):
        """发送心跳消息到所有活跃连接"""
        while True:
            try:
                current_time = time.time()
                to_remove = []
                
                for session_id, ws in self.active_connections.items():
                    try:
                        await ws.send_json({
                            "type": "ping",
                            "timestamp": current_time,
                        })
                    except Exception as e:
                        to_remove.append(session_id)
                
                for session_id in to_remove:
                    await self.disconnect(session_id)
                
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(self._heartbeat_interval)

    async def check_timeouts(self):
        """检查超时连接"""
        while True:
            try:
                current_time = time.time()
                to_remove = []
                
                for session_id, last_ping in self._last_ping.items():
                    if current_time - last_ping > self._connection_timeout:
                        to_remove.append(session_id)
                
                for session_id in to_remove:
                    await self.disconnect(session_id)
                
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(60)

    async def start_background_tasks(self):
        """启动后台任务"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self.send_heartbeat())
        
        if self._timeout_check_task is None or self._timeout_check_task.done():
            self._timeout_check_task = asyncio.create_task(self.check_timeouts())

    async def stop_background_tasks(self):
        """停止后台任务"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._timeout_check_task and not self._timeout_check_task.done():
            self._timeout_check_task.cancel()
            try:
                await self._timeout_check_task
            except asyncio.CancelledError:
                pass

    async def update_ping(self, session_id: str):
        """更新最后ping时间"""
        if session_id in self._last_ping:
            self._last_ping[session_id] = time.time()

    def get_connection_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        if session_id not in self.active_connections:
            return None
        
        return {
            "session_id": session_id,
            "connected_duration": time.time() - self._connection_start.get(session_id, 0),
            "last_ping": time.time() - self._last_ping.get(session_id, 0),
        }


manager = ConnectionManager()


@router.websocket("/api/v1/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    from app.storage.database import async_session_factory
    from app.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    await manager.connect(session_id, websocket)
    await manager.start_background_tasks()
    
    connection_info = manager.get_connection_info(session_id)
    logger.info(f"WebSocket connected: {connection_info}")
    
    try:
        async with async_session_factory() as db_session:
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "chat":
                    content = data.get("content", "")
                    await handle_chat_message(session_id, content, db_session)

                elif data.get("type") == "stop":
                    await manager.send_event(
                        session_id,
                        "stopped",
                        {"message": "Processing stopped by user"}
                    )

                elif data.get("type") == "ping":
                    await manager.update_ping(session_id)
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})

                elif data.get("type") == "pong":
                    await manager.update_ping(session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
    finally:
        await manager.disconnect(session_id)
        logger.info(f"WebSocket cleanup completed: {session_id}")


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
