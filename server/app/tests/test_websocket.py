import pytest
from fastapi import WebSocket
from unittest.mock import AsyncMock, Mock, patch
from ..api.websocket import WebSocketManager
from ..core.security import create_access_token

@pytest.fixture
def mock_websocket():
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_bytes = AsyncMock(return_value=b"test audio data")
    websocket.send_json = AsyncMock()
    websocket.send_bytes = AsyncMock()
    return websocket

class TestWebSocket:
    @pytest.mark.asyncio
    async def test_websocket_manager(self, mock_websocket):
        manager = WebSocketManager()
        client_id = "test_client"
        user = {"id": "test_user"}
        
        # Test connection
        mock_websocket.accept = AsyncMock()
        await manager.handle_client(mock_websocket, client_id)
        mock_websocket.accept.assert_called_once()

        # Verify message handling
        mock_websocket.receive_json.return_value = {
            "type": "message",
            "content": "test message"
        }
        
        # Verify message response
        expected_response = {
            "type": "message",
            "content": "Received: test message"
        }
        mock_websocket.send_json.assert_called_with(expected_response)

    @pytest.mark.asyncio
    async def test_websocket_disconnect(self, mock_websocket):
        manager = WebSocketManager()
        client_id = "test_client"
        
        # Test disconnection
        await manager.disconnect(client_id)
        assert client_id not in manager.active_connections
