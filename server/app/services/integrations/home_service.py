from typing import Dict, Any, Optional
import asyncio
from ...config import settings
from ...core.logging import setup_logging
import aiohttp

logger = setup_logging()

class HomeAutomationService:
    def __init__(self):
        self.hass_url = settings.HOME_ASSISTANT_URL
        self.hass_token = settings.HOME_ASSISTANT_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.hass_token}",
            "Content-Type": "application/json",
        }

    async def control_device(
        self, 
        device_type: str,
        action: str,
        device_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            if action == "status":
                return await self._get_device_status(device_type, device_id)
            
            service_data = {
                "entity_id": device_id or f"{device_type}.{device_id}"
            }
            if parameters:
                service_data.update(parameters)

            service = self._get_service_call(device_type, action)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.hass_url}/api/services/{service}"
                async with session.post(
                    url,
                    headers=self.headers,
                    json=service_data
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Home Assistant API error: {response.status}")
                    
                    return {
                        "status": "success",
                        "device_type": device_type,
                        "action": action,
                        "device_id": device_id
                    }

        except Exception as e:
            logger.error(f"Home automation failed: {str(e)}")
            raise

    def _get_service_call(self, device_type: str, action: str) -> str:
        service_calls = {
            "light": {
                "on": "light/turn_on",
                "off": "light/turn_off",
                "adjust": "light/turn_on"  # with brightness/color
            },
            "thermostat": {
                "on": "climate/turn_on",
                "off": "climate/turn_off",
                "adjust": "climate/set_temperature"
            },
            "security": {
                "on": "alarm_control_panel/arm_away",
                "off": "alarm_control_panel/disarm"
            },
            "camera": {
                "on": "camera/turn_on",
                "off": "camera/turn_off"
            },
            "speaker": {
                "on": "media_player/turn_on",
                "off": "media_player/turn_off",
                "adjust": "media_player/volume_set"
            }
        }
        return service_calls.get(device_type, {}).get(action, "")

    async def _get_device_status(
        self, 
        device_type: str, 
        device_id: str
    ) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            url = f"{self.hass_url}/api/states/{device_type}.{device_id}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get device status: {response.status}")
                data = await response.json()
                return {
                    "status": "success",
                    "device_type": device_type,
                    "device_id": device_id,
                    "state": data["state"],
                    "attributes": data["attributes"]
                }
