from celery import Task
from ...core.command import CommandProcessor
from ...core.voice import VoiceProcessor
from ...database import SessionLocal
from ...models import VoiceCommand
import logging
from typing import Dict, Any
from .celery_app import celery_app

logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None

@celery_app.task(base=DatabaseTask, bind=True)
def process_voice_command(self, audio_data: bytes, user_id: int) -> Dict[str, Any]:
    """Process voice command in background"""
    try:
        processor = VoiceProcessor()
        result = await processor.process_audio(audio_data, user_id)
        
        # Store result in database
        command = VoiceCommand(
            user_id=user_id,
            text=result["text"],
            confidence=result["confidence"],
            status="completed",
            metadata=result["metadata"]
        )
        self.db.add(command)
        self.db.commit()
        
        return {
            "status": "success",
            "command_id": command.id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Voice command processing failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@celery_app.task(base=DatabaseTask, bind=True)
def execute_command_action(self, action: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Execute command action in background"""
    try:
        processor = CommandProcessor()
        result = await processor.execute_action(action, user_id)
        
        return {
            "status": "success",
            "action_type": action["type"],
            "result": result
        }
    except Exception as e:
        logger.error(f"Action execution failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
