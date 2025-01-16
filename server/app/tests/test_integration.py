import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient
from ..services.voice_processor import VoiceProcessor
from ..services.tts_service import TTSService
from ..core.security import create_access_token
import json
import io
import numpy as np
from scipy.io import wavfile
from unittest.mock import patch, AsyncMock

@pytest.fixture
def auth_headers():
    access_token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.integration
class TestVoiceIntegration:
    
    @pytest.mark.asyncio
    async def test_voice_processing_pipeline(self, client: TestClient, auth_headers):
        # Create a proper WAV file for testing
        sample_rate = 16000
        duration = 1  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sample_rate, audio_data)
        wav_buffer.seek(0)
        
        files = {
            "audio_file": ("test.wav", wav_buffer, "audio/wav")
        }
        
        # Patch the necessary services
        with patch('app.services.stt_service.STTService.speech_to_text') as mock_stt, \
             patch('app.services.azure_ai.AzureAIService.analyze_text') as mock_analyze:
            
            mock_stt.return_value = {
                "text": "test command",
                "confidence": 0.95,
                "language": "en",
                "segments": []
            }
            mock_analyze.return_value = {
                "analysis": "Test analysis",
                "usage": {}
            }
            
            response = client.post("/api/v1/voice/process", files=files, headers=auth_headers)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: TestClient):
        access_token = create_access_token({"sub": "test@example.com"})
        client_id = "test_client"
        
        with patch('app.core.cache.RedisClient.exists', new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False  # Token not blacklisted
            
            async with client.websocket_connect(
                f"/api/v1/ws/{client_id}?token={access_token}"
            ) as websocket:
                await websocket.send_json({
                    "type": "message",
                    "content": "test message"
                })
                
                response = await websocket.receive_json()
                assert response["type"] == "message"
                assert response["content"] == "Received: test message"
