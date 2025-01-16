import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("Canopus")
    logger.setLevel(logging.INFO)

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/Canopus.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/error.log",
        maxBytes=10485760,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)

    # Formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger
