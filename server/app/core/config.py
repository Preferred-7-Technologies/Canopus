from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Canopus"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    DATABASE_URL: str = "sqlite:///./data/app.db"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Azure AI Configuration
    AZURE_ENDPOINT: str = ""
    AZURE_API_KEY: str = ""
    AZURE_DEPLOYMENT_NAME: str = ""
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Voice Processing
    MAX_AUDIO_SIZE_MB: int = 10
    SUPPORTED_AUDIO_FORMATS: List[str] = ["wav", "mp3"]
    SAMPLE_RATE: int = 16000
    
    # Monitoring
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    
    # Template Repository
    TEMPLATE_STORAGE_PATH: Path = Path("data/templates")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
