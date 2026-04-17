#!/usr/bin/env python3
"""
Data Validation and Checksum Utilities for ETL Pipeline
Production-grade implementation for ensuring data integrity
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """Production-grade data validation utilities"""

    def __init__(self):
        self.validation_rules = {
            "researcher_id": {
                "type": str,
                "required": True,
                "pattern": r"^[a-f0-9\-]{36}$",
            },
            "name": {"type": str, "required": True, "min_length": 1, "max_length": 255},
            "institution": {"type": str, "required": True, "min_length": 1},
            "state": {"type": str, "required": True, "length": 2},
            "email": {
                "type": str,
                "required": False,
                "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            },
            "year_joined": {"type": int, "required": False, "min": 1900, "max": 2026},
        }

    def validate_researcher(self, record: Dict[str, Any]) -> tuple:
        """Validate researcher record against rules"""
        errors = []

        for field, rules in self.validation_rules.items():
            value = record.get(field)

            if rules["required"] and not value:
                errors.append(f"Missing required field: {field}")
                continue

            if value:
                if "type" in rules and not isinstance(value, rules["type"]):
                    errors.append(
                        f"Invalid type for {field}: expected {rules['type']}, got {type(value)}"
                    )

                if "min_length" in rules and len(str(value)) < rules["min_length"]:
                    errors.append(
                        f"Field {field} too short: {len(str(value))} < {rules['min_length']}"
                    )

                if "max_length" in rules and len(str(value)) > rules["max_length"]:
                    errors.append(
                        f"Field {field} too long: {len(str(value))} > {rules['max_length']}"
                    )

        return len(errors) == 0, errors

    def calculate_checksum(self, data: Any) -> str:
        """Calculate MD5 checksum for data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()

    def verify_checksum(self, data: Any, expected_checksum: str) -> bool:
        """Verify data matches expected checksum"""
        actual_checksum = self.calculate_checksum(data)
        return actual_checksum == expected_checksum


if __name__ == "__main__":
    validator = DataValidator()
    test_record = {
        "researcher_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Dr. Jane Smith",
        "institution": "MIT",
        "state": "MA",
    }
    is_valid, errors = validator.validate_researcher(test_record)
    logger.info(f"Valid: {is_valid}, Errors: {errors}")
