"""
Observability Tests — Protocol #12 Phase 3B

Tests for /api/metrics, /api/providers/health, /api/vectors/health,
Langfuse decorators, ingestion script, and anomaly alerting.

SKILLS: /python-backend (FastAPI TestClient), /testing-strategy
"""

import json
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class TestApiMetrics:
    """Tests for /api/metrics endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        api_main._api_cache.invalidate()

    @pytest.fixture
    def researcher_client(self):
        client = TestClient(api_main.app)
        response = client.post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
        token = response.json()["access_token"]
        return client, token

    def test_metrics_returns_valid_json(self, researcher_client):
        """GET /api/metrics returns valid JSON with required fields."""
        client, token = researcher_client
        response = client.get("/api/metrics", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        required_fields = ["queries", "llm_providers", "cache", "audit", "slo"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_metrics_requires_tier_1(self):
        """GET /api/metrics returns 403 for non-researcher tiers."""
        client = TestClient(api_main.app)

        gov_response = client.post("/login", json={"username": "gov_user", "password": "government-pass"})
        gov_token = gov_response.json()["access_token"]
        gov_metrics = client.get("/api/metrics", headers={"Authorization": f"Bearer {gov_token}"})
        assert gov_metrics.status_code == 403, "Government tier should be forbidden from metrics"

        ind_response = client.post("/login", json={"username": "industry_user", "password": "industry-pass"})
        ind_token = ind_response.json()["access_token"]
        ind_metrics = client.get("/api/metrics", headers={"Authorization": f"Bearer {ind_token}"})
        assert ind_metrics.status_code == 403, "Industry tier should be forbidden from metrics"

    def test_metrics_prometheus_format(self, researcher_client):
        """Accept: text/plain returns Prometheus-compatible format."""
        client, token = researcher_client
        response = client.get(
            "/api/metrics",
            headers={"Authorization": f"Bearer {token}", "Accept": "text/plain"},
        )
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_includes_slo_status(self, researcher_client):
        """Response includes slo_status with latency, citations, synthesis."""
        client, token = researcher_client
        response = client.get("/api/metrics", headers={"Authorization": f"Bearer {token}"})
        data = response.json()

        assert "latency" in data["slo"], "SLO status must include latency"
        assert "citations" in data["slo"], "SLO status must include citations"
        assert "synthesis" in data["slo"], "SLO status must include synthesis"
        assert "overall" in data["slo"], "SLO status must include overall"

    def test_metrics_includes_provider_health(self, researcher_client):
        """Response includes llm_providers.mesh_health with provider statuses."""
        client, token = researcher_client
        response = client.get("/api/metrics", headers={"Authorization": f"Bearer {token}"})
        data = response.json()

        assert "llm_providers" in data
        assert "mesh_health" in data["llm_providers"]

    def test_metrics_includes_audit_chain_info(self, researcher_client):
        """Response includes audit.chain_length, chain_valid, valid_event_count."""
        client, token = researcher_client
        response = client.get("/api/metrics", headers={"Authorization": f"Bearer {token}"})
        data = response.json()

        assert "audit" in data
        assert "chain_length" in data["audit"]
        assert "chain_valid" in data["audit"]
        assert "valid_event_count" in data["audit"]


class TestProvidersHealthEndpoint:
    """Tests for /api/providers/health endpoint."""

    def test_providers_health_returns_json(self):
        """GET /api/providers/health returns provider health JSON."""
        client = TestClient(api_main.app)
        response = client.get("/api/providers/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "providers" in data, "Response must have providers field"
        assert "timeout_budget_seconds" in data, "Response must include timeout budget"


class TestVectorsHealthEndpoint:
    """Tests for /api/vectors/health endpoint."""

    def test_vectors_health_returns_collection_stats(self):
        """GET /api/vectors/health returns vector collection stats."""
        client = TestClient(api_main.app)
        response = client.get("/api/vectors/health")

        if response.status_code == 503:
            pytest.skip("Qdrant not available")
        assert response.status_code == 200
        data = response.json()

        required = ["collection_name", "vector_count", "index_status"]
        for field in required:
            assert field in data, f"Missing required field: {field}"


class TestSloTrackerAnomalyAlerting:
    """Tests for SLO anomaly alerting."""

    def test_p95_breach_triggers_warning(self):
        """P95 latency breach for 5+ minutes logs CRITICAL."""
        from src.observability.metrics import SLOTracker
        import logging
        import io
        from unittest.mock import patch

        tracker = SLOTracker(max_samples=100)
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.CRITICAL)
        logger = logging.getLogger("src.observability.metrics")
        logger.addHandler(handler)
        logger.setLevel(logging.CRITICAL)

        base_time = 1000.0
        with patch("time.time", return_value=base_time):
            tracker.record_latency(10000.0)

        with patch("time.time", return_value=base_time + 400):
            for _ in range(5):
                tracker.record_latency(10000.0)

        log_output = log_capture.getvalue()
        assert "SLO BREACH" in log_output or "P95" in log_output.upper(), \
            f"Expected SLO breach warning in logs, got: {log_output}"

        logger.removeHandler(handler)

    def test_provider_zero_success_rate_triggers_critical(self):
        """Provider with 0%% success for 10+ min logs CRITICAL."""
        from src.observability.metrics import SLOTracker
        import logging
        import io
        from unittest.mock import patch

        tracker = SLOTracker(max_samples=100)
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.CRITICAL)
        logger = logging.getLogger("src.observability.metrics")
        logger.addHandler(handler)
        logger.setLevel(logging.CRITICAL)

        base_time = 2000.0
        with patch("time.time", return_value=base_time):
            tracker.check_provider_breach("nvidia", success_rate=0.0)

        with patch("time.time", return_value=base_time + 700):
            tracker.check_provider_breach("nvidia", success_rate=0.0)

        log_output = log_capture.getvalue()
        assert "PROVIDER BREACH" in log_output or "nvidia" in log_output.lower(), \
            f"Expected provider breach warning, got: {log_output}"

        logger.removeHandler(handler)


class TestLangfuseTracing:
    """Tests for Langfuse tracer activation/deactivation."""

    def test_langfuse_decorator_silent_when_no_keys(self):
        """Decorators complete without error when Langfuse keys are absent."""
        from src.observability.langfuse_tracer import trace_llm_call, _init_langfuse

        client = _init_langfuse()
        assert client is None, "Langfuse should be None when keys are absent"

        @trace_llm_call("test_node")
        def dummy_fn(x):
            return x * 2

        result = dummy_fn(5)
        assert result == 10, "Function should still work with unconfigured tracer"

    def test_sql_generation_decorator_exists(self):
        """trace_sql_generation decorator is available in langfuse_tracer."""
        from src.observability.langfuse_tracer import trace_sql_generation
        assert callable(trace_sql_generation), "trace_sql_generation should be a callable decorator"

    def test_rag_retrieval_decorator_exists(self):
        """trace_rag_retrieval decorator is available in langfuse_tracer."""
        from src.observability.langfuse_tracer import trace_rag_retrieval
        assert callable(trace_rag_retrieval), "trace_rag_retrieval should be a callable decorator"

    def test_trace_sql_generation_wraps_function(self):
        """trace_sql_generation decorator can wrap a function."""
        from src.observability.langfuse_tracer import trace_sql_generation

        @trace_sql_generation
        def dummy_sql_gen():
            return "SELECT * FROM researchers"

        result = dummy_sql_gen()
        assert result == "SELECT * FROM researchers"


class TestIngestionScript:
    """Tests for scripts/ingest_documents.py."""

    def test_chunk_text_splits_correctly(self):
        """_chunk_text splits text into overlapping chunks of correct size."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from scripts.ingest_documents import _chunk_text

        text = "A" * 3000
        chunks = _chunk_text(text, chunk_tokens=512, overlap_tokens=50)
        assert len(chunks) > 1, "Long text should be split into multiple chunks"
        assert all(len(c) <= 512 * 4 + 1 for c in chunks), "Chunks should respect token limit"

    def test_sha256_hashing_for_dedup(self):
        """_sha256 produces consistent hashes for duplicate detection."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from scripts.ingest_documents import _sha256

        hash1 = _sha256("test content")
        hash2 = _sha256("test content")
        hash3 = _sha256("different content")

        assert hash1 == hash2, "Same content should produce same hash"
        assert hash1 != hash3, "Different content should produce different hash"
        assert len(hash1) == 64, "SHA256 hash should be 64 characters"

    def test_ingest_csv_parser(self, tmp_path):
        """CSV parser extracts document_id, title, and content correctly."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,title,content\n1,Test Doc,This is test content.\n")

        from scripts.ingest_documents import _parse_csv
        docs = list(_parse_csv(csv_file))

        assert len(docs) == 1
        assert docs[0].document_id == "1"
        assert docs[0].title == "Test Doc"
        assert docs[0].content == "This is test content."

    def test_ingest_script_handles_malformed_csv(self, tmp_path):
        """Malformed CSV rows are skipped gracefully."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        csv_file = tmp_path / "malformed.csv"
        csv_file.write_text("id,title,content\n1,Good,Valid row\n2,BadRow\n3,AlsoGood,Another valid\n")

        from scripts.ingest_documents import _parse_csv
        docs = list(_parse_csv(csv_file))

        assert len(docs) >= 2, "Valid rows should be parsed, malformed skipped"


class TestAnomalyAlertingIntegration:
    """Integration tests for anomaly alerting in SLOTracker."""

    def test_audit_write_blocked_after_chain_failure(self):
        """is_audit_write_blocked returns True after persistent chain failures."""
        from src.observability.metrics import SLOTracker
        from unittest.mock import patch

        tracker = SLOTracker(max_samples=100)
        base_time = 3000.0
        with patch("time.time", return_value=base_time):
            tracker.check_audit_breach(chain_valid=False, errors=["Hash mismatch at event 42"])
        with patch("time.time", return_value=base_time + 400):
            tracker.check_audit_breach(chain_valid=False, errors=["Hash mismatch at event 42"])

        assert tracker.is_audit_write_blocked() is True, \
            "Audit writes should be blocked after persistent failures"

    def test_audit_unblocked_after_recovery(self):
        """Audit writes unblocked once chain is valid again."""
        from src.observability.metrics import SLOTracker
        from unittest.mock import patch

        tracker = SLOTracker(max_samples=100)
        base_time = 4000.0
        with patch("time.time", return_value=base_time):
            tracker.check_audit_breach(chain_valid=False, errors=["Hash mismatch"])
        with patch("time.time", return_value=base_time + 400):
            tracker.check_audit_breach(chain_valid=False, errors=["Hash mismatch"])
        tracker.check_audit_breach(chain_valid=True, errors=[])

        assert tracker.is_audit_write_blocked() is False, \
            "Audit writes should be unblocked after recovery"
