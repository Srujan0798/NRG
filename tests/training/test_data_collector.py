"""Tests for TrainingDataCollector."""

import json
import pytest
from pathlib import Path

from src.training.data_collector import (
    TrainingDataCollector,
    _scrub_pii,
    _scrub_dict_pii,
)


class TestPIIHandling:
    """PII scrubbing tests."""

    def test_scrub_email(self):
        assert _scrub_pii("contact john.doe@example.com here") == "contact [EMAIL_REDACTED] here"

    def test_scrub_phone(self):
        assert _scrub_pii("call 9876543210") == "call [PHONE_REDACTED]"
        assert "[PHONE_REDACTED]" in _scrub_pii("call +91 9876543210")

    def test_scrub_aadhaar(self):
        assert _scrub_pii("aadhaar 1234-5678-9012") == "aadhaar [AADHAAR_REDACTED]"
        assert _scrub_pii("aadhaar 123456789012") == "aadhaar [AADHAAR_REDACTED]"

    def test_scrub_pan(self):
        assert _scrub_pii("pan ABCDE1234F") == "pan [PAN_REDACTED]"

    def test_scrub_dict(self):
        data = {"email": "test@example.com", "phone": "9876543210"}
        result = _scrub_dict_pii(data)
        assert result["email"] == "[EMAIL_REDACTED]"
        assert result["phone"] == "[PHONE_REDACTED]"

    def test_scrub_nested_dict(self):
        data = {"user": {"email": "test@example.com"}, "phone": "9876543210"}
        result = _scrub_dict_pii(data)
        assert result["user"]["email"] == "[EMAIL_REDACTED]"
        assert result["phone"] == "[PHONE_REDACTED]"

    def test_scrub_list(self):
        data = ["test@example.com", "9876543210"]
        result = _scrub_dict_pii(data)
        assert result == ["[EMAIL_REDACTED]", "[PHONE_REDACTED]"]

    def test_scrub_none(self):
        assert _scrub_dict_pii(None) is None

    def test_scrub_empty(self):
        assert _scrub_pii("") == ""
        assert _scrub_pii(None) is None


