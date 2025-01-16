from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.api import api_router
from .api.v1.endpoints import websocket
from .middleware.logging import RequestLoggingMiddleware
from .config import settings
from prometheus_client import make_asgi_app
import sentry_sdk
from .core.performance import configure_performance
from .core.cache import redis_client
from .core.logging import setup_logging
from contextlib import asynccontextmanager

logger = setup_logging()

# Initialize Sentry if configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        enable_tracing=True,
    )
    logger.info("Sentry initialized successfully")

# Configure performance optimizations
configure_performance()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.init()
    logger.info("Application startup complete")
    yield
    # Shutdown
    await redis_client.close()
    logger.info("Application shutdown complete")

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Canopus Enterprise Voice Assistant API",
        lifespan=lifespan
    )

    # Add middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(
        websocket.router,
        prefix=settings.API_V1_STR,
        tags=["websocket"]
    )

    return app