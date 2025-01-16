import uvicorn
from app import create_app
from app.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False,
        ssl_keyfile=settings.SSL_KEYFILE if not settings.DEBUG else None,
        ssl_certfile=settings.SSL_CERTFILE if not settings.DEBUG else None,
    )
