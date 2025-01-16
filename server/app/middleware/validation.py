from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
import json

app = FastAPI()

class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        json.loads(body)
            
            response = await call_next(request)
            return response
            
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON data"
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=str(e)
            )

app.add_middleware(ValidationMiddleware)
