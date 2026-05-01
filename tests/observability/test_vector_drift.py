"""Tests for Vector Drift Monitor — C5: Auto-Retrain Trigger."""

import json
from unittest.mock import patch, MagicMock
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "vector_drift_check.py"
_spec = importlib.util.spec_from_file_location("vector_drift_check", SCRIPT_PATH)
_vdc = importlib.util.module_from_spec(_spec)
sys.modules["vector_drift_check"] = _vdc
_spec.loader.exec_module(_vdc)

_trigger_reindex = _vdc._trigger_reindex
_check_cosine_shift = _vdc._check_cosine_shift
_cosine_shift = _vdc._cosine_shift
_load_reference_centroids = _vdc._load_reference_centroids
BENCHMARK_QUERIES = _vdc.BENCHMARK_QUERIES
DRIFT_SCORE_SLO = _vdc.DRIFT_SCORE_SLO
DRIFT_SCORE_WARNING = _vdc.DRIFT_SCORE_WARNING
DRIFT_SCORE_CRITICAL = _vdc.DRIFT_SCORE_CRITICAL
COSINE_SHIFT_THRESHOLD = _vdc.COSINE_SHIFT_THRESHOLD
run_drift_check = _vdc.run_drift_check
_qdrant_ready_for_benchmark = _vdc._qdrant_ready_for_benchmark
establish_baseline = _vdc.establish_baseline
write_status_file = _vdc._write_status_file


class TestCosineShift:
    """Unit tests for cosine shift computation."""

    def test_identical_vectors_near_zero_shift(self):
        """Identical vectors produce near-zero cosine shift (within float epsilon)."""
        vec = [0.1] * 128
        shift = _cosine_shift(vec, vec)
        assert abs(shift) < 1e-10, f"Expected near-zero shift for identical vectors, got {shift}"

    def test_opposite_vectors_max_shift(self):
        """Opposite vectors produce maximum shift (1.0)."""
        vec_a = [1.0] * 128
        vec_b = [-1.0] * 128
        shift = _cosine_shift(vec_a, vec_b)
        assert abs(shift - 1.0) < 0.01

    def test_orthogonal_vectors_high_shift(self):
        """Orthogonal vectors produce high shift."""
        vec_a = [1.0] * 64 + [0.0] * 64
        vec_b = [0.0] * 64 + [1.0] * 64
        shift = _cosine_shift(vec_a, vec_b)
        assert 0.4 < shift < 0.6


