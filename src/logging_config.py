




# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FILE = "log.log"


# Configure logging
logger = logging.getLogger("arb-scan")
logger.setLevel(logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# File handler with rotation (5MB per file, keep 3 backups)
file_handler = logging.FileHandler(LOG_FILE, mode="w")
file_handler.setLevel(logging.DEBUG)

# Console handler (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Common formatter
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Attach handlers (avoid duplicates if re-imported)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
