from PyQt5.QtCore import QObject, pyqtSignal
from pynput import keyboard
import json
from pathlib import Path
import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)

class HotkeyManager(QObject):
    hotkey_triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hotkeys: Dict[str, keyboard.HotKey] = {}
        self.hotkey_mappings = {}
        self.listener = None
        self._load_hotkeys()

    def _load_hotkeys(self):
        try:
            hotkeys_file = Path("data/hotkeys.json")
            if (hotkeys_file.exists()):
                with open(hotkeys_file, "r") as f:
                    self.hotkey_mappings = json.load(f)
                    
            for action, keys in self.hotkey_mappings.items():
                self.register_hotkey(keys, action)
        except Exception as e:
            logger.error(f"Failed to load hotkeys: {str(e)}")

    def register_hotkey(self, keys: str, action: str):
        try:
            hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(keys),
                lambda: self.hotkey_triggered.emit(action)
            )
            self.hotkeys[action] = hotkey
            logger.info(f"Registered hotkey {keys} for action {action}")
        except Exception as e:
            logger.error(f"Failed to register hotkey {keys}: {str(e)}")

    def start_listening(self):
        def on_press(key):
            for hotkey in self.hotkeys.values():
                hotkey.press(key)

        def on_release(key):
            for hotkey in self.hotkeys.values():
                hotkey.release(key)
            return True

        self.listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.listener.start()
        logger.info("Hotkey listener started")

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            logger.info("Hotkey listener stopped")
