import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
import fakeredis.aioredis
from unittest.mock import Mock, patch
from ..core.cache import redis_client
from ..database import Base, get_db
from ..services.tts_service import TTSService

# Add the parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Test database using SQLite in-memory
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test database engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
async def setup_database():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_app(mock_tts_service):
    from ..main import app
    app.dependency_overrides[get_db] = lambda: next(TestingSessionLocal())
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

# Mock Redis
@pytest.fixture(autouse=True)
async def mock_redis():
    """Replace Redis with fakeredis for testing"""
    mock_redis = fakeredis.aioredis.FakeRedis()
    original_redis = redis_client._redis
    redis_client._redis = mock_redis
    yield mock_redis
    redis_client._redis = original_redis
    await mock_redis.close()

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    """Register custom marks to avoid warnings"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )

@pytest.fixture
def mock_tts_service():
    """Provide a mock TTS service for testing"""
    service = TTSService(test_mode=True)
    service.test_chunks = [b"test_audio_data"]
    return service

@pytest.fixture(autouse=True)
def patch_tts_service(mock_tts_service):
    with patch('app.services.tts_service.TTSService') as mock:
        mock.return_value = mock_tts_service
        yield mock
