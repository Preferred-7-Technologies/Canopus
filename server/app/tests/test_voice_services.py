import pytest
from ..services.voice_processor import VoiceProcessor
from ..services.tts_service import TTSService
from ..services.stt_service import STTService
from fastapi import UploadFile
import io
from unittest.mock import Mock, patch, AsyncMock
import json
import numpy as np

@pytest.fixture
def voice_services():
    return {
        "processor": VoiceProcessor(),
        "tts": TTSService(),
        "stt": STTService()
    }

@pytest.fixture
def sample_audio_data():
    return b"mock audio data"

@pytest.fixture
def mock_tts():
    with patch('app.services.tts_service.TTSService') as mock:
        tts = mock.return_value
        tts.text_to_speech = AsyncMock()
        tts.text_to_speech.return_value = [b"test_audio_chunk"]
        yield tts

class TestVoiceProcessor:
    @pytest.mark.asyncio
    async def test_process_audio_success(self, voice_services, sample_audio_data):
        with patch('app.services.stt_service.STTService.speech_to_text') as mock_stt, \
             patch('app.services.azure_ai.AzureAIService.analyze_text') as mock_analyze:
            
            mock_stt.return_value = {
                "text": "test command",
                "confidence": 0.95,
                "language": "en",
                "segments": []
            }
            mock_analyze.return_value = {
                "intent": "command",
                "confidence": 0.9
            }

            audio_file = UploadFile(
                filename="test.wav",
                file=io.BytesIO(sample_audio_data)
            )
            result = await voice_services["processor"].process_audio(audio_file)
            
            assert result["task_id"] is not None
            assert result["result"]["text"] == "test command"
            assert result["stats"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_audio_failure(self, voice_services, sample_audio_data):
        with patch('app.services.stt_service.STTService.speech_to_text') as mock_stt:
            mock_stt.side_effect = Exception("STT processing failed")
            
            audio_file = UploadFile(
                filename="test.wav",
                file=io.BytesIO(sample_audio_data)
            )
            
            with pytest.raises(Exception):
                await voice_services["processor"].process_audio(audio_file)

class TestTTSService:
    @pytest.mark.asyncio
    async def test_text_to_speech_success(self, mock_tts):
        # Set up mock TTS service
        mock_tts.test_chunks = [b"test_audio_chunk"]
        text = "Test speech synthesis"
        chunks = []
        async for chunk in mock_tts.text_to_speech(text):
            chunks.append(chunk)
        assert chunks == [b"test_audio_chunk"]

    @pytest.mark.asyncio
    async def test_voice_selection(self, voice_services):
        # Initialize TTS service in test mode
        tts_service = TTSService(test_mode=True)
        tts_service.test_chunks = [b"test", b"audio", b"data"]
        voice_services["tts"] = tts_service

        text = "Test with specific voice"
        voice_id = "test_voice_id"
        voice_uri = "s3://voices/test_voice"

        with patch('app.core.voice_registry.VoiceRegistry.get_voice') as mock_get_voice, \
             patch('pyht.client.Client.tts') as mock_tts:
            # Mock voice details
            mock_voice = Mock()
            mock_voice.id = voice_id
            mock_voice.voice_engine = "PlayHT2.0"
            mock_voice.voice_uri = voice_uri
            mock_get_voice.return_value = mock_voice

            # Mock TTS response
            mock_tts.return_value = iter([b"test", b"audio", b"data"])

            # Test TTS generation
            chunks = []
            async for chunk in voice_services["tts"].text_to_speech(text, voice_id):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert all(isinstance(chunk, bytes) for chunk in chunks)
            mock_tts.assert_called_once()

class TestSTTService:
    @pytest.mark.asyncio
    async def test_speech_to_text_success(self, voice_services, sample_audio_data):
        mock_result = {
            "text": "test transcription",
            "language": "en",
            "segments": [{"confidence": 0.95}]
        }
        
        with patch.object(voice_services["stt"].model, 'transcribe', 
                         return_value=mock_result):
            result = await voice_services["stt"].speech_to_text(b"test_audio")
            assert result["text"] == "test transcription"
            assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_speech_to_text_error_handling(self, voice_services):
        with pytest.raises(Exception):
            await voice_services["stt"].speech_to_text(b"invalid audio data")

    def test_processing_history(self, voice_services):
        history = voice_services["stt"].get_processing_history()
        assert isinstance(history, dict)
