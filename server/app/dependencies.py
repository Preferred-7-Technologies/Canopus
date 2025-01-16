from typing import Generator, AsyncGenerator
from fastapi import Depends, HTTPException, status
from .database import SessionLocal
from .core.cache import redis_client
from .core.ai.azure_client import AzureAIClient
from .services.voice import VoiceService
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[Session, None]:
    """Dependency for database sessions"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_voice_service() -> AsyncGenerator[VoiceService, None]:
    """Dependency for voice service"""
    service = VoiceService()
    try:
        yield service
    finally:
        await service.cleanup()

async def get_ai_client() -> AsyncGenerator[AzureAIClient, None]:
    """Dependency for AI client"""
    client = AzureAIClient()
    try:
        yield client
    finally:
        await client.close()

async def get_cache() -> AsyncGenerator[redis_client, None]:
    """Dependency for cache client"""
    try:
        yield redis_client
    finally:
        pass  # Redis cleanup is handled at application shutdown
