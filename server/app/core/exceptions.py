from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .error_tracking import ErrorHandler
from typing import Union

async def http_exception_handler(
    request: Request,
    exc: Union[HTTPException, StarletteHTTPException]
):
    await ErrorHandler.capture_exception(exc, {"url": str(request.url)})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail),
                "type": "http_error",
                "request_id": request.state.request_id
            }
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    await ErrorHandler.capture_exception(exc, {"url": str(request.url)})
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "type": "validation_error",
                "request_id": request.state.request_id
            }
        }
    )

class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str = "api_error",
        error_code: str = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_type = error_type
        self.error_code = error_code
