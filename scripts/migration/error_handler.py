#!/usr/bin/env python3
"""
Error handling utilities for ETL pipeline
"""

import logging
from typing import Dict, Any, Optional, Callable
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLError(Exception):
    """Base exception for ETL errors"""

    pass


class DataValidationError(ETLError):
    """Exception for data validation errors"""

    pass


class ConnectionError(ETLError):
    """Exception for connection errors"""

    pass


class TransformationError(ETLError):
    """Exception for transformation errors"""

    pass


class ErrorHandler:
    """Handle errors in ETL pipeline"""

    def __init__(self):
        self.errors = []

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Handle an error with context"""
        error_record = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
        }
        self.errors.append(error_record)
        logger.error(f"Error: {error_record}")

    def get_errors(self) -> list:
        """Get all recorded errors"""
        return self.errors

    def clear_errors(self) -> None:
        """Clear all recorded errors"""
        self.errors = []

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    def safe_execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Safely execute an operation with error handling"""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, {"operation": operation.__name__})
            return None


if __name__ == "__main__":
    handler = ErrorHandler()

    # Test error handling
    try:
        result = 1 / 0
    except Exception as e:
        handler.handle_error(e, {"operation": "test_division"})

    logger.info(f"Errors recorded: {handler.get_errors()}")
