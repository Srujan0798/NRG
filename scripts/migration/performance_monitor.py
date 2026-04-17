#!/usr/bin/env python3
"""
Performance monitoring utilities for ETL operations
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and log performance metrics"""

    def __init__(self):
        self.metrics = {}
        self.start_time = None

    def start_monitoring(self, operation: str) -> None:
        """Start monitoring an operation"""
        self.metrics[operation] = {
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
        }
        logger.info(f"Started monitoring: {operation}")

    def stop_monitoring(self, operation: str) -> float:
        """Stop monitoring an operation"""
        if operation in self.metrics:
            self.metrics[operation]["end_time"] = time.time()
            self.metrics[operation]["duration"] = (
                self.metrics[operation]["end_time"]
                - self.metrics[operation]["start_time"]
            )
            logger.info(f"Stopped monitoring: {operation}")
            logger.info(f"Duration: {self.metrics[operation]['duration']:.2f}s")
            return self.metrics[operation]["duration"]
        return 0.0

    @contextmanager
    def track_operation(self, operation: str):
        """Context manager for tracking operation duration"""
        self.start_monitoring(operation)
        try:
            yield
        finally:
            self.stop_monitoring(operation)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics"""
        return self.metrics

    def log_summary(self) -> None:
        """Log summary of all metrics"""
        logger.info("Performance Summary:")
        for operation, data in self.metrics.items():
            if data["duration"]:
                logger.info(f"  {operation}: {data['duration']:.2f}s")


if __name__ == "__main__":
    monitor = PerformanceMonitor()

    # Test monitoring
    with monitor.track_operation("test_operation"):
        time.sleep(1)

    monitor.log_summary()
