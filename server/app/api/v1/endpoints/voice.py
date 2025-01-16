from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from ....core.auth import get_current_user
from ....models.user import User
from ....services.voice import VoiceService
from ....core.voice import VoiceProcessor
from ....core.cache import redis_client
from ....core.metrics import track_time, voice_processing_duration_seconds
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/process")
@track_time(voice_processing_duration_seconds)
async def process_voice_command(
    audio: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process voice command and return response"""
    voice_service = VoiceService()
    
    try:
        result = await voice_service.process_voice_command(
            audio,
            current_user.id,
            background_tasks
        )
        return result
    except Exception as e:
        logger.error(f"Voice processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train")
async def train_voice_profile(
    audio_samples: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Train voice profile for user"""
    voice_service = VoiceService()
    
    try:
        result = await voice_service.train_voice_profile(
            audio_samples,
            current_user.id
        )
        return result
    except Exception as e:
        logger.error(f"Voice training failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_voice_profile(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's voice profile"""
    voice_service = VoiceService()
    
    try:
        profile = await voice_service.get_voice_profile(current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{command_id}", response_model=VoiceCommandResponse)
async def get_command_status(
    command_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a voice command"""
    try:
        # Check cache first
        cached_result = await redis_client.get(f"voice_command:{command_id}")
        if cached_result:
            return cached_result

        # Get from database if not in cache
        voice_service = VoiceService()
        result = await voice_service.get_command_status(command_id, current_user.id)
        
        # Cache result if completed
        if result["status"] in ["completed", "failed"]:
            await redis_client.set(
                f"voice_command:{command_id}",
                result,
                expire=3600
            )
        
        return result
    except Exception as e:
        logger.error(f"Failed to get command status: {str(e)}")
        raise
