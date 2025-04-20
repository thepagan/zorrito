import logging
import os

# Define the default path for the log file
LOG_FILE_PATH = os.getenv("ZORRITO_LOG_FILE", "/app/logs/zorrito.log")

# Create logger with a proper name
logger = logging.getLogger("zorrito")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.hasHandlers():
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(logging.INFO)

    # Create formatter and add to handler
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

def configure_logging():
    return logger