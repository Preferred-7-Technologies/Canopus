import zipfile
import json
from pathlib import Path
import logging
from datetime import datetime
import shutil
from typing import List, Dict, Any
import hashlib

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, config):
        self.config = config
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)

    def export_data(self, categories: List[str] = None) -> Path:
        """Export selected categories of application data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Export configuration
                if not categories or 'config' in categories:
                    self._export_config(zf)
                
                # Export templates
                if not categories or 'templates' in categories:
                    self._export_templates(zf)
                
                # Export macros
                if not categories or 'macros' in categories:
                    self._export_macros(zf)
                
                # Export command history
                if not categories or 'history' in categories:
                    self._export_history(zf)
                
                # Export preferences
                if not categories or 'preferences' in categories:
                    self._export_preferences(zf)
                
                # Add manifest
                manifest = {
                    "timestamp": timestamp,
                    "categories": categories or "all",
                    "version": "1.0"
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Data export failed: {str(e)}")
            raise

    def import_data(self, backup_file: Path, categories: List[str] = None) -> bool:
        """Import data from backup file"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zf:
                # Verify manifest
                if not self._verify_backup(zf):
                    raise ValueError("Invalid backup file")
                
                # Create temporary directory
                temp_dir = Path("data/temp_import")
                temp_dir.mkdir(exist_ok=True)
                
                try:
                    # Extract files
                    zf.extractall(temp_dir)
                    
                    # Import each category
                    if not categories or 'config' in categories:
                        self._import_config(temp_dir)
                    
                    if not categories or 'templates' in categories:
                        self._import_templates(temp_dir)
                    
                    if not categories or 'macros' in categories:
                        self._import_macros(temp_dir)
                    
                    if not categories or 'history' in categories:
                        self._import_history(temp_dir)
                    
                    if not categories or 'preferences' in categories:
                        self._import_preferences(temp_dir)
                    
                    return True
                    
                finally:
                    # Cleanup
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.error(f"Data import failed: {str(e)}")
            return False

    def _verify_backup(self, zf: zipfile.ZipFile) -> bool:
        try:
            manifest = json.loads(zf.read("manifest.json"))
            return manifest["version"] == "1.0"
        except Exception:
            return False

    def _export_config(self, zf: zipfile.ZipFile):
        config_file = Path("data/device_config.json")
        if config_file.exists():
            zf.write(config_file, "config/device_config.json")

    def _export_templates(self, zf: zipfile.ZipFile):
        template_dir = Path("data/templates")
        if template_dir.exists():
            for template_file in template_dir.glob("*.json"):
                zf.write(template_file, f"templates/{template_file.name}")

    def _export_macros(self, zf: zipfile.ZipFile):
        macro_dir = Path("data/macros")
        if macro_dir.exists():
            for macro_file in macro_dir.glob("*.json"):
                zf.write(macro_file, f"macros/{macro_file.name}")

    def _export_history(self, zf: zipfile.ZipFile):
        history_file = Path(self.config.LOCAL_DB_PATH)
        if history_file.exists():
            zf.write(history_file, "history/local.db")

    def _export_preferences(self, zf: zipfile.ZipFile):
        prefs_file = Path("data/user_preferences.json")
        if prefs_file.exists():
            zf.write(prefs_file, "preferences/user_preferences.json")

    # Similar _import_* methods for each category...
