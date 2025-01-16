from typing import Dict, Any, List, Optional
import logging
from fastapi import UploadFile, BackgroundTasks
from ..core.voice import VoiceProcessor
from ..core.command import CommandProcessor
from ..models import VoiceCommand, VoiceProfile
from ..database import get_db
from sqlalchemy.orm import Session
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.voice_processor = VoiceProcessor()
        self.command_processor = CommandProcessor()
        self.db = next(get_db())

    async def process_voice_command(
        self,
        audio: UploadFile,
        user_id: int,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Process voice command and return response"""
        try:
            # Read audio data
            audio_data = await audio.read()
            
            # Process voice command
            text_result = await self.voice_processor.transcribe(audio_data)
            
            # Process command
            command_result = await self.command_processor.process(
                text_result["text"],
                user_id
            )
            
            # Store result
            command = VoiceCommand(
                user_id=user_id,
                text=text_result["text"],
                confidence=text_result["confidence"],
                result=command_result,
                audio_metadata=text_result["metadata"]
            )
            self.db.add(command)
            self.db.commit()
            
            return {
                "id": command.id,
                "text": text_result["text"],
                "confidence": text_result["confidence"],
                "result": command_result
            }
            
        except Exception as e:
            logger.error(f"Voice processing failed: {str(e)}")
            raise

    async def train_voice_profile(
        self,
        audio_samples: List[UploadFile],
        user_id: int
    ) -> Dict[str, Any]:
        """Train voice profile for user"""
        try:
            # Process voice samples
            profile_data = await self.voice_processor.create_profile(
                [await sample.read() for sample in audio_samples]
            )
            
            # Store voice profile
            profile = VoiceProfile(
                user_id=user_id,
                model_data=profile_data
            )
            self.db.add(profile)
            self.db.commit()
            
            return {
                "id": profile.id,
                "created_at": profile.created_at.isoformat(),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Voice training failed: {str(e)}")
            raise

    async def get_voice_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's voice profile"""
        try:
            profile = self.db.query(VoiceProfile).filter(
                VoiceProfile.user_id == user_id,
                VoiceProfile.is_active == True
            ).first()
            
            if not profile:
                return None
                
            return {
                "id": profile.id,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                "metadata": profile.model_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get voice profile: {str(e)}")
            raise
