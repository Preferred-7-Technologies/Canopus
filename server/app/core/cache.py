from redis.asyncio import Redis
from typing import Optional, Any
import pickle
from ..config import settings
from ..core.logging import setup_logging
import json

logger = setup_logging()

class RedisClient:
    def __init__(self):
        self._redis: Optional[Redis] = None

    async def init(self):
        if not self._redis:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self._redis.get(key)
            return pickle.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get operation failed: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        try:
            serialized = pickle.dumps(value)
            return await self._redis.set(key, serialized, ex=expire)
        except Exception as e:
            logger.error(f"Redis set operation failed: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            return bool(await self._redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete operation failed: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        if not self._redis:
            return False
        return await self._redis.exists(key) > 0

redis_client = RedisClient()

# For backward compatibility
cache = redis_client

def cache_response(expire_time=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set(
                cache_key,
                result,
                expire=expire_time
            )
            return result
        return wrapper
    return decorator
