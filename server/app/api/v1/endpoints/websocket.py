from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from ....core.auth import get_current_user_ws
from ....core.websocket import ConnectionManager
from ....core.command import CommandProcessor
from ....schemas.command import CommandResponse
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)
router = APIRouter()
manager = ConnectionManager()
command_processor = CommandProcessor()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Depends(get_current_user_ws)
):
    await manager.connect(websocket, token)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command_data = json.loads(data)
                response = await command_processor.process(
                    command_data,
                    token
                )
                await manager.send_personal_message(
                    json.dumps(response),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                await manager.send_personal_message(
                    json.dumps({
                        "error": str(e),
                        "status": "error"
                    }),
                    websocket
                )
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
