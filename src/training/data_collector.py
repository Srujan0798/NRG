"""
Training Data Collector — Task #22 Phase 1
Captures every query→SQL→result→feedback tuple from the NRG pipeline.
Non-blocking, async fire-and-forget — must NOT slow down user responses.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.orchestration.state import NRGState

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="training_collector")
_PII_PATTERNS = None


def _get_pii_patterns():
    """Lazy-load PII patterns for scrubbing."""
    global _PII_PATTERNS
    if _PII_PATTERNS is None:
        import re
        _PII_PATTERNS = [
            (re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"), "[AADHAAR_REDACTED]"),
            (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"), "[PAN_REDACTED]"),
            (re.compile(r"\b[6-9][0-9]{9}\b"), "[PHONE_REDACTED]"),
            (re.compile(r"\+91[- ]?[6-9][0-9]{9}\b"), "[PHONE_REDACTED]"),
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
        ]
    return _PII_PATTERNS


def _scrub_pii(text: str) -> str:
    """Remove PII from text for safe storage in training data."""
    if not text:
        return text
    result = str(text)
    for pattern, placeholder in _get_pii_patterns():
        result = pattern.sub(placeholder, result)
    return result


def _scrub_dict_pii(data: dict) -> dict:
    """Recursively scrub PII from a dict (safe copy)."""
    if data is None:
        return None
    if isinstance(data, dict):
        return {k: _scrub_dict_pii(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_scrub_dict_pii(item) for item in data]
    if isinstance(data, str):
        return _scrub_pii(data)
    return data


class TrainingDataCollector:
    """Collects and stores training pairs from the NRG pipeline.

    Captures (query, SQL, result, quality_score) for SQL tuning,
    (query, chunks, answer, citations) for RAG tuning,
    and (query, final_response, user_feedback) for RLHF alignment.

    All storage is async and non-blocking.
    """

    _instance: "TrainingDataCollector | None" = None
    _lock = threading.Lock()

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("TRAINING_DATA_DB", ".training_data.db")
        self._ensure_schema()

    @classmethod
    def get_instance(cls) -> "TrainingDataCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _ensure_schema(self) -> None:
        """Create the training_pairs table if it doesn't exist."""
        schema_sql = Path(__file__).parent.parent.parent / "db" / "training_pairs.sql"
        if schema_sql.exists():
            sql = schema_sql.read_text()
        else:
            sql = """
            CREATE TABLE IF NOT EXISTS training_pairs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                tier INTEGER NOT NULL,
                route TEXT NOT NULL,
                sql_generated TEXT,
                sql_result TEXT,
                sql_row_count INTEGER DEFAULT 0,
                chunks_retrieved INTEGER DEFAULT 0,
                chunk_ids TEXT,
                similarity_scores TEXT,
                response TEXT,
                citations TEXT,
                synthesis_method TEXT,
                verifier_score REAL DEFAULT 0.0,
                latency_ms INTEGER DEFAULT 0,
                quality_grade TEXT DEFAULT 'ungraded',
                feedback_score INTEGER DEFAULT NULL,
                feedback_text TEXT DEFAULT NULL,
                exported BOOLEAN DEFAULT FALSE,
                exported_at TEXT DEFAULT NULL,
                export_version TEXT DEFAULT NULL,
                pii_scrubbed BOOLEAN DEFAULT FALSE,
                session_id TEXT,
                user_id TEXT,
                node_timings TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tp_tier ON training_pairs(tier);
            CREATE INDEX IF NOT EXISTS idx_tp_route ON training_pairs(route);
            CREATE INDEX IF NOT EXISTS idx_tp_grade ON training_pairs(quality_grade);
            """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _grade_pair(
        self,
        verifier_score: float,
        sql_row_count: int,
        latency_ms: float,
        response_length: int,
        route: str,
    ) -> str:
        """Grade a training pair as GOLD/SILVER/BRONZE/REJECT."""
        if route == "text_to_sql" and sql_row_count == 0:
            return "reject"
        if verifier_score > 0.8 and latency_ms < 5000 and sql_row_count > 0:
            return "gold"
        if verifier_score > 0.5 and response_length > 100:
            return "silver"
        if verifier_score > 0 or response_length > 0:
            return "bronze"
        return "reject"

    def capture(self, state: "NRGState | dict", user_id: str = None) -> str:
        """Capture a training pair from NRGState. Returns the pair ID."""
        if state is None:
            return None

        if hasattr(state, "to_dict"):
            s = state.to_dict()
        else:
            s = dict(state)

        pair_id = s.get("query_id") or str(uuid.uuid4())[:12]
        timestamp = datetime.now(UTC).isoformat()

        query = _scrub_pii(s.get("user_query", ""))
        route = s.get("routing_decision") or s.get("intent") or "unknown"
        if route in ("structured", "unstructured", "hybrid"):
            route_map = {"structured": "text_to_sql", "unstructured": "rag", "hybrid": "hybrid"}
            route = route_map.get(route, route)

        tier = s.get("user_tier", 1)
        lat_ms = int(s.get("execution_time_ms", {}).get("total", 0) or 0)

        sql_gen = s.get("sql_query")
        sql_results_raw = s.get("sql_results", [])
        sql_row_count = len(sql_results_raw) if sql_results_raw else 0
        sql_result_str = _scrub_dict_pii(
            json.dumps(sql_results_raw[:100], default=str) if sql_results_raw else ""
        )
        sql_gen_scrubbed = _scrub_pii(sql_gen) if sql_gen else None

        chunks = s.get("retrieved_chunks", [])
        chunk_ids = json.dumps([c.get("chunk_id", str(i)) for i, c in enumerate(chunks)]) if chunks else "[]"
        sim_scores = json.dumps([c.get("score", 0.0) for c in chunks]) if chunks else "[]"

        response_raw = s.get("synthesized_response", "")
        response = _scrub_pii(response_raw) if response_raw else ""
        citations_raw = s.get("citations", [])
        citations = json.dumps(citations_raw, default=str) if citations_raw else "[]"

        verifier_score = float(s.get("faithfulness_score", 0.0) or 0.0)
        synthesis_method = s.get("synthesis_method", "unknown")

        node_timings = json.dumps(s.get("node_timings", {}), default=str)
        session_id = s.get("session_id")

        quality_grade = self._grade_pair(
            verifier_score=verifier_score,
            sql_row_count=sql_row_count,
            latency_ms=lat_ms,
            response_length=len(response),
            route=route,
        )

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO training_pairs (
                    id, timestamp, query, tier, route,
                    sql_generated, sql_result, sql_row_count,
                    chunks_retrieved, chunk_ids, similarity_scores,
                    response, citations, synthesis_method,
                    verifier_score, latency_ms, quality_grade,
                    session_id, user_id, node_timings, pii_scrubbed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pair_id,
                    timestamp,
                    query,
                    tier,
                    route,
                    sql_gen_scrubbed,
                    sql_result_str,
                    sql_row_count,
                    len(chunks) if chunks else 0,
                    chunk_ids,
                    sim_scores,
                    response,
                    citations,
                    synthesis_method,
                    verifier_score,
                    lat_ms,
                    quality_grade,
                    session_id,
                    user_id,
                    node_timings,
                    True,
                ),
            )
            conn.commit()
            logger.info(f"Training pair captured: {pair_id} grade={quality_grade}")
            return pair_id
        except Exception as e:
            logger.error(f"Failed to capture training pair: {e}")
            return None
        finally:
            conn.close()

    def capture_async(self, state: "NRGState | dict", user_id: str = None) -> None:
        """Fire-and-forget async capture — does NOT block the response."""
        _EXECUTOR.submit(self.capture, state, user_id)

    def update_feedback(
        self,
        query_id: str,
        score: int | None = None,
        feedback_text: str | None = None,
    ) -> bool:
        """Update a training pair with user feedback (RLHF signal)."""
        if not query_id:
            return False
        conn = self._get_connection()
        try:
            if score is not None:
                conn.execute(
                    "UPDATE training_pairs SET feedback_score = ?, feedback_text = ? WHERE id = ?",
                    (score, _scrub_pii(feedback_text or ""), query_id),
                )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update feedback for {query_id}: {e}")
            return False
        finally:
            conn.close()

    def get_stats(self) -> dict:
        """Return training data statistics for /api/metrics dashboard."""
        conn = self._get_connection()
        try:
            cur = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN quality_grade = 'gold' THEN 1 ELSE 0 END) as gold,
                    SUM(CASE WHEN quality_grade = 'silver' THEN 1 ELSE 0 END) as silver,
                    SUM(CASE WHEN quality_grade = 'bronze' THEN 1 ELSE 0 END) as bronze,
                    SUM(CASE WHEN quality_grade = 'reject' THEN 1 ELSE 0 END) as reject,
                    SUM(CASE WHEN quality_grade = 'ungraded' THEN 1 ELSE 0 END) as ungraded,
                    SUM(CASE WHEN feedback_score IS NOT NULL THEN 1 ELSE 0 END) as with_feedback,
                    AVG(feedback_score) as avg_feedback,
                    SUM(CASE WHEN exported = 1 THEN 1 ELSE 0 END) as exported
                FROM training_pairs
                """
            )
            row = cur.fetchone()
            return {
                "total_pairs": row[0] or 0,
                "by_grade": {
                    "gold": row[1] or 0,
                    "silver": row[2] or 0,
                    "bronze": row[3] or 0,
                    "reject": row[4] or 0,
                    "ungraded": row[5] or 0,
                },
                "with_user_feedback": row[6] or 0,
                "avg_feedback_score": round(row[7] or 0.0, 2),
                "exported_pairs": row[8] or 0,
            }
        finally:
            conn.close()

    def get_training_pairs(
        self,
        min_grade: str = "bronze",
        limit: int = 10000,
        route: str | None = None,
    ) -> list[dict]:
        """Retrieve training pairs for export."""
        grade_order = {"gold": 0, "silver": 1, "bronze": 2, "reject": 3, "ungraded": 4}
        min_rank = grade_order.get(min_grade, 2)

        conn = self._get_connection()
        try:
            query = "SELECT * FROM training_pairs WHERE quality_grade IN ({})".format(
                ",".join(f"'{g}'" for g, r in grade_order.items() if r <= min_rank)
            )
            if route:
                query += f" AND route = '{route}'"
            query += f" ORDER BY quality_grade, timestamp DESC LIMIT {limit}"

            cur = conn.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()

    def mark_exported(self, pair_ids: list[str], version: str) -> int:
        """Mark pairs as exported with version tag."""
        if not pair_ids:
            return 0
        conn = self._get_connection()
        try:
            placeholders = ",".join("?" * len(pair_ids))
            conn.execute(
                f"UPDATE training_pairs SET exported = 1, exported_at = ?, export_version = ? "
                f"WHERE id IN ({placeholders})",
                [datetime.now(UTC).isoformat(), version] + list(pair_ids),
            )
            conn.commit()
            return len(pair_ids)
        finally:
            conn.close()


_collector_instance: TrainingDataCollector | None = None


def get_training_collector() -> TrainingDataCollector:
    """Get singleton training data collector."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = TrainingDataCollector()
    return _collector_instance
