from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from ..core.logging import setup_logging

logger = setup_logging()

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        logger.info(f"Request {request_id} started: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(f"Request {request_id} completed in {process_time:.2f}s")
            return response
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise
