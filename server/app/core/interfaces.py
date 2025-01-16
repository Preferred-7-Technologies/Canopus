from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional

class VoiceProcessorInterface(ABC):
    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def interrupt_processing(self, task_id: str) -> bool:
        pass

class TTSInterface(ABC):
    @abstractmethod
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        pass

class STTInterface(ABC):
    @abstractmethod
    async def speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        pass

class AIProcessorInterface(ABC):
    @abstractmethod
    async def analyze_intent(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_response(self, intent: Dict[str, Any]) -> str:
        pass
