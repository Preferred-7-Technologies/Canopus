import sys
import asyncio
from ..core.logging import setup_logging

logger = setup_logging()

def configure_performance():
    """Configure performance optimizations based on platform"""
    if sys_platform_is_unix():
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            logger.info("uvloop installed and configured successfully")
        except ImportError:
            logger.warning("uvloop not available, using default event loop")
    else:
        # Windows-specific optimizations
        if sys.version_info >= (3, 8):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.info("Windows event loop policy configured")

def sys_platform_is_unix():
    """Check if platform is Unix-like"""
    return sys.platform != 'win32'
