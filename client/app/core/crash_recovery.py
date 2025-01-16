import sys
from pathlib import Path
import json
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class CrashRecoverySystem(QObject):
    recovery_available = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.crash_dir = Path("data/crashes")
        self.crash_dir.mkdir(exist_ok=True)
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._install_exception_hook()

    def _install_exception_hook(self):
        self._original_hook = sys.excepthook
        sys.excepthook = self._handle_exception

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        try:
            # Save crash information
            crash_data = {
                "timestamp": datetime.now().isoformat(),
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_tb(exc_traceback),
                "session_id": self.current_session
            }
            
            crash_file = self.crash_dir / f"crash_{self.current_session}.json"
            with open(crash_file, "w") as f:
                json.dump(crash_data, f, indent=2)
                
            logger.critical(f"Application crashed: {str(exc_value)}")
            
        finally:
            # Call original exception hook
            self._original_hook(exc_type, exc_value, exc_traceback)

    def save_state(self, state: Dict[str, Any]):
        """Save current application state"""
        try:
            state_file = self.crash_dir / f"state_{self.current_session}.json"
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save application state: {str(e)}")

    def check_recovery(self) -> Optional[Dict[str, Any]]:
        """Check for recoverable state from previous crash"""
        try:
            crashes = sorted(self.crash_dir.glob("crash_*.json"))
            if not crashes:
                return None

            latest_crash = crashes[-1]
            state_file = self.crash_dir / f"state_{latest_crash.stem[6:]}.json"
            
            if not state_file.exists():
                return None

            with open(state_file, "r") as f:
                state = json.load(f)
                self.recovery_available.emit(state)
                return state

        except Exception as e:
            logger.error(f"Failed to check recovery state: {str(e)}")
            return None

    def cleanup_old_crashes(self, max_age_days: int = 30):
        """Clean up old crash reports"""
        try:
            cutoff = datetime.now().timestamp() - (max_age_days * 86400)
            for file in self.crash_dir.glob("*.*"):
                if file.stat().st_mtime < cutoff:
                    file.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup old crashes: {str(e)}")
