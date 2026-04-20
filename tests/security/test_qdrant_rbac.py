"""Tests for Qdrant RBAC implementation."""

import pytest

import src.security.rbac.qdrant_rbac as qdrant_rbac_module


class FakeQdrantClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port


def test_create_access_filter_tier1():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    f = rbac.create_access_filter(1)
    assert f.must[0].match.any == [1, 2, 3]


def test_create_access_filter_tier2():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    f = rbac.create_access_filter(2)
    assert f.must[0].match.any == [2, 3]


def test_create_access_filter_tier3():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    f = rbac.create_access_filter(3)
    assert f.must[0].match.any == [3]


def test_create_access_filter_invalid_tier():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    with pytest.raises(ValueError):
        rbac.create_access_filter(99)


def test_validate_access():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    assert rbac.validate_access(1, 1) is True
    assert rbac.validate_access(1, 3) is True
    assert rbac.validate_access(2, 1) is False
    assert rbac.validate_access(2, 2) is True
    assert rbac.validate_access(2, 3) is True
    assert rbac.validate_access(3, 2) is False
    assert rbac.validate_access(3, 3) is True
    assert rbac.validate_access(99, 1) is False


def test_filter_search_results():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    results = [
        {"payload": {"access_tier": 1}},
        {"payload": {"access_tier": 2}},
        {"payload": {"access_tier": 3}},
    ]
    filtered = rbac.filter_search_results(results, 2)
    assert len(filtered) == 2
    assert filtered[0]["payload"]["access_tier"] == 2
    assert filtered[1]["payload"]["access_tier"] == 3


def test_inject_access_filter_no_existing():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    query = {"vector": [0.1]}
    result = rbac.inject_access_filter(query, 2)
    assert "filter" in result


def test_inject_access_filter_with_existing():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    existing = qdrant_rbac_module.models.Filter(must=[])
    query = {"vector": [0.1], "filter": existing}
    result = rbac.inject_access_filter(query, 2)
    assert "filter" in result


def test_setup_collection_security_logs(caplog):
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    with caplog.at_level("INFO"):
        rbac.setup_collection_security("test_collection")
    assert "test_collection" in caplog.text


def test_test_access_isolation():
    rbac = qdrant_rbac_module.QdrantRBAC.__new__(qdrant_rbac_module.QdrantRBAC)
    rbac.client = FakeQdrantClient("localhost", 6333)
    rbac.access_tier_mapping = {1: "full_access", 2: "limited_access", 3: "public_access"}
    results = rbac.test_access_isolation()
    assert results["tier_1_tests"] == 1
    assert results["tier_2_tests"] == 1
    assert results["tier_3_tests"] == 1
    assert results["passed"] == 3
    assert results["failed"] == 0
