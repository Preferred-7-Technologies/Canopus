from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime

T = TypeVar('T')

class ResponseMetadata(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

class APIResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[T] = None
    metadata: ResponseMetadata

class PaginatedResponse(APIResponse, Generic[T]):
    data: T
    page: int
    page_size: int
    total_count: int
    total_pages: int

class ErrorResponse(BaseModel):
    error: dict = Field(
        ...,
        example={
            "code": 400,
            "message": "Bad Request",
            "type": "validation_error",
            "details": []
        }
    )
    metadata: ResponseMetadata
