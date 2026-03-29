import logging
import os
from logging.handlers import TimedRotatingFileHandler
from app.config import Config


def get_logger(name):
    # Configure root logger to ensure all child loggers inherit settings
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not root_logger.handlers:
        config = Config()
        log_path = config.LOG_PATH

        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        root_logger.addHandler(ch)

        # File Handler (Timed Rotating) - Daily rotation
        backup_count = config.LOG_RETENTION_DAYS if config.DELETE_OLD_LOGS else 0

        try:
            fh = TimedRotatingFileHandler(
                log_path,
                when="midnight",
                interval=1,
                backupCount=backup_count,
                encoding="utf-8",
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            root_logger.addHandler(fh)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    return logging.getLogger(name)
