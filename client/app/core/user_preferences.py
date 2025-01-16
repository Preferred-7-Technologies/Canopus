from pathlib import Path
import json
import logging
from typing import Any, Dict, Optional
from .secure_storage import SecureStorage

logger = logging.getLogger(__name__)

class UserPreferences:
    def __init__(self, config):
        self.config = config
        self.secure_storage = SecureStorage()
        self.prefs_file = Path("data/user_preferences.json")
        self._prefs: Dict[str, Any] = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        try:
            if self.prefs_file.exists():
                with open(self.prefs_file, 'r') as f:
                    return json.load(f)
            return self._get_default_preferences()
        except Exception as e:
            logger.error(f"Failed to load preferences: {str(e)}")
            return self._get_default_preferences()

    def _get_default_preferences(self) -> Dict[str, Any]:
        return {
            "theme": "light",
            "notifications_enabled": True,
            "auto_start": False,
            "minimize_to_tray": True,
            "voice_command_confirmation": True,
            "custom_wake_word": "",
            "language": "en-US",
            "audio": {
                "noise_reduction": True,
                "voice_activity_detection": True,
                "auto_gain_control": True
            },
            "accessibility": {
                "high_contrast": False,
                "large_text": False
            }
        }

    def save(self) -> bool:
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(self._prefs, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save preferences: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        try:
            keys = key.split('.')
            value = self._prefs
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        try:
            keys = key.split('.')
            target = self._prefs
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            target[keys[-1]] = value
            return self.save()
        except Exception as e:
            logger.error(f"Failed to set preference {key}: {str(e)}")
            return False
