from ..core.celery_app import celery_app
from ..services.stt_service import STTService
from ..core.logging import setup_logging
from typing import Dict, Any
import numpy as np

logger = setup_logging()

class VoiceTaskProcessor:
    def __init__(self):
        self.stt_service = STTService()

    async def process_voice_data(self, audio_data: bytes) -> Dict[str, Any]:
        try:
            # Process with STT service
            result = await self.stt_service.speech_to_text(audio_data)
            
            # Additional processing/analysis could be added here
            processed_result = {
                "text": result["text"],
                "confidence": result["confidence"],
                "language": result["language"],
                "word_count": len(result["text"].split()),
                "segments": [
                    {
                        "text": seg["text"],
                        "confidence": seg["confidence"],
                        "start": seg["start"],
                        "end": seg["end"]
                    }
                    for seg in result["segments"]
                ],
                "metadata": {
                    "average_confidence": float(np.mean([s["confidence"] for s in result["segments"]])),
                    "processing_time": result.get("processing_time", 0)
                }
            }
            
            return processed_result

        except Exception as e:
            logger.error(f"Voice processing failed: {str(e)}")
            raise

@celery_app.task(bind=True, name="process_voice_command")
def process_voice_command(self, audio_data: bytes) -> Dict[str, Any]:
    """Celery task for processing voice commands"""
    processor = VoiceTaskProcessor()
    return asyncio.run(processor.process_voice_data(audio_data))
