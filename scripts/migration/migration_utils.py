#!/usr/bin/env python3
"""
Migration utilities for handling large-scale data transformations
"""

import logging
from typing import Dict, Any, List, Iterator
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationUtils:
    """Utility functions for migration operations"""

    @staticmethod
    def batch_iterator(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
        """Create batches from data for processing"""
        for i in range(0, len(data), batch_size):
            yield data[i : i + batch_size]

    @staticmethod
    def normalize_researcher_name(name: str) -> str:
        """Normalize researcher name format"""
        if not name:
            return ""
        # Remove extra whitespace
        name = " ".join(name.split())
        # Title case
        return name.title()

    @staticmethod
    def normalize_institution_name(institution: str) -> str:
        """Normalize institution name"""
        if not institution:
            return ""
        institution = " ".join(institution.split())
        return institution.strip()

    @staticmethod
    def validate_year(year: Any) -> Optional[int]:
        """Validate and convert year to integer"""
        try:
            year_int = int(year)
            if 1900 <= year_int <= 2026:
                return year_int
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def create_migration_record(
        source_data: Dict[str, Any],
        target_schema: str,
        transformation_applied: List[str],
    ) -> Dict[str, Any]:
        """Create migration record with metadata"""
        return {
            "source_data": source_data,
            "target_schema": target_schema,
            "transformation_applied": transformation_applied,
            "migration_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
        }


if __name__ == "__main__":
    utils = MigrationUtils()

    # Test batch iterator
    test_data = list(range(100))
    batches = list(utils.batch_iterator(test_data, 10))
    logger.info(f"Created {len(batches)} batches")

    # Test name normalization
    test_name = "  dr.   jane   smith  "
    normalized = utils.normalize_researcher_name(test_name)
    logger.info(f"Normalized: '{test_name}' -> '{normalized}'")
