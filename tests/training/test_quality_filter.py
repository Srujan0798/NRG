"""Tests for QualityFilter."""

import pytest
from src.training.quality_filter import (
    QualityFilter,
    cosine_similarity,
    regrade_pair,
    _estimate_query_embedding,
)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        assert cosine_similarity(v1, v2) == 1.0

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        assert cosine_similarity(v1, v2) == 0.0

    def test_opposite_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]
        assert cosine_similarity(v1, v2) == -1.0

    def test_empty_vector(self):
        assert cosine_similarity([], []) == 0.0
        assert cosine_similarity([1.0], []) == 0.0

    def test_partial_overlap(self):
        v1 = [1.0, 1.0, 0.0]
        v2 = [1.0, 0.0, 1.0]
        sim = cosine_similarity(v1, v2)
        assert 0.0 < sim < 1.0


class TestQueryEmbedding:
    def test_embedding_length(self):
        emb = _estimate_query_embedding("Show me researchers in Gujarat")
        assert len(emb) == 100

    def test_same_query_same_embedding(self):
        emb1 = _estimate_query_embedding("Show me researchers")
        emb2 = _estimate_query_embedding("Show me researchers")
        assert emb1 == emb2

    def test_different_queries_different_embeddings(self):
        emb1 = _estimate_query_embedding("researchers Gujarat")
        emb2 = _estimate_query_embedding("publications")
        assert emb1 != emb2

    def test_empty_query(self):
        emb = _estimate_query_embedding("")
        assert len(emb) == 100
        assert all(v == 0.0 for v in emb)


class TestQualityFilter:
    @pytest.fixture
    def qf(self):
        return QualityFilter(similarity_threshold=0.95)

    def test_grade_gold(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.9,
            "latency_ms": 500,
            "sql_row_count": 10,
            "response": "A" * 200,
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "gold"

    def test_grade_silver(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.6,
            "latency_ms": 100,
            "sql_row_count": 5,
            "response": "A" * 150,
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "silver"

    def test_grade_bronze(self, qf):
        pair = {
            "route": "rag",
            "verifier_score": 0.1,
            "latency_ms": 1000,
            "response": "This is a reasonable bronze response.",
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "bronze"

    def test_grade_reject_empty_response(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.9,
            "latency_ms": 500,
            "sql_row_count": 10,
            "response": "",
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "reject"

    def test_grade_reject_sql_error(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.5,
            "sql_result": "ERROR: table not found",
            "response": "A" * 200,
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "reject"

    def test_grade_reject_pii_not_scrubbed(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.9,
            "response": "A" * 200,
            "pii_scrubbed": False,
            "citations": [],
        }
        assert qf.grade_pair(pair) == "reject"

    def test_grade_reject_sql_no_rows_short_response(self, qf):
        pair = {
            "route": "text_to_sql",
            "verifier_score": 0.9,
            "latency_ms": 500,
            "sql_row_count": 0,
            "response": "No results",
            "citations": [],
            "pii_scrubbed": True,
        }
        assert qf.grade_pair(pair) == "reject"

    def test_filter_pairs_dedup(self, qf):
        pairs = [
            {
                "id": "p1",
                "query": "List all robotics researchers working in Gujarat",
                "route": "text_to_sql",
                "verifier_score": 0.9,
                "latency_ms": 500,
                "sql_row_count": 10,
                "response": "A" * 200,
                "citations": [],
                "pii_scrubbed": True,
            },
            {
                "id": "p2",
                "query": "List all robotics researchers working in Gujarat",
                "route": "text_to_sql",
                "verifier_score": 0.9,
                "latency_ms": 500,
                "sql_row_count": 10,
                "response": "A" * 200,
                "citations": [],
                "pii_scrubbed": True,
            },
            {
                "id": "p3",
                "query": "What machine learning papers were published in 2023",
                "route": "text_to_sql",
                "verifier_score": 0.9,
                "latency_ms": 500,
                "sql_row_count": 10,
                "response": "A" * 200,
                "citations": [],
                "pii_scrubbed": True,
            },
        ]
        filtered, stats = qf.filter_pairs(pairs)
        assert len(filtered) == 2
        assert stats["dedup_removed"] == 1

    def test_filter_pairs_all_reject(self, qf):
        pairs = [
            {
                "id": "r1",
                "query": "Bad query with malformed request and broken intent",
                "route": "text_to_sql",
                "verifier_score": 0.0,
                "sql_row_count": 0,
                "response": "",
                "citations": [],
                "pii_scrubbed": True,
            }
        ]
        filtered, stats = qf.filter_pairs(pairs)
        assert len(filtered) == 0
        assert stats["reject"] == 1

    def test_filter_batch(self, qf):
        pairs = [
            {
                "id": "b1",
                "query": "Show me gold standard research in robotics",
                "route": "text_to_sql",
                "verifier_score": 0.9,
                "latency_ms": 500,
                "sql_row_count": 10,
                "response": "A" * 200,
                "citations": [],
                "pii_scrubbed": True,
            }
        ]
        filtered = qf.filter_batch(pairs)
        assert len(filtered) == 1

    def test_get_export_grade_filter(self, qf):
        result = qf.get_export_grade_filter("silver")
        assert result == {"gold", "silver"}

    def test_get_export_grade_filter_gold_only(self, qf):
        result = qf.get_export_grade_filter("gold")
        assert result == {"gold"}


class TestRegradePair:
    def test_regrade_gold(self):
        assert regrade_pair(0.9, 500, 5, 200, "text_to_sql") == "gold"

    def test_regrade_silver(self):
        assert regrade_pair(0.6, 100, 0, 150, "rag") == "silver"

    def test_regrade_bronze(self):
        assert regrade_pair(0.1, 100, 0, 50, "rag") == "bronze"

    def test_regrade_reject(self):
        assert regrade_pair(0.0, 100, 0, 0, "text_to_sql") == "reject"

    def test_regrade_sql_no_rows_reject(self):
        assert regrade_pair(0.9, 500, 0, 200, "text_to_sql") == "reject"
