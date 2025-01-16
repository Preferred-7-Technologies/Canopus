from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import settings
from fastapi import Security, HTTPException, status, Depends, WebSocket
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from ..core.cache import redis_client
import secrets
import hashlib
from ..core.logging import setup_logging

logger = setup_logging()

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key")

# Rate limiting configuration
RATE_LIMIT_DURATION = 3600  # 1 hour
MAX_REQUESTS = 1000

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """Verify API key and check rate limits"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Check if API key exists
    if not await redis_client.exists(f"api_key:{key_hash}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Rate limiting
    requests = await redis_client.incr(f"rate_limit:{key_hash}")
    if requests == 1:
        await redis_client.expire(f"rate_limit:{key_hash}", RATE_LIMIT_DURATION)
    elif requests > MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return True

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Validate JWT token and return user info"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        if not payload:
            raise credentials_exception
        
        # Check token in blacklist
        if await redis_client.exists(f"blacklist:{token}"):
            raise credentials_exception
            
        return payload
    except JWTError:
        raise credentials_exception

async def get_current_user_ws(websocket: WebSocket) -> Dict[str, Any]:
    """Validate JWT token from WebSocket and return user info"""
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        # Verify token
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        # Check token blacklist
        is_blacklisted = await redis_client.exists(f"blacklist:{token}")
        if is_blacklisted:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return payload
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None

async def validate_ws_connection(websocket: WebSocket) -> bool:
    """Validate WebSocket connection rate limits and authentication"""
    try:
        client_ip = websocket.client.host
        rate_key = f"ws_rate:{client_ip}"
        
        # Check rate limit
        requests = await redis_client.incr(rate_key)
        if requests == 1:
            await redis_client.expire(rate_key, 60)  # 1 minute window
        elif requests > 60:  # 60 connections per minute
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False
            
        return True
    except Exception as e:
        logger.error(f"WebSocket validation failed: {str(e)}")
        return False

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm="HS256"
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_api_key() -> str:
    """Generate new API key"""
    return secrets.token_urlsafe(32)

async def blacklist_token(token: str) -> None:
    """Add token to blacklist"""
    await redis_client.setex(
        f"blacklist:{token}",
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "1"
    )
