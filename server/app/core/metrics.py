from prometheus_client import Counter, Histogram, Gauge
import time
import logging
from typing import Callable
from functools import wraps

logger = logging.getLogger(__name__)

# Metrics definitions
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

voice_processing_duration_seconds = Histogram(
    'voice_processing_duration_seconds',
    'Voice processing duration in seconds',
    ['status']
)

active_websocket_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections'
)

def track_time(metric: Histogram) -> Callable:
    """Decorator to track execution time of a function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metric.labels(status='error').observe(duration)
                raise
        return wrapper
    return decorator
