
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable, Any
from ..core.logging import setup_logging
import elasticapm
from elasticapm.contrib.starlette import ElasticAPM

logger = setup_logging()

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration_seconds = Histogram(
    'request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_tasks = Gauge(
    'active_tasks',
    'Number of active tasks',
    ['task_type']
)

def monitor_task(task_type: str) -> Callable:
    """Decorator to monitor async tasks"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            active_tasks.labels(task_type=task_type).inc()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                request_duration_seconds.labels(
                    method='task',
                    endpoint=task_type
                ).observe(duration)
                
                return result
            
            except Exception as e:
                logger.error(f"Task failed: {str(e)}")
                elasticapm.capture_exception()
                raise
            
            finally:
                active_tasks.labels(task_type=task_type).dec()
                
        return wrapper
    return decorator