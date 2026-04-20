"""Tests for utility helpers."""

import json
import uuid
from datetime import datetime

from src.utils.helpers import (
    generate_uuid,
    hash_string,
    json_serialize,
    get_timestamp,
    validate_required_fields,
    safe_get,
    batch_list,
)


class TestGenerateUUID:
    def test_returns_string(self):
        result = generate_uuid()
        assert isinstance(result, str)

    def test_returns_valid_uuid(self):
        result = generate_uuid()
        parsed = uuid.UUID(result)
        assert str(parsed) == result


class TestHashString:
    def test_returns_hex_string(self):
        result = hash_string("test")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_deterministic(self):
        assert hash_string("hello") == hash_string("hello")
        assert hash_string("hello") != hash_string("world")


class TestJsonSerialize:
    def test_serializes_dict(self):
        data = {"key": "value", "num": 42}
        result = json_serialize(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_serializes_list(self):
        data = [1, 2, 3]
        result = json_serialize(data)
        parsed = json.loads(result)
        assert parsed == data


class TestGetTimestamp:
    def test_returns_iso_string(self):
        result = get_timestamp()
        assert isinstance(result, str)
        dt = datetime.fromisoformat(result)
        assert dt.tzinfo is not None


class TestValidateRequiredFields:
    def test_all_present(self):
        ok, missing = validate_required_fields({"a": 1, "b": 2}, ["a", "b"])
        assert ok is True
        assert missing == []

    def test_missing_field(self):
        ok, missing = validate_required_fields({"a": 1}, ["a", "b"])
        assert ok is False
        assert "b" in missing

    def test_empty_value_considered_missing(self):
        ok, missing = validate_required_fields({"a": ""}, ["a"])
        assert ok is False
        assert "a" in missing

    def test_none_value_considered_missing(self):
        ok, missing = validate_required_fields({"a": None}, ["a"])
        assert ok is False
        assert "a" in missing


class TestSafeGet:
    def test_existing_key(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_missing_key_with_default(self):
        assert safe_get({}, "a", "default") == "default"

    def test_missing_key_no_default(self):
        assert safe_get({}, "a") is None


class TestBatchList:
    def test_batches_correctly(self):
        items = [1, 2, 3, 4, 5]
        batches = batch_list(items, 2)
        assert batches == [[1, 2], [3, 4], [5]]

    def test_exact_batch_size(self):
        items = [1, 2, 3, 4]
        batches = batch_list(items, 2)
        assert batches == [[1, 2], [3, 4]]

    def test_empty_list(self):
        assert batch_list([], 3) == []

    def test_batch_larger_than_list(self):
        items = [1]
        batches = batch_list(items, 10)
        assert batches == [[1]]
