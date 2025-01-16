import pytest
from ..services.tts_service import TTSService
from unittest.mock import patch, Mock
import json
import os

@pytest.fixture
def mock_voice_file(tmp_path):
    voice_data = [{
        "id": "default_voice",
        "name": "Default",
        "language": "English (US)",
        "language_code": "en-US",
        "voice_engine": "PlayHT2.0",
        "is_cloned": False,
        "style": "narrative",
        "sample": "test.wav"
    }]
    file_path = tmp_path / "test_voices.json"
    with open(file_path, 'w') as f:
        json.dump(voice_data, f)
    return str(file_path)

@pytest.fixture
def tts_service(mock_voice_file, monkeypatch):
    monkeypatch.setattr('app.config.settings.VOICE_CONFIG_PATH', mock_voice_file)
    with patch('pyht.Client') as mock_client:
        mock_client.return_value.tts.return_value = [b"test audio"]
        return TTSService()

@pytest.mark.asyncio
async def test_text_to_speech_success(tts_service):
    with patch('pyht.Client.tts', return_value=[b"test audio"]):
        async for chunk in tts_service.text_to_speech("test"):
            assert isinstance(chunk, bytes)
