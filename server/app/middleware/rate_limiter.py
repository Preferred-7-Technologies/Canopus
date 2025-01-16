from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.cache import redis_client
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        route = request.url.path
        key = f"rate_limit:{client_ip}:{route}"
        
        # Check rate limit (100 requests per minute)
        requests = redis_client.get(key)
        if requests and int(requests) > 100:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )
        
        # Increment request count
        pipeline = redis_client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, 60)  # Reset after 60 seconds
        pipeline.execute()
        
        return await call_next(request)
