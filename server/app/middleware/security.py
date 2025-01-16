from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Dict, Optional
import time
from ..core.cache import redis_client
from ..core.logging import setup_logging

logger = setup_logging()

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        redis_prefix: str = "ratelimit:",
        rate_limit: int = 100,  # requests per window
        window: int = 600  # 10 minutes
    ):
        super().__init__(app)
        self.redis_prefix = redis_prefix
        self.rate_limit = rate_limit
        self.window = window

    async def dispatch(
        self, request: Request, call_next
    ) -> Response:
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

    async def check_rate_limit(
        self, 
        identifier: str
    ) -> tuple[bool, Optional[Dict]]:
        """Check if request is within rate limits"""
        current = int(time.time())
        key = f"{self.redis_prefix}{identifier}"
        
        pipeline = redis_client.pipeline()
        pipeline.zremrangebyscore(key, 0, current - self.window)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(current): current})
        pipeline.expire(key, self.window)
        results = await pipeline.execute()
        
        request_count = results[1]
        
        if request_count > self.rate_limit:
            return False, {
                "limit": self.rate_limit,
                "remaining": 0,
                "reset": current + self.window
            }
        
        return True, {
            "limit": self.rate_limit,
            "remaining": self.rate_limit - request_count,
            "reset": current + self.window
        }
