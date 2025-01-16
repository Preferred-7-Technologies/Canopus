from typing import Dict, Any, Optional
import logging
from ...models import User, Template
from ..ai.azure_client import AzureAIClient
from ..cache import redis_client
from sqlalchemy.orm import Session
from ...database import get_db
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self):
        self.ai_client = AzureAIClient()
        self.db = next(get_db())

    async def process_command(
        self,
        text: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a command through the AI pipeline"""
        try:
            # Check command cache
            cache_key = f"command:{user_id}:{hash(text)}"
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return cached_result

            # Get user context
            user_context = await self._get_user_context(user_id)
            
            # Prepare AI request
            request_data = {
                "text": text,
                "context": {
                    **(context or {}),
                    **user_context
                }
            }

            # Get AI response
            response = await self.ai_client.process_request(
                request_data,
                "command_processing"
            )

            # Extract actions and parameters
            actions = self._extract_actions(response)
            
            result = {
                "processed_text": response.get("processed_text", text),
                "confidence": response.get("confidence", 0.0),
                "actions": actions,
                "response": response.get("response"),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": response.get("model_used"),
                    "processing_time": response.get("processing_time")
                }
            }

            # Cache successful results
            if response.get("confidence", 0.0) > 0.7:
                await redis_client.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            raise

    async def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user-specific context for command processing"""
        try:
            # Get user preferences and settings
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}

            return {
                "voice_preference": user.voice_preference.id if user.voice_preference else None,
                "language": user.language if hasattr(user, 'language') else "en-US",
                "timezone": user.timezone if hasattr(user, 'timezone') else "UTC",
            }

        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            return {}

    def _extract_actions(self, response: Dict[str, Any]) -> list:
        """Extract actionable items from AI response"""
        actions = []
        try:
            if "actions" in response:
                for action in response["actions"]:
                    if self._validate_action(action):
                        actions.append(action)
        except Exception as e:
            logger.error(f"Action extraction failed: {str(e)}")
        return actions

    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate if an action is properly formatted and allowed"""
        required_fields = {"type", "parameters"}
        allowed_types = {"system_command", "api_call", "template_execution"}
        
        return (
            all(field in action for field in required_fields) and
            action.get("type") in allowed_types
        )
