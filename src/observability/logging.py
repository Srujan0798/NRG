"""Structured JSON Logging for NRG - consistent logging format across all services."""

import logging
import json
import sys
import re
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from functools import wraps
from contextvars import ContextVar


_request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


SENSITIVE_PATTERNS = [
    (r'password["\']?\s*[:=]\s*["\'][^"\']+["\']', 'password: ***'),
    (r'token["\']?\s*[:=]\s*["\'][^"\']+["\']', 'token: ***'),
    (r'authorization["\']?\s*[:=]\s*["\'][^"\']+["\']', 'authorization: ***'),
    (r'Bearer\s+[^\s]+', 'Bearer ***'),
    (r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']', 'secret: ***'),
    (r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']', 'api_key: ***'),
]


def _redact_sensitive(text: str) -> str:
    """Redact sensitive data from text."""
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _sanitize_value(value: Any, max_length: int = 1000) -> Any:
    """Sanitize a value for logging."""
    if isinstance(value, str):
        sanitized = _redact_sensitive(value)
        return sanitized[:max_length] if len(sanitized) > max_length else sanitized
    elif isinstance(value, dict):
        return {k: _sanitize_value(v, max_length) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(v, max_length) for v in value[:100]]
    elif isinstance(value, (int, float, bool)):
        return value
    else:
        return str(value)[:max_length]


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, service_name: str = "nrg"):
        super().__init__()
        self.service_name = service_name
        self.environment = os.getenv("ENV", "production")
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": _sanitize_value(record.getMessage(), max_length=2000),
            "environment": self.environment,
        }
        
        if record.pathname:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        if hasattr(record, 'request_id') and record.request_id:
            log_data["request_id"] = record.request_id
        if hasattr(record, 'user_id') and record.user_id:
            log_data["user_id"] = record.user_id
        if hasattr(record, 'trace_id') and record.trace_id:
            log_data["trace_id"] = record.trace_id
        
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'lineno', 'module', 'msecs', 'pathname',
                          'process', 'processName', 'relativeCreated', 'stack_info',
                          'exc_info', 'exc_text', 'thread', 'threadName', 'message',
                          'request_id', 'user_id', 'trace_id'):
                if not key.startswith('_'):
                    log_data[key] = _sanitize_value(value)
        
        try:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        except Exception:
            return json.dumps({
                "timestamp": log_data["timestamp"],
                "level": log_data["level"],
                "service": self.service_name,
                "message": "LOGGING_ERROR: Failed to serialize log record"
            })


def setup_logging(
    service_name: str = "nrg",
    level: str = None,
    log_format: str = "json"
):
    """Setup structured JSON logging for the application."""
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    
    if log_format == "json":
        console_handler.setFormatter(JSONFormatter(service_name))
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None, trace_id: Optional[str] = None):
    """Set request context for logging."""
    if request_id:
        _request_id_var.set(request_id)
    if user_id:
        _user_id_var.set(user_id)
    if trace_id:
        _trace_id_var.set(trace_id)


def get_request_context() -> Dict[str, Optional[str]]:
    """Get current request context."""
    return {
        "request_id": _request_id_var.get(),
        "user_id": _user_id_var.get(),
        "trace_id": _trace_id_var.get()
    }


class StructuredLogger:
    """Logger wrapper that adds structured context to all logs."""
    
    def __init__(self, name: str, default_context: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.default_context = default_context or {}
    
    def _build_context(self, **kwargs) -> Dict[str, Any]:
        context = dict(self.default_context)
        context.update(kwargs)
        context.update(get_request_context())
        return context
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=self._build_context(**kwargs))
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=self._build_context(**kwargs))
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=self._build_context(**kwargs))
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=self._build_context(**kwargs))
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=self._build_context(**kwargs))
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log an HTTP request."""
        self.logger.info(
            f"{method} {path} {status_code} {duration_ms:.2f}ms",
            extra=self._build_context(
                event="http_request",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                **kwargs
            )
        )
    
    def log_llm_call(self, provider: str, model: str, tokens: int, duration_ms: float, **kwargs):
        """Log an LLM API call."""
        self.logger.info(
            f"LLM {provider}/{model}: {tokens} tokens in {duration_ms:.2f}ms",
            extra=self._build_context(
                event="llm_call",
                provider=provider,
                model=model,
                tokens=tokens,
                duration_ms=duration_ms,
                **kwargs
            )
        )
    
    def log_query(self, query_text: str, intent: str, user_tier: int, success: bool, **kwargs):
        """Log a user query."""
        self.logger.info(
            f"Query [{intent}] tier={user_tier} success={success}",
            extra=self._build_context(
                event="query",
                query_preview=query_text[:200] if query_text else "",
                intent=intent,
                user_tier=user_tier,
                success=success,
                **kwargs
            )
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log an error with full context."""
        error_context = {
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "**kwargs": kwargs
        }
        if context:
            error_context.update(context)
        
        self.logger.error(
            f"ERROR: {type(error).__name__}: {str(error)}",
            extra=self._build_context(**error_context),
            exc_info=True
        )


def log_function_call(func_name: str = None):
    """Decorator to log function entry and exit."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            logger = logging.getLogger(func.__module__)
            logger.debug(f"ENTER: {name}", extra={"function": name, "args": str(args)[:200]})
            try:
                result = func(*args, **kwargs)
                logger.debug(f"EXIT: {name}", extra={"function": name, "status": "success"})
                return result
            except Exception as e:
                logger.error(
                    f"EXCEPTION in {name}: {str(e)}",
                    extra={"function": name, "error": str(e), "error_type": type(e).__name__},
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


class LogCapture:
    """Capture logs for testing or analysis."""
    
    def __init__(self, logger_name: str = None, level: int = logging.INFO):
        self.logger_name = logger_name
        self.level = level
        self.records: List[logging.LogRecord] = []
        self.handler: Optional[logging.Handler] = None
    
    def __enter__(self):
        self.records = []
        logger = logging.getLogger(self.logger_name) if self.logger_name else logging.getLogger()
        
        class CaptureHandler(logging.Handler):
            def __init__(self, capture):
                super().__init__()
                self.capture = capture
            
            def emit(self, record):
                self.capture.records.append(record)
        
        self.handler = CaptureHandler(self)
        self.handler.setLevel(self.level)
        logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            logger = logging.getLogger(self.logger_name) if self.logger_name else logging.getLogger()
            logger.removeHandler(self.handler)
    
    def get_messages(self) -> List[str]:
        """Get captured log messages."""
        return [r.getMessage() for r in self.records]
    
    def get_structured_logs(self) -> List[Dict[str, Any]]:
        """Get captured logs as structured data."""
        formatter = JSONFormatter()
        return [json.loads(formatter.format(r)) for r in self.records]


def create_logger(name: str, **default_context) -> StructuredLogger:
    """Create a structured logger with default context."""
    return StructuredLogger(name, default_context)