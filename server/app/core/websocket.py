from fastapi import WebSocket
from typing import Dict, Set
import logging
import asyncio
from datetime import datetime
from .metrics import websocket_connections, websocket_messages
from .cache import redis_client

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_last_seen: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_last_seen[user_id] = datetime.utcnow()
        
        # Update metrics
        websocket_connections.inc()
        
        # Start cleanup if not running
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        logger.info(f"Client connected: {user_id}")

    async def disconnect(self, websocket: WebSocket):
        for user_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.active_connections[user_id]
                websocket_connections.dec()
                logger.info(f"Client disconnected: {user_id}")
                break

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            websocket_messages.inc()
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            await self.disconnect(websocket)

    async def broadcast(self, message: str, exclude: Set[WebSocket] = None):
        exclude = exclude or set()
        for connections in self.active_connections.values():
            for connection in connections - exclude:
                await self.send_personal_message(message, connection)

    async def notify_user(self, user_id: str, message: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await self.send_personal_message(message, connection)

    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")

    async def _cleanup_stale_connections(self):
        now = datetime.utcnow()
        stale_threshold = 3600  # 1 hour

        for user_id, last_seen in list(self.user_last_seen.items()):
            if (now - last_seen).total_seconds() > stale_threshold:
                if user_id in self.active_connections:
                    connections = self.active_connections[user_id]
                    for websocket in connections:
                        await self.disconnect(websocket)
                    logger.info(f"Cleaned up stale connection for user: {user_id}")
