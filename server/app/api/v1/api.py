from fastapi import APIRouter
from .endpoints import voice, auth, health, metrics, websocket
from fastapi.openapi.utils import get_openapi
from ...config import settings

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
# WebSocket routes are included directly in main.py

def custom_openapi():
    if api_router.openapi_schema:
        return api_router.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="""
        Canopus Voice Assistant API
        
        An enterprise-grade voice assistant system with the following features:
        * Voice Processing
        * Text-to-Speech
        * Real-time WebSocket Communication
        * Task Management
        * Authentication & Authorization
        """,
        routes=api_router.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Add security requirement to all endpoints
    openapi_schema["security"] = [{"bearerAuth": []}]

    api_router.openapi_schema = openapi_schema
    return api_router.openapi_schema

api_router.openapi = custom_openapi
