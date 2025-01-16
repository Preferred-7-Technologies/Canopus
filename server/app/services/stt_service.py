import os
import torch
import whisper
from ..config import settings
from ..core.logging import setup_logging
import asyncio
import tempfile
from typing import Dict, Any
import numpy as np
from datetime import datetime

logger = setup_logging()

class STTService:
    def __init__(self):
        self.model = None
        self.processing_history = {}
        self._initialize_model()

    def _initialize_model(self):
        """Initialize Whisper model with proper error handling"""
        try:
            # Ensure CUDA is available if specified
            if settings.WHISPER_DEVICE == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                settings.WHISPER_DEVICE = "cpu"

            # Load model
            self.model = whisper.load_model(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                download_root=os.path.join(os.path.dirname(__file__), "models")
            )
            logger.info(f"Whisper model loaded successfully on {settings.WHISPER_DEVICE}")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise RuntimeError(f"Could not initialize Whisper model: {str(e)}")

    async def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Convert speech to text using Whisper"""
        if not self.model:
            raise RuntimeError("Whisper model not initialized")

        process_id = os.urandom(16).hex()
        start_time = datetime.now()

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file.close()

                # Run transcription in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._transcribe_audio,
                    temp_file.name
                )

                # Calculate metrics
                confidence = np.mean([s["confidence"] for s in result["segments"]])

                self.processing_history[process_id] = {
                    "timestamp": start_time,
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "confidence": confidence,
                    "language": result["language"]
                }

                return {
                    "text": result["text"],
                    "language": result["language"],
                    "segments": result["segments"],
                    "confidence": float(confidence),
                    "process_id": process_id
                }

        except Exception as e:
            self.processing_history[process_id] = {
                "timestamp": start_time,
                "error": str(e)
            }
            logger.error(f"Speech-to-text conversion failed: {str(e)}")
            raise
        finally:
            if 'temp_file' in locals():
                os.unlink(temp_file.name)

    def get_processing_history(self, limit: int = 100) -> Dict[str, Dict]:
        """Get recent processing history"""
        sorted_items = sorted(
            self.processing_history.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        return dict(sorted_items[:limit])

    def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file using Whisper"""
        return self.model.transcribe(
            audio_path,
            language=settings.WHISPER_LANGUAGE,
            fp16=False
        )
