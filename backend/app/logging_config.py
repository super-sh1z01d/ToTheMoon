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

    # Create a rotating file handler
    # This will create up to 5 backup files of 5MB each.
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

    # Also, let's make sure our own app's loggers use this config
    logging.getLogger("app").setLevel(logging.INFO)
