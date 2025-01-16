from typing import Dict, Any, Optional
import aiohttp
import logging
from ...config import settings
from ..cache import redis_client
import json
import time

logger = logging.getLogger(__name__)

class AzureAIClient:
    def __init__(self):
        self.endpoint = settings.AZURE_ENDPOINT
        self.api_key = settings.AZURE_API_KEY
        self.default_model = settings.AZURE_DEFAULT_MODEL
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self._session

    async def process_request(
        self,
        request_data: Dict[str, Any],
        request_type: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process request through Azure AI"""
        start_time = time.time()
        cache_key = f"ai_request:{hash(json.dumps(request_data))}"

        try:
            # Check cache
            cached = await redis_client.get(cache_key)
            if cached:
                return cached

            session = await self._get_session()
            async with session.post(
                f"{self.endpoint}/completions",
                json={
                    "model": model or self.default_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt(request_type)
                        },
                        {
                            "role": "user",
                            "content": json.dumps(request_data)
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()

                processed_result = {
                    "response": result["choices"][0]["message"]["content"],
                    "model_used": model or self.default_model,
                    "processing_time": time.time() - start_time,
                    "confidence": result.get("choices", [{}])[0].get("confidence", 0.0)
                }

                # Cache successful responses
                if processed_result["confidence"] > 0.7:
                    await redis_client.set(cache_key, processed_result, expire=3600)

                return processed_result

        except Exception as e:
            logger.error(f"Azure AI request failed: {str(e)}")
            raise

    def _get_system_prompt(self, request_type: str) -> str:
        """Get system prompt based on request type"""
        prompts = {
            "command_processing": """
            You are an AI assistant processing voice commands. 
            Analyze the command and extract actions and parameters.
            Return structured responses with high confidence scores only.
            """,
            "voice_analysis": """
            You are an AI assistant analyzing voice characteristics.
            Focus on clarity, emotion, and intent recognition.
            Provide detailed analysis with confidence scores.
            """
        }
        return prompts.get(request_type, prompts["command_processing"])

    async def close(self):
        """Close the client session"""
        if self._session:
            await self._session.close()
            self._session = None
