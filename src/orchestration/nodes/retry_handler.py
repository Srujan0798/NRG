#!/usr/bin/env python3
"""
Retry Handler for Agentic Workflow Engine
Handles failure recovery for complex queries
"""

import sys
import logging
import time
from typing import Callable, Optional, ParamSpec, TypeVar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("retry_handler.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


class RetryHandler:
    """Retry handler for agentic workflow engine"""

    def __init__(self, max_retries: int = 3, sleep_fn: Callable[[float], None] | None = None):
        self.max_retries = max(1, min(int(max_retries), 3))
        self.sleep_fn = sleep_fn or time.sleep

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        """Return deterministic exponential backoff: 2^n seconds."""
        return float(2 ** max(attempt, 0))

    def handle_retry(self, operation: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Handle operation with automatic retry on failures

        Args:
            operation: Function to execute with retry capability
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of operation or raises exception after max retries
        """
        last_exception: Optional[BaseException] = None

        for attempt in range(self.max_retries + 1):
            try:
                # Try the operation
                result = operation(*args, **kwargs)
                return result
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.backoff_seconds(attempt)
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}"
                    )
                    self.sleep_fn(delay)
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries} retries: {e}"
                    )
                    raise last_exception

        # If we get here, all retries failed
        assert last_exception is not None
        raise last_exception


def main() -> None:
    """Main function for retry handler"""
    logger.info("Retry handler initialized")

    # In a real implementation, this would be integrated with the agentic workflow
    # to automatically handle retries for failed operations


if __name__ == "__main__":
    main()
