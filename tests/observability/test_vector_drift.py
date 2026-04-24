"""Tests for Vector Drift Monitor — C5: Auto-Retrain Trigger."""

from unittest.mock import patch, MagicMock
import importlib.util
import sys
from pathlib import Path

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
