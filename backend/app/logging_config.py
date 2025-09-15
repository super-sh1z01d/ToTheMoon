import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configures logging to a rotating file."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a rotating file handler
    # This will create up to 5 backup files of 5MB each.
    handler = RotatingFileHandler(
        'logs/backend.log', 
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
