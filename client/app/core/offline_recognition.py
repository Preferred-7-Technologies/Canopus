from vosk import Model, KaldiRecognizer
import json
import logging
from pathlib import Path
from typing import Optional
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class OfflineRecognizer:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.recognizer = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._ensure_model()
        self._initialize_recognizer()

    def _ensure_model(self):
        model_path = Path("data/vosk-model-small-en-us")
        if not model_path.exists():
            logger.info("Downloading Vosk model...")
            import urllib.request
            import zipfile
            
            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            zip_path = "data/model.zip"
            
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("data")
            
            Path(zip_path).unlink()

        self.model = Model(str(model_path))
        logger.info("Vosk model loaded successfully")

    def _initialize_recognizer(self):
        self.recognizer = KaldiRecognizer(
            self.model,
            self.config.VOICE_SAMPLE_RATE
        )
        self.recognizer.SetWords(True)

    async def recognize(self, audio_data: np.ndarray) -> Optional[str]:
        try:
            # Convert float32 to int16 for Vosk
            audio_int16 = (audio_data * 32768).astype(np.int16)
            
            # Run recognition in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._process_audio,
                audio_int16.tobytes()
            )
            
            if result:
                parsed = json.loads(result)
                return parsed.get("text", "")
            
            return None
        except Exception as e:
            logger.error(f"Offline recognition failed: {str(e)}")
            return None

    def _process_audio(self, audio_bytes: bytes) -> Optional[str]:
        if self.recognizer.AcceptWaveform(audio_bytes):
            return self.recognizer.Result()
        return None

    def __del__(self):
        self.executor.shutdown(wait=True)
