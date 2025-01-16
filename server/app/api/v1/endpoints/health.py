from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.cache import redis_client
from ....core.celery_app import celery_app
from ....core.metrics import http_requests_total
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check system health status"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    # Check Redis connection
    try:
        await redis_client._redis.ping()
        cache_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        cache_status = "unhealthy"

    status = "healthy" if all([
        db_status == "healthy",
        cache_status == "healthy"
    ]) else "degraded"

    http_requests_total.labels(
        method="GET",
        endpoint="/health",
        status=200 if status == "healthy" else 503
    ).inc()

    return {
        "status": status,
        "services": {
            "database": db_status,
            "cache": cache_status
        }
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    health_status = {
        "database": "healthy",
        "redis": "healthy",
        "celery": "healthy"
    }
    
    try:
        # Check database
        db.execute("SELECT 1")
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis
        redis_client.ping()
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Celery
        celery_app.control.ping()
    except Exception as e:
        health_status["celery"] = f"unhealthy: {str(e)}"
    
    return health_status

@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"status": "ok"}
