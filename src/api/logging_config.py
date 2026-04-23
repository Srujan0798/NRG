"""
Structured JSON Logging Configuration
Logs in JSON format for ELK/Grafana aggregation.
"""

import logging
import json
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for log aggregation systems."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in logging.LogRecord(
                    "", "", 0, "", (), None, None
                ).__dict__ and not k.startswith("_")
            }
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """Wrapper for structured logging with context."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "StructuredLogger":
        """Add context to all subsequent logs."""
        new_logger = StructuredLogger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(self, level: int, msg: str, **kwargs: Any):
        reserved = {"exc_info", "stack_info", "stack_depth", "extra"}
        filtered = {k: v for k, v in kwargs.items() if k not in reserved}
        extra = {**self._context, **filtered}
        self.logger.log(level, msg, extra=extra)

    def debug(self, msg: str, **kwargs: Any):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any):
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any):
        self._log(logging.CRITICAL, msg, **kwargs)


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
    include_extra: bool = True,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Output JSON instead of text logs
        include_extra: Include extra fields from record
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if json_format:
        handler.setFormatter(JSONFormatter(include_extra=include_extra))
    else:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(format_str))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
