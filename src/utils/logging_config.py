#!/usr/bin/env python3
"""
Logging configuration for production environment
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime, UTC
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(
    log_level: str = "INFO", log_file: str = None, json_format: bool = False
):
    """Setup logging configuration"""

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))

    root_logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            file_handler.setFormatter(logging.Formatter(file_format))

        root_logger.addHandler(file_handler)

    return root_logger


if __name__ == "__main__":
    # Test logging setup
    logger = setup_logging(log_level="DEBUG", log_file="test.log")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
