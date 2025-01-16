import pyaudio
import wave
import numpy as np
from threading import Thread, Event
from queue import Queue
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceCapture:
    def __init__(self, config):
        self.config = config
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.recording = Event()
        self.audio_queue = Queue()
        self._recording_thread: Optional[Thread] = None

    def start_recording(self):
        if self.recording.is_set():
            return

        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.config.CHANNELS,
            rate=self.config.VOICE_SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.config.CHUNK_SIZE
        )

        self.recording.set()
        self._recording_thread = Thread(target=self._record_audio)
        self._recording_thread.start()
        logger.info("Started voice recording")

    def stop_recording(self):
        self.recording.clear()
        if self._recording_thread:
            self._recording_thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        logger.info("Stopped voice recording")

    def _record_audio(self):
        while self.recording.is_set():
            try:
                data = np.frombuffer(
                    self.stream.read(self.config.CHUNK_SIZE),
                    dtype=np.float32
                )
                self.audio_queue.put(data)
            except Exception as e:
                logger.error(f"Error recording audio: {str(e)}")
                break

    def get_audio_data(self):
        return self.audio_queue.get() if not self.audio_queue.empty() else None

    def __del__(self):
        if self.stream:
            self.stream.close()
        self.audio.terminate()
