import importlib.util
import inspect
from pathlib import Path
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class PluginBase(ABC):
    @abstractmethod
    def initialize(self, config: Any) -> bool:
        pass

    @abstractmethod
    def process_command(self, command: str) -> Optional[str]:
        pass

    @abstractmethod
    def cleanup(self):
        pass

class PluginManager:
    def __init__(self, config):
        self.config = config
        self.plugins: Dict[str, PluginBase] = {}
        self._load_plugins()

    def _load_plugins(self):
        try:
            plugins_dir = Path("plugins")
            if not plugins_dir.exists():
                plugins_dir.mkdir()
                return

            for plugin_file in plugins_dir.glob("*.py"):
                try:
                    if plugin_file.name.startswith("__"):
                        continue

                    spec = importlib.util.spec_from_file_location(
                        plugin_file.stem,
                        plugin_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        for item_name, item in inspect.getmembers(module):
                            if (inspect.isclass(item) and 
                                issubclass(item, PluginBase) and 
                                item != PluginBase):
                                plugin = item()
                                if plugin.initialize(self.config):
                                    self.plugins[plugin_file.stem] = plugin
                                    logger.info(f"Loaded plugin: {plugin_file.stem}")

                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to load plugins: {str(e)}")

    def process_command(self, command: str) -> Optional[str]:
        results = []
        for plugin_name, plugin in self.plugins.items():
            try:
                result = plugin.process_command(command)
                if result:
                    results.append(f"[{plugin_name}] {result}")
            except Exception as e:
                logger.error(f"Plugin {plugin_name} failed: {str(e)}")
        
        return "\n".join(results) if results else None

    def cleanup(self):
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup plugin {plugin_name}: {str(e)}")