class TestTriggerReindex:
    """Unit tests for _trigger_reindex()."""

    @patch("httpx.post")
    def test_trigger_posts_to_reindex_endpoint(self, mock_post):
        """When cosine shift triggers reindex, POST to /api/reindex."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "reindex_scheduled"}
        mock_post.return_value = mock_resp

        with patch.dict("os.environ", {"NRG_SERVICE_TOKEN": "test-token"}):
            _trigger_reindex(
                {"alert_level": "CRITICAL", "drift_score": 0.35},
                {"max_shift": 0.08, "shifting_topics": ["machine learning"]}
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/reindex" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
        payload = call_args[1]["json"]
        assert payload["drift_score"] == 0.35
        assert payload["cosine_shift"] == 0.08
        assert "machine learning" in payload["shifting_topics"]

    @patch("httpx.post")
    def test_trigger_skips_when_no_token(self, mock_post):
        """No POST when NRG_SERVICE_TOKEN is absent."""
        with patch.dict("os.environ", {}, clear=True):
            _trigger_reindex(
                {"alert_level": "WARNING", "drift_score": 0.55},
                {"max_shift": 0.06, "shifting_topics": []}
            )
        mock_post.assert_not_called()


class TestCheckCosineShift:
    """Unit tests for _check_cosine_shift()."""

    @patch("vector_drift_check._load_reference_centroids")
    @patch("vector_drift_check._compute_centroids")
    def test_no_reference_establishes_baseline(self, mock_compute, mock_load_ref):
        """When no reference centroids exist, establish baseline."""
        mock_load_ref.return_value = {}
        mock_compute.return_value = {"ml": [0.1] * 128}

        mock_retriever = MagicMock()
        mock_embedder = MagicMock()

        result = _check_cosine_shift({}, mock_retriever, mock_embedder)

        assert result["status"] == "baseline_established"
        assert result["reindex_triggered"] is False

    @patch("vector_drift_check._load_reference_centroids")
    @patch("vector_drift_check._compute_centroids")
    def test_shift_above_threshold_triggers_reindex(self, mock_compute, mock_load_ref):
        """Cosine shift > 0.05 triggers reindex."""
        mock_load_ref.return_value = {"ml": [0.1] * 128}
        mock_compute.return_value = {"ml": [0.5 if i < 10 else 0.1 for i in range(128)]}

        mock_retriever = MagicMock()
        mock_embedder = MagicMock()

        result = _check_cosine_shift({}, mock_retriever, mock_embedder)

        assert result["reindex_triggered"] is True, f"Expected reindex_triggered=True, got {result}"
        assert result["max_shift"] > COSINE_SHIFT_THRESHOLD

    @patch("vector_drift_check._load_reference_centroids")
    @patch("vector_drift_check._compute_centroids")
    def test_stable_when_shift_below_threshold(self, mock_compute, mock_load_ref):
        """Shift < 0.05 returns stable, no reindex."""
        import math
        ref_vec = [0.1] * 128
        ref_norm = math.sqrt(sum(v * v for v in ref_vec))
        ref_vec = [v / ref_norm for v in ref_vec]

        near_vec = [0.1001 if i == 0 else 0.0999 for i in range(128)]
        near_norm = math.sqrt(sum(v * v for v in near_vec))
        near_vec = [v / near_norm for v in near_vec]

        mock_load_ref.return_value = {"ml": ref_vec}
        mock_compute.return_value = {"ml": near_vec}

        mock_retriever = MagicMock()
        mock_embedder = MagicMock()

        result = _check_cosine_shift({}, mock_retriever, mock_embedder)

        assert result["status"] == "stable"
        assert result["reindex_triggered"] is False


class TestEstablishBaseline:
    """Tests for explicit C5 baseline establishment."""

    @patch("vector_drift_check._save_benchmark_cache")
    @patch("vector_drift_check._save_reference_centroids")
    @patch("vector_drift_check._compute_centroids")
    @patch("src.skills.rag.embedder.Embedder")
    def test_establish_baseline_persists_reference_data(
        self,
        mock_embedder_class,
        mock_compute,
        mock_save_centroids,
        mock_save_benchmark,
    ):
        class FakeRetriever:
            def retrieve(self, query_vector, user_tier=1, top_k=5, **kwargs):
                return {
                    "metadata": [
                        {
                            "institution": "IIT Gandhinagar",
                            "topics": ["machine learning"],
                        }
                    ]
                }

        fake_embedder = MagicMock()
        mock_embedder_class.return_value = fake_embedder
        mock_compute.return_value = {"machine learning": [0.1, 0.2, 0.3]}

        result = establish_baseline(FakeRetriever())

        assert result["status"] == "baseline_established"
        assert result["centroids_saved"] == 1
        assert result["queries_saved"] == len(BENCHMARK_QUERIES)
        mock_save_centroids.assert_called_once_with({"machine learning": [0.1, 0.2, 0.3]})
        mock_save_benchmark.assert_called_once()
        fake_embedder.close.assert_called_once()


class TestStatusFile:
    def test_write_status_file_persists_vector_drift_health(self, monkeypatch, tmp_path):
        status_file = tmp_path / "vector_drift_status.json"
        monkeypatch.setenv("NRG_VECTOR_DRIFT_STATUS_FILE", str(status_file))

        write_status_file({"alert_level": "GREEN", "drift_score": 0.9})

        payload = json.loads(status_file.read_text())
        assert payload["status"] == "healthy"
        assert payload["alert_level"] == "GREEN"
        assert payload["drift_score"] == 0.9


class TestSLOThresholds:
    """Verify SLO thresholds match spec requirements."""

    def test_drift_slo_exactly_085(self):
        """Spec requires SLO drift_score >= 0.85."""
        assert DRIFT_SCORE_SLO == 0.85

    def test_cosine_shift_threshold_exactly_005(self):
        """Spec requires 1-minute detect→emit for shift > 0.05."""
        assert COSINE_SHIFT_THRESHOLD == 0.05

    def test_benchmark_queries_count(self):
        """10 benchmark queries as defined in spec."""
        assert len(BENCHMARK_QUERIES) == 10
        for q in BENCHMARK_QUERIES:
            assert "query" in q
            assert "expected_topics" in q


class TestDriftCheckRuntime:
    """Runtime guardrails for the C5 drift check."""

    def test_qdrant_unhealthy_is_not_benchmark_ready(self):
        health = {
            "status": "unhealthy",
            "indexed_vectors": 0,
            "total_vectors": 0,
        }

        assert _qdrant_ready_for_benchmark(health) is False

    def test_qdrant_empty_collection_is_not_benchmark_ready(self):
        health = {
            "status": "degraded",
            "indexed_vectors": 0,
            "total_vectors": 0,
        }

        assert _qdrant_ready_for_benchmark(health) is False

    def test_qdrant_unindexed_collection_is_not_benchmark_ready(self):
        health = {
            "status": "degraded",
            "indexed_vectors": 0,
            "total_vectors": 19322,
        }

        assert _qdrant_ready_for_benchmark(health) is False

    def test_qdrant_small_threshold_exempt_collection_is_benchmark_ready(self):
        health = {
            "status": "ok",
            "indexed_vectors": 0,
            "total_vectors": 1800,
            "index_built": True,
        }

        assert _qdrant_ready_for_benchmark(health) is True

    def test_qdrant_with_vectors_is_benchmark_ready(self):
        health = {
            "status": "degraded",
            "indexed_vectors": 50,
            "total_vectors": 100,
        }

        assert _qdrant_ready_for_benchmark(health) is True

    def test_run_drift_check_reuses_one_embedder_for_all_benchmarks(self, monkeypatch):
        """A C5 scorecard run must not reload the embedding model per query."""
        from src.skills.rag import embedder as embedder_module

        class FakeEmbedder:
            init_count = 0
            close_count = 0

            def __init__(self):
                FakeEmbedder.init_count += 1

            def embed_single(self, text):
                return [0.1, 0.2, 0.3]

            def close(self):
                FakeEmbedder.close_count += 1

        class FakeRetriever:
            def retrieve(self, query_vector, user_tier=1, top_k=5, **kwargs):
                return {
                    "metadata": [
                        {
                            "institution": "IIT Gandhinagar",
                            "topics": ["machine learning"],
                        }
                    ]
                }

        monkeypatch.setattr(embedder_module, "Embedder", FakeEmbedder)
        monkeypatch.setattr(_vdc, "_save_benchmark_cache", lambda data: None)
        monkeypatch.setattr(
            _vdc,
            "_check_cosine_shift",
            lambda drift_result, retriever, embedder: {
                "status": "stable",
                "reindex_triggered": False,
            },
        )

        result = run_drift_check(FakeRetriever())

        assert result["queries_checked"] == len(BENCHMARK_QUERIES)
        assert FakeEmbedder.init_count == 1
        assert FakeEmbedder.close_count == 1

    def test_run_drift_check_skips_cosine_when_benchmark_is_critical(self, monkeypatch):
        """Critical benchmark drift should trigger reindex without a slow centroid pass."""
        from src.skills.rag import embedder as embedder_module

        class FakeEmbedder:
            def embed_single(self, text):
                return [0.1, 0.2, 0.3]

            def close(self):
                pass

        class FakeRetriever:
            def retrieve(self, query_vector, user_tier=1, top_k=5, **kwargs):
                return {"metadata": [{"institution": "Unrelated", "topics": ["unrelated"]}]}

        triggered = []

        monkeypatch.setattr(embedder_module, "Embedder", FakeEmbedder)
        monkeypatch.setattr(_vdc, "_save_benchmark_cache", lambda data: None)
        monkeypatch.setattr(
            _vdc,
            "_check_cosine_shift",
            lambda *args, **kwargs: pytest.fail("cosine shift should be skipped on critical drift"),
        )
        monkeypatch.setattr(
            _vdc,
            "_trigger_reindex",
            lambda drift_result, reindex_info: triggered.append((drift_result, reindex_info)),
        )

        result = run_drift_check(FakeRetriever())

        assert result["alert_level"] == "CRITICAL"
        assert triggered
        assert triggered[0][1]["status"] == "benchmark_drift_detected"

    def test_run_drift_check_uses_established_baseline_cache(self, monkeypatch):
        """C5 drift should compare current retrieval to the persisted baseline."""
        from src.skills.rag import embedder as embedder_module

        class FakeEmbedder:
            def embed_single(self, text):
                return [0.1, 0.2, 0.3]

            def close(self):
                pass

        class FakeRetriever:
            def retrieve(self, query_vector, user_tier=1, top_k=5, **kwargs):
                return {
                    "metadata": [
                        {
                            "institution": "IIT Gandhinagar",
                            "topics": ["machine learning", "robotics"],
                        }
                    ]
                }

        baseline = {
            query["query"]: {
                "sources": ["iit gandhinagar"],
                "topics": ["machine learning", "robotics"],
            }
            for query in BENCHMARK_QUERIES
        }
        latest = []

        monkeypatch.setattr(embedder_module, "Embedder", FakeEmbedder)
        monkeypatch.setattr(_vdc, "_load_benchmark_cache", lambda: baseline)
        monkeypatch.setattr(
            _vdc,
            "_save_benchmark_cache",
            lambda data: pytest.fail("drift checks must not overwrite the known-good baseline"),
        )
        monkeypatch.setattr(_vdc, "_save_latest_results", lambda data: latest.append(data))
        monkeypatch.setattr(
            _vdc,
            "_check_cosine_shift",
            lambda drift_result, retriever, embedder: {
                "status": "stable",
                "reindex_triggered": False,
            },
        )

        result = run_drift_check(FakeRetriever())

        assert result["alert_level"] == "GREEN"
        assert result["drift_score"] == 1.0
        assert all(item["baseline"] == "cache" for item in result["per_query"])
        assert latest
