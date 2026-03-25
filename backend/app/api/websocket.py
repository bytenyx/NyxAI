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
from app.storage.repositories.agent_exec_repo import AgentExecutionRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

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
        self._connection_timeout = 120

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self._last_ping[session_id] = time.time()
        self._connection_start[session_id] = time.time()
        logger.info(f"[WebSocket] Connection established session_id={session_id} total_connections={len(self.active_connections)}")

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].close()
            except Exception as e:
                logger.warning(f"[WebSocket] Error closing connection for session_id={session_id}: {e}")
            del self.active_connections[session_id]
        if session_id in self._last_ping:
            del self._last_ping[session_id]
        if session_id in self._connection_start:
            del self._connection_start[session_id]
        logger.info(f"[WebSocket] Connection closed session_id={session_id} remaining_connections={len(self.active_connections)}")

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
                "session_id": session_id,
                "agent": agent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence": self._get_sequence(),
            }
            try:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"[WebSocket] Event sent session_id={session_id} type={event_type} sequence={message['sequence']}")
            except Exception as e:
                logger.error(f"[WebSocket] Failed to send event session_id={session_id} type={event_type}: {e}", exc_info=True)
                await self.disconnect(session_id)
        else:
            logger.warning(f"[WebSocket] Cannot send event - no active connection session_id={session_id}")

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
                        logger.warning(f"[WebSocket] Heartbeat failed for session_id={session_id}: {e}")
                        to_remove.append(session_id)
                
                for session_id in to_remove:
                    await self.disconnect(session_id)
                
                logger.debug(f"[WebSocket] Heartbeat sent to {len(self.active_connections)} connections")
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                logger.info("[WebSocket] Heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"[WebSocket] Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(self._heartbeat_interval)

    async def check_timeouts(self):
        """检查超时连接"""
        while True:
            try:
                current_time = time.time()
                to_remove = []
                
                for session_id, last_ping in self._last_ping.items():
                    time_since_ping = current_time - last_ping
                    if time_since_ping > self._connection_timeout:
                        logger.warning(f"[WebSocket] Connection timeout session_id={session_id} time_since_ping={time_since_ping:.1f}s timeout={self._connection_timeout}s")
                        to_remove.append(session_id)
                
                for session_id in to_remove:
                    await self.disconnect(session_id)
                
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("[WebSocket] Timeout check task cancelled")
                break
            except Exception as e:
                logger.error(f"[WebSocket] Timeout check error: {e}", exc_info=True)
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
    from app.utils.logger import get_logger, add_request_context, clear_request_context
    
    logger = get_logger(__name__)
    connection_start = time.time()
    
    add_request_context(session_id=session_id)
    
    await manager.connect(session_id, websocket)
    await manager.start_background_tasks()
    
    connection_info = manager.get_connection_info(session_id)
    logger.info(f"[WebSocket] Chat endpoint connected session_id={session_id} info={connection_info}")
    
    try:
        async with async_session_factory() as db_session:
            message_count = 0
            while True:
                data = await websocket.receive_json()
                message_count += 1
                message_type = data.get("type", "unknown")
                
                logger.debug(f"[WebSocket] Message received session_id={session_id} type={message_type} count={message_count}")

                if message_type == "chat":
                    content = data.get("content", "")
                    logger.info(f"[WebSocket] Chat message session_id={session_id} content_length={len(content)}")
                    await handle_chat_message(session_id, content, db_session)

                elif message_type == "stop":
                    logger.info(f"[WebSocket] Stop command received session_id={session_id}")
                    await manager.send_event(
                        session_id,
                        "stopped",
                        {"message": "Processing stopped by user"}
                    )

                elif message_type == "ping":
                    await manager.update_ping(session_id)
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
                    logger.debug(f"[WebSocket] Pong sent session_id={session_id}")

                elif message_type == "pong":
                    await manager.update_ping(session_id)
                    logger.debug(f"[WebSocket] Pong received session_id={session_id}")
                else:
                    logger.warning(f"[WebSocket] Unknown message type session_id={session_id} type={message_type}")

    except WebSocketDisconnect:
        connection_duration = time.time() - connection_start
        logger.info(f"[WebSocket] Disconnected session_id={session_id} duration={connection_duration:.1f}s messages_processed={message_count}")
    except Exception as e:
        connection_duration = time.time() - connection_start
        logger.error(f"[WebSocket] Error session_id={session_id} duration={connection_duration:.1f}s messages_processed={message_count} error={e}", exc_info=True)
    finally:
        await manager.disconnect(session_id)
        connection_duration = time.time() - connection_start
        logger.info(f"[WebSocket] Cleanup completed session_id={session_id} total_duration={connection_duration:.1f}s total_messages={message_count}")
        clear_request_context()


async def handle_chat_message(session_id: str, content: str, db_session):
    session_repo = SessionRepository(db_session)
    evidence_repo = EvidenceRepository(db_session)
    agent_exec_repo = AgentExecutionRepository(db_session)
    
    orchestrator = OrchestratorAgent(
        session_repo=session_repo,
        evidence_repo=evidence_repo,
        agent_exec_repo=agent_exec_repo,
    )

    async for event in orchestrator.run_stream(session_id, content):
        await manager.send_event(
            session_id,
            event["type"],
            event.get("payload", {}),
            event.get("agent"),
        )
