import json
from typing import Dict, List, Optional
from pydantic import BaseModel
import os

class Voice(BaseModel):
    id: str
    name: str
    language: str
    language_code: str
    voice_engine: str
    is_cloned: bool
    sample: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    loudness: Optional[str] = None
    style: Optional[str] = None
    tempo: Optional[str] = None
    texture: Optional[str] = None

class VoiceRegistry:
    def __init__(self, voice_file_path: str):
        self.voices: Dict[str, Voice] = {}
        self.load_voices(voice_file_path)

    def load_voices(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Voice configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            voices_data = json.load(f)
            self.voices = {
                voice_data["id"]: Voice(**voice_data)
                for voice_data in voices_data
            }

    def get_voice(self, voice_id: str) -> Optional[Voice]:
        return self.voices.get(voice_id)

    def list_voices(self, 
                    language: Optional[str] = None,
                    gender: Optional[str] = None,
                    style: Optional[str] = None) -> List[Voice]:
        filtered_voices = self.voices.values()
        
        if language:
            filtered_voices = [v for v in filtered_voices if v.language_code == language]
        if gender:
            filtered_voices = [v for v in filtered_voices if v.gender == gender]
        if style:
            filtered_voices = [v for v in filtered_voices if v.style == style]
            
        return list(filtered_voices)

    def get_default_voice(self) -> Voice:
        # Return a reliable default voice (you may want to adjust this based on your needs)
        default_voices = [v for v in self.voices.values() 
                         if v.language_code == "en-US" and 
                            v.voice_engine == "PlayHT2.0" and 
                            v.style == "narrative"]
        return default_voices[0] if default_voices else next(iter(self.voices.values()))
