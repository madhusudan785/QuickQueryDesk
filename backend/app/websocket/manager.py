"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications.

    Connections are organized by role:
    - Agents: receive ticket_created events
    - Employees: keyed by user_id, receive ticket_resolved events for their tickets

    This is an in-memory manager. If the server restarts, all connections are lost.
    REST APIs remain the source of truth — WebSocket is supplementary.
    """

    def __init__(self):
        # Agent connections: list of WebSocket instances
        self.agent_connections: list[WebSocket] = []
        # Employee connections: user_id -> list of WebSocket instances
        self.employee_connections: dict[str, list[WebSocket]] = {}

    async def connect_agent(self, websocket: WebSocket):
        """Accept and register an agent WebSocket connection."""
        await websocket.accept()
        self.agent_connections.append(websocket)
        logger.info(f"Agent connected. Total agent connections: {len(self.agent_connections)}")

    async def connect_employee(self, websocket: WebSocket, user_id: str):
        """Accept and register an employee WebSocket connection."""
        await websocket.accept()
        if user_id not in self.employee_connections:
            self.employee_connections[user_id] = []
        self.employee_connections[user_id].append(websocket)
        logger.info(f"Employee {user_id} connected. Connections: {len(self.employee_connections[user_id])}")

    def disconnect_agent(self, websocket: WebSocket):
        """Remove a disconnected agent WebSocket."""
        if websocket in self.agent_connections:
            self.agent_connections.remove(websocket)
        logger.info(f"Agent disconnected. Total agent connections: {len(self.agent_connections)}")

    def disconnect_employee(self, websocket: WebSocket, user_id: str):
        """Remove a disconnected employee WebSocket."""
        if user_id in self.employee_connections:
            if websocket in self.employee_connections[user_id]:
                self.employee_connections[user_id].remove(websocket)
            if not self.employee_connections[user_id]:
                del self.employee_connections[user_id]
        logger.info(f"Employee {user_id} disconnected.")

    async def notify_agents(self, event: str, data: dict[str, Any]):
        """Send a message to all connected agents."""
        message = json.dumps({"event": event, "data": data})
        disconnected = []
        for ws in self.agent_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect_agent(ws)

    async def notify_employee(self, user_id: str, event: str, data: dict[str, Any]):
        """Send a message to a specific employee."""
        if user_id not in self.employee_connections:
            return
        message = json.dumps({"event": event, "data": data})
        disconnected = []
        for ws in self.employee_connections.get(user_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect_employee(ws, user_id)


# Global singleton
manager = ConnectionManager()
