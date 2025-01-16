"""Canopus Voice Assistant Server"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import settings
from .middleware.request_tracking import RequestTrackingMiddleware
from .core.logging import setup_logging
from .middleware.rate_limiter import RateLimitMiddleware
from .middleware.metrics import PrometheusMiddleware
from fastapi.openapi.utils import get_openapi
from .core.error_tracking import init_error_tracking
from .core.backup import BackupManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .middleware.validation import ValidationMiddleware
from .core.exceptions import http_exception_handler, validation_exception_handler

def create_app() -> FastAPI:
    # Initialize error tracking
    init_error_tracking()

    app = FastAPI(
        title="Canopus API",
        description="Enterprise-grade AI Voice Assistant API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add middleware with proper order
    app.add_middleware(ValidationMiddleware)
    
    # Add request tracking middleware
    app.add_middleware(RequestTrackingMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Add prometheus middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Setup logging
    logger = setup_logging()
    
    from .api.v1.endpoints import auth, voice, websocket, health, metrics
    
    # Version prefix for all routes
    api_prefix = f"{settings.API_V1_STR}"
    
    app.include_router(
        auth.router,
        prefix=f"{api_prefix}/auth",
        tags=["authentication"]
    )
    
    app.include_router(
        voice.router,
        prefix=f"{api_prefix}/voice",
        tags=["voice"]
    )
    
    app.include_router(
        websocket.router,
        prefix=f"{api_prefix}/ws",
        tags=["websocket"]
    )
    
    app.include_router(
        health.router,
        prefix=f"{api_prefix}/system",
        tags=["system"]
    )
    
    app.include_router(
        metrics.router,
        prefix=f"{api_prefix}/metrics",
        tags=["metrics"]
    )
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title="Canopus API",
            version="1.0.0",
            description="Enterprise-grade AI Voice Assistant API with advanced security and monitoring",
            routes=app.routes,
        )
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": f"{settings.API_V1_STR}/auth/token",
                        "scopes": {}
                    }
                }
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Add exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Initialize backup manager and scheduler
    backup_manager = BackupManager()
    scheduler = AsyncIOScheduler()
    
    @app.on_event("startup")
    async def startup_event():
        # Schedule daily backups at 2 AM
        scheduler.add_job(
            backup_manager.create_database_backup,
            'cron',
            hour=2
        )
        scheduler.start()
        logger.info("Application startup complete with scheduled backups")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.shutdown()
        logger.info("Application shutdown complete")
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    return app