class TestTrainingDataCollector:
    """TrainingDataCollector tests."""

    @pytest.fixture
    def collector(self, tmp_path):
        db = tmp_path / "training_test.db"
        return TrainingDataCollector(db_path=str(db))

    def test_singleton(self):
        inst1 = TrainingDataCollector.get_instance()
        inst2 = TrainingDataCollector.get_instance()
        assert inst1 is inst2

    def test_capture_creates_record(self, collector):
        state = {
            "query_id": "test-q1",
            "user_query": "Show me researchers in Gujarat",
            "routing_decision": "structured",
            "intent": "structured",
            "user_tier": 2,
            "execution_time_ms": {"total": 150},
            "sql_query": "SELECT * FROM researchers WHERE state='Gujarat'",
            "sql_results": [{"id": 1, "name": "Dr. Test"}],
            "synthesized_response": "Here are the researchers you asked about.",
            "citations": [],
            "faithfulness_score": 0.85,
            "synthesis_method": "sql_synthesis",
            "session_id": "sess-1",
        }
        pair_id = collector.capture(state, user_id="user-1")
        assert pair_id is not None

        stats = collector.get_stats()
        assert stats["total_pairs"] == 1
        assert stats["by_grade"]["gold"] == 1

    def test_capture_grades_sql_no_rows_reject(self, collector):
        state = {
            "query_id": "test-q2",
            "user_query": "Show empty result",
            "routing_decision": "structured",
            "user_tier": 1,
            "execution_time_ms": {"total": 100},
            "sql_query": "SELECT * FROM empty_table",
            "sql_results": [],
            "synthesized_response": "No results found.",
            "citations": [],
            "faithfulness_score": 0.9,
            "synthesis_method": "sql_synthesis",
        }
        pair_id = collector.capture(state)
        assert pair_id is not None
        stats = collector.get_stats()
        assert stats["by_grade"]["reject"] == 1

    def test_capture_routes_normalized(self, collector):
        state = {
            "query_id": "test-q3",
            "user_query": "Test query",
            "intent": "unstructured",
            "user_tier": 1,
            "execution_time_ms": {"total": 50},
            "synthesized_response": "A" * 200,
            "faithfulness_score": 0.6,
            "citations": [],
        }
        pair_id = collector.capture(state)
        assert pair_id is not None

        pairs = collector.get_training_pairs()
        assert any(p["route"] == "rag" for p in pairs)

    def test_update_feedback(self, collector):
        state = {
            "query_id": "test-q4",
            "user_query": "Test feedback",
            "user_tier": 1,
            "execution_time_ms": {"total": 50},
            "synthesized_response": "A" * 50,
            "faithfulness_score": 0.7,
            "citations": [],
        }
        collector.capture(state)
        result = collector.update_feedback("test-q4", score=5, feedback_text="Great response!")
        assert result is True

        pairs = collector.get_training_pairs()
        rated = [p for p in pairs if p["id"] == "test-q4"]
        assert len(rated) == 1
        assert rated[0]["feedback_score"] == 5

    def test_get_stats(self, collector):
        for i in range(3):
            collector.capture({
                "query_id": f"stats-q{i}",
                "user_query": f"Query {i}",
                "user_tier": 1,
                "execution_time_ms": {"total": 50},
                "synthesized_response": "A" * 50,
                "faithfulness_score": 0.7,
                "citations": [],
            })
        stats = collector.get_stats()
        assert stats["total_pairs"] == 3
        assert stats["with_user_feedback"] == 0

    def test_mark_exported(self, collector):
        collector.capture({
            "query_id": "export-q1",
            "user_query": "Export test",
            "user_tier": 1,
            "execution_time_ms": {"total": 50},
            "synthesized_response": "A" * 50,
            "faithfulness_score": 0.7,
            "citations": [],
        })
        marked = collector.mark_exported(["export-q1"], "v1.0")
        assert marked == 1

        pairs = collector.get_training_pairs()
        exported = [p for p in pairs if p["exported"] == 1]
        assert len(exported) == 1

    def test_get_training_pairs_grade_filter(self, collector):
        for i in range(5):
            collector.capture({
                "query_id": f"grade-q{i}",
                "user_query": f"Query {i}",
                "user_tier": 1,
                "execution_time_ms": {"total": 50 if i % 2 == 0 else 5000},
                "synthesized_response": "A" * 200,
                "faithfulness_score": 0.9 if i % 2 == 0 else 0.3,
                "sql_results": [{"id": i}] if i % 2 == 0 else [],
                "citations": [],
                "routing_decision": "structured",
            })
        pairs = collector.get_training_pairs(min_grade="gold")
        assert all(p["quality_grade"] in ("gold",) for p in pairs)

    def test_capture_async_does_not_raise(self, collector):
        state = {
            "query_id": "async-q1",
            "user_query": "Async test",
            "user_tier": 1,
            "execution_time_ms": {"total": 50},
            "synthesized_response": "A" * 50,
            "faithfulness_score": 0.7,
            "citations": [],
        }
        collector.capture_async(state)
        import time
        time.sleep(0.2)
        stats = collector.get_stats()
        assert stats["total_pairs"] == 1

    def test_capture_stores_training_pair(self, collector, tmp_path):
        state = {
            "query_id": "store-q1",
            "user_query": "Show me researchers in Karnataka",
            "routing_decision": "structured",
            "user_tier": 1,
            "execution_time_ms": {"total": 150},
            "sql_query": "SELECT * FROM researchers WHERE state='KA'",
            "sql_results": [{"id": 1, "name": "Dr. Test", "email": "test@example.com"}],
            "synthesized_response": "Here are researchers in Karnataka.",
            "citations": [],
            "faithfulness_score": 0.85,
            "synthesis_method": "sql_synthesis",
            "session_id": "sess-store",
        }
        pair_id = collector.capture(state, user_id="user-test")

        import sqlite3
        conn = sqlite3.connect(tmp_path / "training_test.db")
        cur = conn.execute("SELECT id, query, route, quality_grade, pii_scrubbed FROM training_pairs WHERE id = ?", (pair_id,))
        row = cur.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == pair_id
        assert "Karnataka" in row[1]
        assert row[2] == "text_to_sql"
        assert row[3] == "gold"
        assert row[4] == 1

    def test_capture_async_is_fire_and_forget(self, collector, tmp_path):
        import time
        from src.training.data_collector import TrainingDataCollector

        db_path = tmp_path / "async_fire_test.db"
        coll = TrainingDataCollector(db_path=str(db_path))

        state = {
            "query_id": "async-fire-q1",
            "user_query": "Async fire and forget test",
            "user_tier": 1,
            "execution_time_ms": {"total": 50},
            "synthesized_response": "A" * 50,
            "faithfulness_score": 0.7,
            "citations": [],
        }

        start = time.perf_counter()
        coll.capture_async(state)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05

        import time as time_module
        time_module.sleep(0.5)

        stats = coll.get_stats()
        assert stats["total_pairs"] == 1

    def test_get_training_pairs_filters_by_grade(self, collector):
        test_cases = [
            ("gold-q1", 0.9, 500, [{"id": 1}], "text_to_sql"),
            ("gold-q2", 0.85, 400, [{"id": 2}], "text_to_sql"),
            ("silver-q1", 0.6, 1000, [], "rag"),
            ("bronze-q1", 0.2, 2000, [], "rag"),
            ("reject-q1", 0.1, 100, [], "text_to_sql"),
        ]
        for query_id, score, latency, sql_results, route in test_cases:
            collector.capture({
                "query_id": query_id,
                "user_query": f"Query {query_id}",
                "routing_decision": route,
                "user_tier": 1,
                "execution_time_ms": {"total": latency},
                "sql_results": sql_results,
                "synthesized_response": "A" * 200 if score > 0.5 else "short",
                "faithfulness_score": score,
                "citations": [],
            })

        gold_pairs = collector.get_training_pairs(min_grade="gold")
        assert all(p["quality_grade"] == "gold" for p in gold_pairs)
        assert len(gold_pairs) == 2

        silver_plus = collector.get_training_pairs(min_grade="silver")
        grades = {p["quality_grade"] for p in silver_plus}
        assert grades <= {"gold", "silver"}

    def test_quality_filter_grades_correctly(self, collector):
        states = [
            ("qf-gold", 0.9, 500, [{"id": 1}], "text_to_sql", "gold"),
            ("qf-silver", 0.6, 100, [], "rag", "silver"),
            ("qf-bronze", 0.2, 5000, [], "rag", "bronze"),
            ("qf-reject", 0.1, 100, [], "text_to_sql", "reject"),
        ]
        for query_id, score, latency, sql_results, route, expected_grade in states:
            collector.capture({
                "query_id": query_id,
                "user_query": f"Query {query_id}",
                "routing_decision": route,
                "user_tier": 1,
                "execution_time_ms": {"total": latency},
                "sql_results": sql_results,
                "synthesized_response": "A" * 200 if len(sql_results) > 0 or score > 0.5 else "short",
                "faithfulness_score": score,
                "citations": [],
            })

        pairs = collector.get_training_pairs(min_grade="bronze")
        grades = {p["quality_grade"] for p in pairs if p["id"].startswith("qf-")}
        assert "gold" in grades
        assert "silver" in grades
        assert "bronze" in grades
        assert "reject" not in grades

    def test_export_produces_valid_jsonl(self, tmp_path):
        from src.training.data_collector import TrainingDataCollector

        db_path = tmp_path / "export_test.db"
        collector = TrainingDataCollector(db_path=str(db_path))

        queries = [
            {"query_id": "export-jsonl-0", "user_query": "Find robotics researchers in Gujarat state", "synthesized_response": "Robotics researchers: Dr. Test, Dr. Demo, Dr. Sample"},
            {"query_id": "export-jsonl-1", "user_query": "Show publications from Indian institutions in 2023", "synthesized_response": "Publications 2023: Paper Alpha, Paper Beta, Paper Gamma"},
            {"query_id": "export-jsonl-2", "user_query": "List AI research projects funded by government grants", "synthesized_response": "Government AI projects: Project X, Project Y, Project Z"},
        ]

        for item in queries:
            collector.capture({
                "query_id": item["query_id"],
                "user_query": item["user_query"],
                "routing_decision": "structured",
                "user_tier": 1,
                "execution_time_ms": {"total": 100},
                "sql_query": "SELECT * FROM test",
                "sql_results": [{"id": 1}],
                "synthesized_response": item["synthesized_response"],
                "faithfulness_score": 0.85,
                "synthesis_method": "sql_synthesis",
                "citations": [],
            })

        from src.training.export import ExportPipeline
        output_dir = tmp_path / "exports"
        pipeline = ExportPipeline(output_dir=output_dir, min_grade="bronze")
        pipeline.collector = collector
        stats = pipeline.export(fmt="jsonl", dry_run=False)

        assert stats["pairs_exported"] == 3
        output_file = Path(output_dir) / f"{stats['version']}_jsonl.jsonl"
        assert output_file.exists()

        with output_file.open() as f:
            lines = f.readlines()
        assert len(lines) == 3
        for line in lines:
            parsed = json.loads(line)
            assert "instruction" in parsed or "conversations" in parsed

    def test_pii_scrubbing_no_raw_pii_in_stored_pairs(self, collector):
        pii_test_cases = [
            ("pii-email-1", "Contact john.doe@example.com for details"),
            ("pii-phone-1", "Call 9876543210 for support"),
            ("pii-aadhaar-1", "Aadhaar 1234-5678-9012 verified"),
            ("pii-pan-1", "PAN ABCDE1234F submitted"),
            ("pii-mixed-1", "Email test@example.com and phone +91 9876543210"),
        ]
        for query_id, query in pii_test_cases:
            collector.capture({
                "query_id": query_id,
                "user_query": query,
                "user_tier": 1,
                "execution_time_ms": {"total": 50},
                "synthesized_response": "Response with test@example.com and 9876543210",
                "faithfulness_score": 0.7,
                "citations": [],
            })

        pairs = collector.get_training_pairs(min_grade="bronze")
        pii_patterns = [
            "john.doe@example.com", "test@example.com",
            "9876543210", "+91 9876543210",
            "1234-5678-9012", "ABCDE1234F",
        ]
        for pair in pairs:
            if pair["id"].startswith("pii-"):
                combined = str(pair.values())
                for pii in pii_patterns:
                    assert pii not in combined, f"Raw PII found in pair {pair['id']}: {pii}"
