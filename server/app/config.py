from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import torch
import secrets

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Canopus"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/Canopus"
    
    # Azure AI
    AZURE_API_KEY: str = os.getenv("AZURE_API_KEY", "")
    AZURE_ENDPOINT: str = os.getenv("AZURE_ENDPOINT", "")
    
    # Azure AI Settings
    AZURE_TOKEN: str = os.getenv("AZURE_API_KEY", "")
    AZURE_DEFAULT_MODEL: str = "Codestral-2501"
    AZURE_IMAGE_MAX_SIZE: int = 4 * 1024 * 1024  # 4MB
    
    # TTS Settings
    PLAY_HT_USER_ID: str = os.getenv("PLAY_HT_USER_ID", "")
    PLAY_HT_API_KEY: str = os.getenv("PLAY_HT_API_KEY", "")
    DEFAULT_VOICE_URL: str = "s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json"
    TTS_SAMPLE_RATE: int = 44100
    TTS_OUTPUT_FORMAT: str = "FORMAT_WAV"  # Must match Format enum values in pyht
    
    # Whisper Settings
    WHISPER_MODEL: str = "base"
    WHISPER_LANGUAGE: str = "en"
    WHISPER_DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Voice Configuration
    VOICE_CONFIG_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice.json")
    DEFAULT_VOICE_ID: Optional[str] = None  # Will be set dynamically based on VoiceRegistry

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Voice Processing
    VOICE_MODEL_PATH: str = "models/voice"
    MAX_AUDIO_LENGTH: int = 30  # seconds
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
