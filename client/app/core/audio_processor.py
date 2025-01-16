import numpy as np
from typing import Optional
import wave
import io
import logging
from scipy import signal
from .exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, config):
        self.config = config
        self.noise_threshold = -30  # dB
        self.vad_enabled = True

    def process_audio(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        try:
            # Normalize audio
            audio_data = self._normalize(audio_data)
            
            # Apply noise reduction
            audio_data = self._reduce_noise(audio_data)
            
            # Voice Activity Detection
            if self.vad_enabled and not self._detect_voice(audio_data):
                return None
            
            return audio_data

        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            raise AudioProcessingError(str(e))

    def _normalize(self, audio_data: np.ndarray) -> np.ndarray:
        return np.float32(audio_data / np.max(np.abs(audio_data)))

    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        # Simple noise gate
        amplitude = np.abs(audio_data)
        mask = amplitude > 10**(self.noise_threshold/20)
        return audio_data * mask

    def _detect_voice(self, audio_data: np.ndarray) -> bool:
        energy = np.sum(audio_data**2) / len(audio_data)
        return energy > 10**(self.noise_threshold/10)

    def to_wav(self, audio_data: np.ndarray) -> bytes:
        with io.BytesIO() as wav_io:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(self.config.CHANNELS)
                wav_file.setsampwidth(4)  # 32-bit float
                wav_file.setframerate(self.config.VOICE_SAMPLE_RATE)
                wav_file.writeframes(audio_data.tobytes())
            return wav_io.getvalue()
