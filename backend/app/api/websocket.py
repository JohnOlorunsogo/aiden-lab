"""WebSocket handlers for real-time error streaming."""
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from app.models.error import ErrorWithSolution

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        # Convert to JSON
        json_message = json.dumps(message, default=str)
        
        # Send to all connections
        disconnected = set()
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.add(connection)
        
        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                self.active_connections -= disconnected
    
    async def broadcast_error(self, error_with_solution: ErrorWithSolution):
        """Broadcast an error update to all clients."""
        message = {
            "type": "error_update",
            "data": {
                "error": {
                    "id": error_with_solution.error.id,
                    "device_id": error_with_solution.error.device_id,
                    "timestamp": error_with_solution.error.timestamp.isoformat(),
                    "error_line": error_with_solution.error.error_line,
                    "severity": error_with_solution.error.severity.value,
                    "created_at": error_with_solution.error.created_at.isoformat()
                },
                "solution": None
            }
        }
        
        if error_with_solution.solution:
            message["data"]["solution"] = {
                "id": error_with_solution.solution.id,
                "root_cause": error_with_solution.solution.root_cause,
                "impact": error_with_solution.solution.impact,
                "solution": error_with_solution.solution.solution,
                "prevention": error_with_solution.solution.prevention
            }
        
        await self.broadcast(message)
    
    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time error updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
