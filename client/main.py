import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from app.core.config import ClientConfig
from app.ui.main_window import MainWindow
from app.core.logging import setup_logging
import sentry_sdk
from app.core.exceptions import handle_exception

logger = setup_logging()

def initialize_sentry(config: ClientConfig):
    if config.SENTRY_DSN:
        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            environment=config.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized for client application")

def main():
    try:
        # Load configuration
        config = ClientConfig()
        
        # Initialize error tracking
        initialize_sentry(config)
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Canopus")
        app.setOrganizationName("Canopus Enterprise")
        
        # Set up exception handling
        sys.excepthook = handle_exception
        
        # Create and show main window
        window = MainWindow(config)
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
