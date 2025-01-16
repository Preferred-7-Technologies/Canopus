import aiohttp
from typing import Dict, Any, Optional
from ...config import settings
from ...core.logging import setup_logging

logger = setup_logging()

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def get_weather(
        self, 
        location: str, 
        forecast_type: str = "current"
    ) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                if forecast_type == "current":
                    url = f"{self.base_url}/weather"
                elif forecast_type == "hourly":
                    url = f"{self.base_url}/forecast"
                else:
                    url = f"{self.base_url}/forecast/daily"

                params = {
                    "q": location,
                    "appid": self.api_key,
                    "units": "metric"
                }

                async with session.get(url, params=params) as response:
                    data = await response.json()
                    if response.status != 200:
                        raise Exception(f"Weather API error: {data.get('message')}")
                    
                    return self._format_weather_data(data, forecast_type)

        except Exception as e:
            logger.error(f"Weather service failed: {str(e)}")
            raise

    def _format_weather_data(
        self, 
        data: Dict[str, Any], 
        forecast_type: str
    ) -> Dict[str, Any]:
        if forecast_type == "current":
            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"]
            }
        # Add formatting for other forecast types
        return data
