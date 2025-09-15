import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configures logging to a rotating file."""
    # Ensure log directory exists
    log_file_path = 'logs/backend.log'
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers to prevent duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a rotating file handler
    handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=5*1024*1024, # 5 MB
        backupCount=5
    )

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    logger.addHandler(handler)

    # Suppress console output from uvicorn and other libraries
    # Set levels for specific loggers to CRITICAL or ERROR
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.server").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL) # Suppress httpx logs
    logging.getLogger("websockets").setLevel(logging.CRITICAL) # Suppress websockets logs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL) # Suppress SQLAlchemy SQL logs

    # Also, let's make sure our own app's loggers use this config
    logging.getLogger("app").setLevel(logging.INFO)
