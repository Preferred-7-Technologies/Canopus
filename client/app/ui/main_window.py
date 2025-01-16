from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from ..core.voice_capture import VoiceCapture
from ..core.audio_processor import AudioProcessor
from ..core.database import LocalDatabase
from ..core.api_client import APIClient
import logging
import asyncio
from qtasync import asyncSlot
from .login_dialog import LoginDialog
from ..core.websocket_client import WebSocketClient
from ..core.offline_queue import OfflineQueue
from .settings_dialog import SettingsDialog
from .history_viewer import HistoryViewer
from ..core.user_preferences import UserPreferences
from ..core.hotkeys import HotkeyManager
from ..core.plugin_manager import PluginManager
from ..core.offline_recognition import OfflineRecognizer
from ..core.background_service import BackgroundService
from .audio_visualizer import AudioVisualizer
from ..core.voice_templates import VoiceTemplateManager
from .template_manager import TemplateManagerDialog
from ..core.command_scheduler import CommandScheduler
from .command_playground import CommandPlayground
from ..core.command_macros import MacroManager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.voice_capture = VoiceCapture(config)
        self.audio_processor = AudioProcessor(config)
        self.db = LocalDatabase(config)
        self.api_client = None
        self.ws_client = WebSocketClient(config)
        self.offline_queue = OfflineQueue(self.db)
        self.user_prefs = UserPreferences(config)
        self.hotkey_manager = HotkeyManager()
        self.plugin_manager = PluginManager(config)
        self.offline_recognizer = OfflineRecognizer(config)
        self.background_service = BackgroundService(config)
        self.template_manager = VoiceTemplateManager()
        self.command_scheduler = CommandScheduler(self.db, self._process_scheduled_command)
        self.macro_manager = MacroManager(self._process_command)
        
        self.setWindowTitle("Canopus Voice Assistant")
        self.setMinimumSize(400, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        # Add processing indicator
        self.processing_label = QLabel("")
        layout.addWidget(self.processing_label)
        
        # Add login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.show_login_dialog)
        layout.addWidget(self.login_button)
        
        # Add offline status indicator
        self.offline_indicator = QLabel("Online")
        self.offline_indicator.setStyleSheet("color: green")
        layout.addWidget(self.offline_indicator)
        
        # Add settings button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)
        
        # Add history button
        history_button = QPushButton("Command History")
        history_button.clicked.connect(self.show_history)
        layout.addWidget(history_button)
        
        # Add template manager button
        template_btn = QPushButton("Manage Templates")
        template_btn.clicked.connect(self.show_template_manager)
        layout.addWidget(template_btn)
        
        # Add playground button
        playground_btn = QPushButton("Command Playground")
        playground_btn.clicked.connect(self.show_playground)
        layout.addWidget(playground_btn)
        
        # Add audio visualizer
        self.visualizer = AudioVisualizer()
        layout.addWidget(self.visualizer)
        
        # Initialize recording state
        self.is_recording = False
        
        # Initialize WebSocket
        asyncio.create_task(self.init_websocket())
        
        # Initialize system tray
        self.setup_system_tray()
        
        # Network monitor
        self.network_timer = QTimer()
        self.network_timer.timeout.connect(self.check_network_status)
        self.network_timer.start(30000)  # Check every 30 seconds

        self._apply_preferences()

        # Connect hotkey signals
        self.hotkey_manager.hotkey_triggered.connect(self.handle_hotkey)
        self.hotkey_manager.start_listening()

        # Start background service
        asyncio.create_task(self.background_service.start())
        
        # Register background handlers
        self.background_service.register_handler(
            "offline_processing",
            self._handle_offline_processing
        )
        
        # Add visualization timer
        self.viz_timer = QTimer()
        self.viz_timer.timeout.connect(self.update_visualization)
        self.viz_timer.start(50)  # Update every 50ms

        # Start scheduler
        asyncio.create_task(self.command_scheduler.start())

    def toggle_recording(self):
        if not self.is_recording:
            self.voice_capture.start_recording()
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording...")
        else:
            self.voice_capture.stop_recording()
            self.record_button.setText("Start Recording")
            self.status_label.setText("Ready")
        
        self.is_recording = not self.is_recording

    def update_visualization(self):
        if self.is_recording:
            audio_data = self.voice_capture.get_audio_data()
            if audio_data is not None:
                self.visualizer.update_data(audio_data)

    @asyncSlot()
    async def process_audio(self, audio_data):
        try:
            self.processing_label.setText("Processing...")
            processed_data = self.audio_processor.process_audio(audio_data)
            
            # Try offline recognition first when offline
            if not self.api_client or not self.ws_client.connected.is_set():
                offline_text = await self.offline_recognizer.recognize(processed_data)
                if offline_text:
                    await self.background_service.process_task(
                        "offline_processing",
                        {"text": offline_text, "audio_data": processed_data.tolist()}
                    )
                    self.status_label.setText(f"Offline: {offline_text}")
                    return
            
            if not self.api_client or not self.ws_client.connected.is_set():
                await self.offline_queue.enqueue({
                    "audio_data": processed_data.tolist(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.status_label.setText("Command queued for offline processing")
                return
            
            if processed_data is not None and self.api_client:
                wav_data = self.audio_processor.to_wav(processed_data)
                response = await self.api_client._make_request(
                    'POST',
                    'voice/process',
                    data=wav_data,
                    headers={'Content-Type': 'audio/wav'}
                )
                
                # Store in local database
                with self.db.get_session() as session:
                    session.add(VoiceCommand(
                        command_text=response.get('text', ''),
                        status='completed',
                        command_metadata=response  # Updated from metadata to command_metadata
                    ))
                
                self.status_label.setText(response.get('text', 'Processed'))
                
                # Process through plugins
                plugin_result = self.plugin_manager.process_command(
                    response.get('text', '')
                )
                if plugin_result:
                    self.status_label.setText(plugin_result)
                
                # Process through templates
                template_match = await self.template_manager.match_command(
                    response.get('text', '')
                )
                
                if template_match:
                    template, variables, confidence = template_match
                    logger.info(f"Matched template {template.name} with confidence {confidence}")
                    # Process template-specific logic here
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            self.status_label.setText("Error processing audio")
        finally:
            self.processing_label.setText("")

    async def init_websocket(self):
        self.ws_client.register_handler("command_response", self.handle_ws_response)
        await self.ws_client.connect()

    async def handle_ws_response(self, data):
        self.status_label.setText(data.get("response", "Received response"))

    def show_login_dialog(self):
        dialog = LoginDialog(self.config, self)
        dialog.login_successful.connect(self.handle_login_success)
        dialog.exec_()

    def handle_login_success(self, credentials):
        self.api_client = APIClient(self.config)
        self.api_client.token = credentials["token"]
        self.login_button.setEnabled(False)
        self.status_label.setText(f"Logged in as {credentials['username']}")
        
        # Process offline queue
        asyncio.create_task(self.process_offline_queue())

    async def process_offline_queue(self):
        try:
            results = await self.offline_queue.process_queue(self.api_client)
            if results:
                self.status_label.setText(f"Processed {len(results)} offline commands")
        except Exception as e:
            logger.error(f"Failed to process offline queue: {str(e)}")

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("resources/icon.png"))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            self.apply_settings()

    def apply_settings(self):
        # Restart components with new settings
        if self.is_recording:
            self.toggle_recording()
        
        self.voice_capture = VoiceCapture(self.config)
        self.ws_client = WebSocketClient(self.config)
        asyncio.create_task(self.init_websocket())

    async def check_network_status(self):
        try:
            async with self.api_client._make_request('GET', 'health') as response:
                online = response.status == 200
        except:
            online = False
            
        self.offline_indicator.setText("Online" if online else "Offline")
        self.offline_indicator.setStyleSheet(
            "color: green" if online else "color: red"
        )

    def quit_application(self):
        if self.is_recording:
            self.voice_capture.stop_recording()
        QApplication.quit()

    def closeEvent(self, event):
        if (self.tray_icon.isVisible() and 
            self.user_prefs.get("minimize_to_tray", True)):
            self.hide()
            event.ignore()
        else:
            if self.is_recording:
                self.voice_capture.stop_recording()
            self.hotkey_manager.stop_listening()
            self.plugin_manager.cleanup()
            asyncio.create_task(self.background_service.stop())
            self.viz_timer.stop()
            asyncio.create_task(self.command_scheduler.stop())
            event.accept()

    def _apply_preferences(self):
        # Apply theme
        if self.user_prefs.get("theme") == "dark":
            self.setStyleSheet(self._get_dark_theme())
        
        # Apply accessibility settings
        font = self.font()
        if self.user_prefs.get("accessibility.large_text"):
            font.setPointSize(font.pointSize() * 1.5)
        self.setFont(font)
        
        # Apply audio settings
        if hasattr(self, "audio_processor"):
            self.audio_processor.noise_reduction = self.user_prefs.get(
                "audio.noise_reduction", True
            )
            self.audio_processor.vad_enabled = self.user_prefs.get(
                "audio.voice_activity_detection", True
            )

    def show_history(self):
        dialog = HistoryViewer(self.db, self)
        dialog.command_selected.connect(self._handle_history_command)
        dialog.exec_()

    def _handle_history_command(self, command_data: dict):
        # Handle replaying or viewing detailed command information
        self.status_label.setText(f"Selected command: {command_data.get('command_text', '')}")

    def _get_dark_theme(self) -> str:
        return """
            QMainWindow, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #505050;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QLabel {
                color: #ffffff;
            }
        """

    def handle_hotkey(self, action: str):
        try:
            if action == "toggle_recording":
                self.toggle_recording()
            elif action == "show_settings":
                self.show_settings()
            elif action == "show_history":
                self.show_history()
        except Exception as e:
            logger.error(f"Failed to handle hotkey action {action}: {str(e)}")

    async def _handle_offline_processing(self, data: dict):
        try:
            # Store in local database
            with self.db.get_session() as session:
                session.add(VoiceCommand(
                    command_text=data["text"],
                    status="pending",
                    command_metadata={"offline": True}  # Updated from metadata to command_metadata
                ))
            
            # Process through plugins
            plugin_result = self.plugin_manager.process_command(data["text"])
            if plugin_result:
                return {"status": "success", "result": plugin_result}
            
            return {"status": "queued"}
            
        except Exception as e:
            logger.error(f"Offline processing failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def show_template_manager(self):
        dialog = TemplateManagerDialog(self.template_manager, self)
        dialog.exec_()

    async def _process_scheduled_command(self, command: str, metadata: dict):
        try:
            # Process through templates
            template_match = await self.template_manager.match_command(command)
            if template_match:
                template, variables, confidence = template_match
                # Process template-specific logic
            
            # Process through plugins
            plugin_result = self.plugin_manager.process_command(command)
            if plugin_result:
                logger.info(f"Scheduled command processed: {plugin_result}")
                
        except Exception as e:
            logger.error(f"Failed to process scheduled command: {str(e)}")

    def show_playground(self):
        playground = CommandPlayground(self.macro_manager, self)
        playground.execute_command.connect(self._handle_playground_command)
        playground.save_macro.connect(self._save_playground_macro)
        playground.exec_()

    async def _handle_playground_command(self, command_data: str):
        try:
            data = json.loads(command_data)
            if data["type"] == "macro":
                result = await self.macro_manager.execute_macro(
                    data["command"]
                )
            else:
                result = await self._process_command(data["command"])
            
            self.playground.add_result({
                "type": data["type"],
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Playground command failed: {str(e)}")

    async def _process_command(self, command: str) -> dict:
        # Process command through available processors
        try:
            template_match = await self.template_manager.match_command(command)
            if template_match:
                return {"type": "template", "result": template_match}
            
            plugin_result = self.plugin_manager.process_command(command)
            if plugin_result:
                return {"type": "plugin", "result": plugin_result}
            
            return {"type": "unknown", "result": "No processor handled the command"}
            
        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            return {"type": "error", "result": str(e)}

    def _save_playground_macro(self, macro_data: dict):
        try:
            self.macro_manager.save_macro(CommandMacro(**macro_data))
        except Exception as e:
            logger.error(f"Failed to save playground macro: {str(e)}")
