import pytest
from fastapi import UploadFile
import io
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from ..services.voice_processor import VoiceProcessor

@pytest.fixture
def voice_processor():
    processor = VoiceProcessor()
    processor.ai_service.process_request = AsyncMock(
        return_value={"content": "Test response"}
    )
    return processor

@pytest.fixture
def mock_audio_file():
    return UploadFile(
        filename="test.wav",
        file=io.BytesIO(b"test audio")
    )

@pytest.mark.asyncio
async def test_process_audio(voice_processor, mock_audio_file):
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
        
        result = await voice_processor.process_audio(mock_audio_file)
        assert result["task_id"] is not None
        assert "result" in result
        assert result["stats"]["status"] == "completed"

@pytest.mark.asyncio
async def test_interrupt_processing(voice_processor):
    # Create a real coroutine that we can cancel
    async def mock_coro():
        try:
            await asyncio.sleep(0.1)  # Reduced sleep time for faster tests
            return "completed"
        except asyncio.CancelledError:
            raise

    task = asyncio.create_task(mock_coro())
    task_id = "test_task"
    voice_processor.active_tasks[task_id] = task
    
    await asyncio.sleep(0.05)  # Give task time to start
    success = await voice_processor.interrupt_processing(task_id)
    assert success
    assert task.cancelled()
