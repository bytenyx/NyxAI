"""WebSocket endpoints for NyxAI.

This module provides WebSocket endpoints for real-time event streaming,
including anomaly notifications and system status updates.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

router = APIRouter()


class EventType(str, Enum):
    """Types of WebSocket events."""

    ANOMALY_DETECTED = "anomaly_detected"
    ANOMALY_RESOLVED = "anomaly_resolved"
    ANOMALY_UPDATED = "anomaly_updated"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FAILED = "recovery_failed"
    SYSTEM_STATUS = "system_status"
    RCA_COMPLETED = "rca_completed"
    AGENT_STATUS = "agent_status"
    PING = "ping"
    PONG = "pong"


class WebSocketEvent(BaseModel):
    """WebSocket event model."""

    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
    incident_id: str | None = None

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps({
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "incident_id": self.incident_id,
        })


class ConnectionManager:
    """Manages WebSocket connections.

    This class handles multiple WebSocket connections and provides
    methods for broadcasting events to connected clients.

    Attributes:
        _connections: Set of active WebSocket connections.
        _subscriptions: Mapping of event types to connected clients.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: set[WebSocket] = set()
        self._subscriptions: dict[EventType, set[WebSocket]] = {}
        self._client_info: dict[WebSocket, dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str | None = None,
        subscriptions: list[EventType] | None = None,
    ) -> None:
        """Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            client_id: Optional client identifier.
            subscriptions: List of event types to subscribe to.
        """
        await websocket.accept()
        self._connections.add(websocket)

        # Store client info
        self._client_info[websocket] = {
            "client_id": client_id or str(id(websocket)),
            "connected_at": datetime.utcnow(),
            "subscriptions": subscriptions or list(EventType),
        }

        # Subscribe to events
        if subscriptions:
            for event_type in subscriptions:
                if event_type not in self._subscriptions:
                    self._subscriptions[event_type] = set()
                self._subscriptions[event_type].add(websocket)
        else:
            # Subscribe to all events by default
            for event_type in EventType:
                if event_type not in self._subscriptions:
                    self._subscriptions[event_type] = set()
                self._subscriptions[event_type].add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove.
        """
        self._connections.discard(websocket)

        # Remove from subscriptions
        for subscribers in self._subscriptions.values():
            subscribers.discard(websocket)

        # Remove client info
        if websocket in self._client_info:
            del self._client_info[websocket]

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Broadcast an event to all subscribed clients.

        Args:
            event: The event to broadcast.
        """
        if event.event_type not in self._subscriptions:
            return

        message = event.to_json()
        disconnected = set()

        for connection in self._subscriptions[event.event_type]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_client(
        self,
        websocket: WebSocket,
        event: WebSocketEvent,
    ) -> bool:
        """Send an event to a specific client.

        Args:
            websocket: The target WebSocket connection.
            event: The event to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            await websocket.send_text(event.to_json())
            return True
        except Exception:
            self.disconnect(websocket)
            return False

    async def broadcast_system_status(self, status_data: dict[str, Any]) -> None:
        """Broadcast system status to all clients.

        Args:
            status_data: System status information.
        """
        event = WebSocketEvent(
            event_type=EventType.SYSTEM_STATUS,
            data=status_data,
        )
        await self.broadcast(event)

    async def notify_anomaly_detected(
        self,
        anomaly_data: dict[str, Any],
        incident_id: str | None = None,
    ) -> None:
        """Notify clients of a detected anomaly.

        Args:
            anomaly_data: Anomaly information.
            incident_id: Optional incident ID.
        """
        event = WebSocketEvent(
            event_type=EventType.ANOMALY_DETECTED,
            data=anomaly_data,
            incident_id=incident_id,
        )
        await self.broadcast(event)

    async def notify_recovery_completed(
        self,
        recovery_data: dict[str, Any],
        incident_id: str | None = None,
    ) -> None:
        """Notify clients of a completed recovery.

        Args:
            recovery_data: Recovery information.
            incident_id: Optional incident ID.
        """
        event = WebSocketEvent(
            event_type=EventType.RECOVERY_COMPLETED,
            data=recovery_data,
            incident_id=incident_id,
        )
        await self.broadcast(event)

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of active connections.
        """
        return len(self._connections)

    def get_client_info(self, websocket: WebSocket) -> dict[str, Any] | None:
        """Get information about a connected client.

        Args:
            websocket: The WebSocket connection.

        Returns:
            Client information or None if not found.
        """
        return self._client_info.get(websocket)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time events.

    This endpoint provides a persistent connection for receiving
    real-time events from the NyxAI system.

    Query Parameters:
        client_id: Optional client identifier.
        subscriptions: Comma-separated list of event types to subscribe to.
    """
    # Parse query parameters
    query_params = websocket.query_params
    client_id = query_params.get("client_id")
    subscriptions_str = query_params.get("subscriptions", "")

    subscriptions = None
    if subscriptions_str:
        try:
            subscriptions = [EventType(s.strip()) for s in subscriptions_str.split(",")]
        except ValueError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Accept connection
    await manager.connect(websocket, client_id, subscriptions)

    client_info = manager.get_client_info(websocket)
    client_id_display = client_info["client_id"] if client_info else "unknown"

    # Send connection confirmation
    await manager.send_to_client(
        websocket,
        WebSocketEvent(
            event_type=EventType.SYSTEM_STATUS,
            data={
                "message": "Connected to NyxAI event stream",
                "client_id": client_id_display,
                "subscriptions": [s.value for s in (subscriptions or EventType)],
            },
        ),
    )

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type", "")

                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_to_client(
                        websocket,
                        WebSocketEvent(
                            event_type=EventType.PONG,
                            data={"timestamp": datetime.utcnow().isoformat()},
                        ),
                    )

                elif message_type == "subscribe":
                    # Handle subscription request
                    event_types = message.get("event_types", [])
                    new_subscriptions = []
                    for et in event_types:
                        try:
                            event_type = EventType(et)
                            if event_type not in self._subscriptions:
                                self._subscriptions[event_type] = set()
                            self._subscriptions[event_type].add(websocket)
                            new_subscriptions.append(et)
                        except ValueError:
                            pass

                    await manager.send_to_client(
                        websocket,
                        WebSocketEvent(
                            event_type=EventType.SYSTEM_STATUS,
                            data={
                                "message": "Subscriptions updated",
                                "subscriptions": new_subscriptions,
                            },
                        ),
                    )

                elif message_type == "unsubscribe":
                    # Handle unsubscription request
                    event_types = message.get("event_types", [])
                    for et in event_types:
                        try:
                            event_type = EventType(et)
                            if event_type in self._subscriptions:
                                self._subscriptions[event_type].discard(websocket)
                        except ValueError:
                            pass

                    await manager.send_to_client(
                        websocket,
                        WebSocketEvent(
                            event_type=EventType.SYSTEM_STATUS,
                            data={"message": "Unsubscribed from events"},
                        ),
                    )

            except json.JSONDecodeError:
                await manager.send_to_client(
                    websocket,
                    WebSocketEvent(
                        event_type=EventType.SYSTEM_STATUS,
                        data={"error": "Invalid JSON message"},
                    ),
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/ws/stats", summary="Get WebSocket statistics")
async def get_websocket_stats() -> dict[str, Any]:
    """Get WebSocket connection statistics.

    Returns:
        Dictionary with connection statistics.
    """
    return {
        "active_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# Helper functions for broadcasting events from other parts of the application

async def broadcast_anomaly_detected(anomaly_data: dict[str, Any]) -> None:
    """Broadcast anomaly detected event.

    Args:
        anomaly_data: Anomaly information.
    """
    await manager.notify_anomaly_detected(anomaly_data)


async def broadcast_recovery_completed(recovery_data: dict[str, Any]) -> None:
    """Broadcast recovery completed event.

    Args:
        recovery_data: Recovery information.
    """
    await manager.notify_recovery_completed(recovery_data)


async def broadcast_agent_status(agent_name: str, status: str, data: dict[str, Any]) -> None:
    """Broadcast agent status update.

    Args:
        agent_name: Name of the agent.
        status: Agent status.
        data: Additional status data.
    """
    event = WebSocketEvent(
        event_type=EventType.AGENT_STATUS,
        data={
            "agent_name": agent_name,
            "status": status,
            **data,
        },
    )
    await manager.broadcast(event)


async def broadcast_rca_completed(service_id: str, root_causes: list[dict[str, Any]]) -> None:
    """Broadcast RCA completed event.

    Args:
        service_id: Service ID.
        root_causes: Identified root causes.
    """
    event = WebSocketEvent(
        event_type=EventType.RCA_COMPLETED,
        data={
            "service_id": service_id,
            "root_causes": root_causes,
        },
    )
    await manager.broadcast(event)
