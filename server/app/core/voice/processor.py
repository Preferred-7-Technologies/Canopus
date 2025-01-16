import whisper
import torch
import numpy as np
from typing import Optional, Dict, Any
import logging
from ...config import settings
from .encoder import AudioEncoder
from .validator import AudioValidator
from ..cache import AsyncRedisCache

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        self.model = whisper.load_model(settings.WHISPER_MODEL)
        self.device = torch.device(settings.WHISPER_DEVICE)
        self.encoder = AudioEncoder()
        self.validator = AudioValidator()
        self.cache = AsyncRedisCache()
        self.model.to(self.device)
        logger.info(f"Voice processor initialized with {settings.WHISPER_MODEL} model on {self.device}")

    async def process_audio(self, audio_data: bytes, user_id: str) -> Dict[str, Any]:
        """Process audio data and return transcription and metadata"""
        try:
            # Check cache first
            cache_key = f"voice_process:{self._generate_audio_hash(audio_data)}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            # Validate audio
            self.validator.validate(audio_data)
            
            # Encode audio for model
            audio_array = self.encoder.encode(audio_data)
            
            # Process with Whisper
            result = await self._transcribe(audio_array)
            
            # Add metadata
            processed_result = {
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"],
                "confidence": float(result["segments"][0]["confidence"]) if result["segments"] else 0.0,
                "processing_metadata": {
                    "model": settings.WHISPER_MODEL,
                    "device": str(self.device),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # Cache result
            await self.cache.set(cache_key, processed_result, expire=3600)
            
            return processed_result

        except Exception as e:
            logger.error(f"Voice processing failed: {str(e)}")
            raise

    async def _transcribe(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Transcribe audio using Whisper model"""
        try:
            with torch.no_grad():
                result = self.model.transcribe(
                    audio_array,
                    language=settings.WHISPER_LANGUAGE,
                    task="transcribe"
                )
            return result
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    def _generate_audio_hash(self, audio_data: bytes) -> str:
        """Generate a hash for audio data for caching"""
        return hashlib.sha256(audio_data).hexdigest()

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'model'):
                del self.model
            torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
