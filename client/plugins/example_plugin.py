from app.core.plugin_manager import PluginBase
import logging

logger = logging.getLogger(__name__)

class WeatherPlugin(PluginBase):
    def initialize(self, config) -> bool:
        self.config = config
        return True

    def process_command(self, command: str) -> str:
        if "weather" in command.lower():
            return "Weather functionality will be implemented here"
        return None

    def cleanup(self):
        pass
