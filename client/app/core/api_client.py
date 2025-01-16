import aiohttp
import asyncio
from typing import Optional, Dict, Any
import jwt
import time
from datetime import datetime
import logging
from .exceptions import APIError, AuthenticationError

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, config):
        self.config = config
        self.base_url = f"{config.API_URL}/api/{config.API_VERSION}"
        self.token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._retry_count = 3
        self._backoff_factor = 0.5

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": f"Canopus-Client/{self.config.CLIENT_ID}"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        try:
            async with self.session.post(
                f"{self.base_url}/auth/login",
                json=credentials
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data["access_token"]
                    return True
                raise AuthenticationError("Authentication failed")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError(str(e))

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        for attempt in range(self._retry_count):
            try:
                headers = kwargs.get('headers', {})
                if self.token:
                    headers['Authorization'] = f"Bearer {self.token}"
                kwargs['headers'] = headers

                async with self.session.request(
                    method,
                    f"{self.base_url}/{endpoint}",
                    **kwargs
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Token expired or invalid")
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                if attempt == self._retry_count - 1:
                    raise APIError(f"API request failed: {str(e)}")
                await asyncio.sleep(self._backoff_factor * (2 ** attempt))
