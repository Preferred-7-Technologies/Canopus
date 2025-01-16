
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.logging import setup_logging
import time
from typing import Callable
import json

logger = setup_logging()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host,
                "headers": dict(request.headers)
            }
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        return response