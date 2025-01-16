import numpy as np
from scipy.io import wavfile
import io
import logging
from typing import Optional
from ...config import settings

logger = logging.getLogger(__name__)

class AudioEncoder:
    def __init__(self):
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.max_length = settings.MAX_AUDIO_LENGTH * self.sample_rate

    def encode(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array for model processing"""
        try:
            # Read WAV data
            with io.BytesIO(audio_data) as buf:
                sample_rate, audio_array = wavfile.read(buf)
            
            # Convert to mono if stereo
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                audio_array = self._resample(audio_array, sample_rate)
            
            # Normalize
            audio_array = self._normalize(audio_array)
            
            # Trim to max length
            if len(audio_array) > self.max_length:
                audio_array = audio_array[:self.max_length]
            
            return audio_array

        except Exception as e:
            logger.error(f"Audio encoding failed: {str(e)}")
            raise

    def _normalize(self, audio_array: np.ndarray) -> np.ndarray:
        """Normalize audio array to [-1, 1] range"""
        return np.float32(audio_array) / np.max(np.abs(audio_array))

    def _resample(self, audio_array: np.ndarray, original_rate: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        try:
            from scipy import signal
            duration = len(audio_array) / original_rate
            time_old = np.linspace(0, duration, len(audio_array))
            time_new = np.linspace(0, duration, int(len(audio_array) * self.sample_rate / original_rate))
            return np.interp(time_new, time_old, audio_array)
        except Exception as e:
            logger.error(f"Resampling failed: {str(e)}")
            raise
