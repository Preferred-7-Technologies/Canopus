from redis.asyncio import Redis
from typing import Optional, Any, Union
import pickle
import json
import logging
from ...config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._prefix = "Canopus:"

    async def init(self):
        """Initialize Redis connection"""
        try:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
            await self._redis.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Redis initialization failed: {str(e)}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            data = await self._redis.get(f"{self._prefix}{key}")
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
        nx: bool = False
    ) -> bool:
        """Set value in cache"""
        try:
            serialized = pickle.dumps(value)
            return await self._redis.set(
                f"{self._prefix}{key}",
                serialized,
                ex=expire,
                nx=nx
            )
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(await self._redis.delete(f"{self._prefix}{key}"))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

redis_client = RedisCache()
