#!/usr/bin/env python3
"""
Utility functions for common operations
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import uuid

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())


def hash_string(input_string: str) -> str:
    """Generate MD5 hash of string"""
    return hashlib.md5(input_string.encode()).hexdigest()


def json_serialize(obj: Any) -> str:
    """Serialize object to JSON"""
    return json.dumps(obj, indent=2, default=str)


def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple:
    """Validate that required fields are present"""
    missing = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing.append(field)
    return len(missing) == 0, missing


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return dictionary.get(key, default)


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split list into batches"""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


if __name__ == "__main__":
    # Test utilities
    test_uuid = generate_uuid()
    test_hash = hash_string("test")
    test_ts = get_timestamp()

    logger.info(f"UUID: {test_uuid}")
    logger.info(f"Hash: {test_hash}")
    logger.info(f"Timestamp: {test_ts}")
