from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                           QLineEdit, QPushButton, QCheckBox, QSpinBox,
                           QTabWidget, QWidget, QComboBox)
from ..core.config import ClientConfig
from ..core.secure_storage import SecureStorage
import logging

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    def __init__(self, config: ClientConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.secure_storage = SecureStorage()
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Connection settings
        conn_tab = QWidget()
        conn_layout = QFormLayout(conn_tab)
        
        self.api_url = QLineEdit(self.config.API_URL)
        self.enable_ssl = QCheckBox("Enable SSL Verification")
        self.enable_ssl.setChecked(True)
        
        conn_layout.addRow("API URL:", self.api_url)
        conn_layout.addRow(self.enable_ssl)
        
        # Audio settings
        audio_tab = QWidget()
        audio_layout = QFormLayout(audio_tab)
        
        self.sample_rate = QSpinBox()
        self.sample_rate.setRange(8000, 48000)
        self.sample_rate.setValue(self.config.VOICE_SAMPLE_RATE)
        
        self.input_device = QComboBox()
        self._populate_audio_devices()
        
        audio_layout.addRow("Sample Rate:", self.sample_rate)
        audio_layout.addRow("Input Device:", self.input_device)
        
        # Add tabs
        tabs.addTab(conn_tab, "Connection")
        tabs.addTab(audio_tab, "Audio")
        
        # Buttons
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        layout.addWidget(tabs)
        layout.addWidget(save_button)

    def _populate_audio_devices(self):
        import pyaudio
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                self.input_device.addItem(
                    device_info['name'],
                    device_info['index']
                )
        p.terminate()

    def save_settings(self):
        try:
            # Update config
            self.config.API_URL = self.api_url.text()
            self.config.VOICE_SAMPLE_RATE = self.sample_rate.value()
            
            # Save SSL preference securely
            self.secure_storage.store(
                'ssl_verify',
                str(self.enable_ssl.isChecked())
            )
            
            # Save selected audio device
            device_index = self.input_device.currentData()
            self.secure_storage.store('audio_device', str(device_index))
            
            self.accept()
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
