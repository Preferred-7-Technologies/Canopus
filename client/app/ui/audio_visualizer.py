from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.audio_data = np.zeros(128)
        self.peaks = np.zeros(32)
        self.peak_decay = 0.95
        self.color_scheme = {
            'background': QColor(30, 30, 30),
            'bars': QColor(0, 200, 100),
            'peaks': QColor(255, 165, 0)
        }

    def update_data(self, audio_data: np.ndarray):
        try:
            # Compute RMS values for visualization
            chunk_size = len(audio_data) // 32
            self.audio_data = np.array([
                np.sqrt(np.mean(chunk**2))
                for chunk in np.array_split(audio_data, 32)
            ])

            # Update peaks
            self.peaks = np.maximum(self.peaks * self.peak_decay, self.audio_data)
            self.update()
        except Exception as e:
            logger.error(f"Error updating audio visualization: {str(e)}")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Fill background
            painter.fillRect(self.rect(), self.color_scheme['background'])

            # Calculate bar dimensions
            width = self.width()
            height = self.height()
            bar_width = width / len(self.audio_data)
            scale_factor = height * 0.8

            # Draw bars
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.color_scheme['bars'])

            for i, value in enumerate(self.audio_data):
                bar_height = value * scale_factor
                x = i * bar_width
                y = height - bar_height
                painter.drawRect(int(x), int(y), int(bar_width - 1), int(bar_height))

            # Draw peaks
            painter.setPen(QPen(self.color_scheme['peaks'], 2))
            for i, peak in enumerate(self.peaks):
                x = i * bar_width
                y = height - (peak * scale_factor)
                painter.drawLine(
                    int(x), int(y),
                    int(x + bar_width - 1), int(y)
                )

        except Exception as e:
            logger.error(f"Error painting audio visualization: {str(e)}")
