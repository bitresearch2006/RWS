# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_file: str, diagnostics_enabled: bool) -> logging.Logger:
    logger = logging.getLogger("RWSLogger")
    logger.setLevel(logging.DEBUG if diagnostics_enabled else logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if diagnostics_enabled else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if diagnostics_enabled else logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def log_status(logger: logging.Logger, message: str, level: str = "info"):
    if logger:
        if level == "debug":
            logger.debug(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        else:
            logger.info(message)
