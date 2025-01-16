import sys
import uvicorn
from app.core.logging import setup_logging

logger = setup_logging()

def get_server_config():
    """Get platform-specific server configuration"""
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "log_level": "info",
    }
    
    # Add Unix-specific optimizations
    if sys.platform != 'win32':
        config.update({
            "workers": 4,
            "loop": "uvloop",
            "http": "httptools"
        })
    else:
        logger.info("Running on Windows - some optimizations not available")
    
    return config

if __name__ == "__main__":
    config = get_server_config()
    uvicorn.run(**config)
