from pydantic_settings import BaseSettings
from pathlib import Path
import json
import os

class ClientConfig(BaseSettings):
    API_URL: str = "http://localhost:8000"
    API_VERSION: str = "v1"
    CLIENT_ID: str = ""
    DEVICE_ID: str = ""
    LOCAL_DB_PATH: str = "data/local.db"
    VOICE_SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self):
        super().__init__()
        self._ensure_directories()
        self._load_or_create_device_id()

    def _ensure_directories(self):
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

    def _load_or_create_device_id(self):
        config_file = Path("data/device_config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                data = json.load(f)
                self.DEVICE_ID = data.get("device_id", "")
        
        if not self.DEVICE_ID:
            import uuid
            self.DEVICE_ID = str(uuid.uuid4())
            with open(config_file, "w") as f:
                json.dump({"device_id": self.DEVICE_ID}, f)
