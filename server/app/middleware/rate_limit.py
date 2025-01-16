from fastapi import Request, HTTPException
from typing import Dict, Tuple
import time
import logging
from ..core.cache import redis_client
from ..config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        current_time = int(time.time())
        
        # Generate cache key
        key = f"rate_limit:{client_ip}:{current_time // 60}"
        
        try:
            # Increment request count
            count = await redis_client.incr(key)
            
            # Set expiry if first request
            if count == 1:
                await redis_client.expire(key, 60)
            
            # Check limits
            if count > self.burst_limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            
            if count > self.requests_per_minute:
                retry_after = 60 - (current_time % 60)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Rate limit exceeded",
                        "retry_after": retry_after
                    }
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Allow request on error to prevent blocking users
            return True

rate_limiter = RateLimiter()
