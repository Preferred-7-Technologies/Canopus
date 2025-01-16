from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, Any
from ..core.logging import setup_logging
import asyncio

logger = setup_logging()

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def handle_client(self, websocket: WebSocket, client_id: str):
        try:
            if client_id not in self.active_connections:
                await websocket.accept()
                self.active_connections[client_id] = websocket

            while True:
                data = await websocket.receive_json()
                await websocket.send_json({
                    "type": "message",
                    "content": f"Received: {data['content']}"
                })
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
        finally:
            await self.disconnect(client_id)

    async def disconnect(self, client_id: str) -> None:
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                del self.active_connections[client_id]
