import logging
import sys
from logging.handlers import RotatingFileHandler
from src.config.settings import LOG_DIR

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a structured logger with rotating file handlers.
    Separates general INFO logs and ERROR logs.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 1. Info File Handler (Rotating: Max 5MB per file, keeps last 3 backups)
        info_log_file = LOG_DIR / "app_info.log"
        info_handler = RotatingFileHandler(info_log_file, maxBytes=5*1024*1024, backupCount=3)
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)

        # 2. Error File Handler (Rotating)
        error_log_file = LOG_DIR / "app_error.log"
        error_handler = RotatingFileHandler(error_log_file, maxBytes=5*1024*1024, backupCount=3)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # 3. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(info_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

    return logger
