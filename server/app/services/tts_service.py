from pyht import Client
from pyht.client import TTSOptions, Format
from ..config import settings
from ..core.logging import setup_logging
from ..core.voice_registry import VoiceRegistry, Voice
import asyncio
import tempfile
import os
from typing import AsyncGenerator, Optional, Union
from unittest.mock import Mock

logger = setup_logging()

class TTSService:
    def __init__(self, test_mode: bool = False):
        try:
            if test_mode:
                self.client = Mock()
                logger.info("TTS service initialized in test mode")
            elif not settings.PLAY_HT_USER_ID or not settings.PLAY_HT_API_KEY:
                logger.warning("PlayHT credentials not configured, TTS service will be unavailable")
                self.client = None
            else:
                self.client = Client(
                    user_id=settings.PLAY_HT_USER_ID,
                    api_key=settings.PLAY_HT_API_KEY
                )
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {str(e)}")
            self.client = None

        self.voice_registry = VoiceRegistry(settings.VOICE_CONFIG_PATH)
        
        # Initialize default voice
        default_voice = self.voice_registry.get_default_voice()
        
        # Handle format properly
        output_format = Format.FORMAT_WAV
        if hasattr(Format, settings.TTS_OUTPUT_FORMAT):
            output_format = getattr(Format, settings.TTS_OUTPUT_FORMAT)
        
        self.default_options = TTSOptions(
            voice=default_voice.id,
            format=output_format,
            sample_rate=settings.TTS_SAMPLE_RATE
        )

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        if not self.client and not hasattr(self, 'test_chunks'):
            logger.error("TTS service not properly initialized")
            raise RuntimeError("TTS service not available")

        try:
            # For test mode
            if hasattr(self, 'test_chunks'):
                for chunk in self.test_chunks:
                    yield chunk
                return

            # Validate and get voice
            voice = None
            if voice_id:
                voice = self.voice_registry.get_voice(voice_id)
                if not voice:
                    logger.warning(f"Voice ID {voice_id} not found, using default voice")
                    voice = self.voice_registry.get_default_voice()
            else:
                voice = self.voice_registry.get_default_voice()

            options = TTSOptions(
                voice=voice.id,
                format=self.default_options.format,
                sample_rate=self.default_options.sample_rate
            )
            # Handle speed separately if needed
            options.speed = speed

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._generate_audio,
                    text,
                    options,
                    temp_file.name,
                    voice.voice_engine
                )

                chunk_size = 1024 * 8
                with open(temp_file.name, 'rb') as audio_file:
                    while chunk := audio_file.read(chunk_size):
                        yield chunk

            finally:
                temp_file.close()
                os.unlink(temp_file.name)

        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise

    def _generate_audio(self, text: str, options: TTSOptions, output_path: str, voice_engine: str):
        """Generate audio using TTS service"""
        with open(output_path, "wb") as audio_file:
            # Remove voice_engine from kwargs if not supported
            kwargs = {}
            if hasattr(self.client, 'voice_engine'):
                kwargs['voice_engine'] = voice_engine

            for chunk in self.client.tts(text, options, **kwargs):
                audio_file.write(chunk)

    def list_available_voices(self, language: Optional[str] = None,
                            gender: Optional[str] = None,
                            style: Optional[str] = None):
        """
        Get a list of available voices with optional filtering
        """
        return self.voice_registry.list_voices(language, gender, style)

    def get_voice_details(self, voice_id: str) -> Optional[Voice]:
        """
        Get detailed information about a specific voice
        """
        return self.voice_registry.get_voice(voice_id)
