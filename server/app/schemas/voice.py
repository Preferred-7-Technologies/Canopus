from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class VoiceCommandBase(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class VoiceCommandCreate(VoiceCommandBase):
    user_id: int
    audio_data: bytes

class VoiceCommandResponse(VoiceCommandBase):
    id: str
    status: str
    created_at: datetime
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class VoiceProfileBase(BaseModel):
    user_id: int
    model_data: Dict[str, Any]

class VoiceProfileResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True

class VoiceProcessingResponse(BaseModel):
    command_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
