import pytest
from ..core.voice_registry import VoiceRegistry, Voice
import json
import tempfile
import os

@pytest.fixture
def mock_voice_data():
    return {
        "id": "test_voice",
        "name": "Test Voice",
        "language": "English (US)",
        "language_code": "en-US",
        "voice_engine": "PlayHT2.0",
        "is_cloned": False,
        "style": "narrative"
    }

@pytest.fixture
def voice_registry(tmp_path, mock_voice_data):
    file_path = tmp_path / "test_voices.json"
    with open(file_path, 'w') as f:
        json.dump([mock_voice_data], f)
    return VoiceRegistry(str(file_path))

class TestVoiceRegistry:
    def test_load_voices(self, voice_registry, mock_voice_data):
        assert len(voice_registry.voices) == 1
        voice = next(iter(voice_registry.voices.values()))
        assert voice.id == mock_voice_data["id"]
        assert voice.name == mock_voice_data["name"]

    def test_get_default_voice(self, voice_registry):
        voice = voice_registry.get_default_voice()
        assert voice is not None
        assert voice.language_code == "en-US"
