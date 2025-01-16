import websockets
import asyncio
import json
import logging
from typing import Optional, Callable
from .exceptions import WebSocketError

logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, config):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = asyncio.Event()
        self.handlers = {}
        self._reconnect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self):
        try:
            ws_url = f"ws://{self.config.API_URL}/ws"
            self.ws = await websockets.connect(
                ws_url,
                extra_headers={"Authorization": f"Bearer {self.config.TOKEN}"}
            )
            self.connected.set()
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            logger.info("WebSocket connected successfully")
            await self._listen()
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            self.connected.clear()
            await self._schedule_reconnect()

    async def _heartbeat(self):
        while self.connected.is_set():
            try:
                await self.ws.ping()
                await asyncio.sleep(30)
            except Exception:
                break

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                event_type = data.get("type")
                if event_type in self.handlers:
                    await self.handlers[event_type](data)
        except Exception as e:
            logger.error(f"WebSocket listen error: {str(e)}")
            self.connected.clear()
            await self._schedule_reconnect()

    async def send(self, message: dict):
        if not self.connected.is_set():
            raise WebSocketError("WebSocket not connected")
        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"WebSocket send error: {str(e)}")
            raise WebSocketError(str(e))

    def register_handler(self, event_type: str, handler: Callable):
        self.handlers[event_type] = handler

    async def _schedule_reconnect(self):
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self, max_attempts=5):
        attempt = 0
        while attempt < max_attempts and not self.connected.is_set():
            try:
                await asyncio.sleep(2 ** attempt)
                await self.connect()
                break
            except Exception:
                attempt += 1
