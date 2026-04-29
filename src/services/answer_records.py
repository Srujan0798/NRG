from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class AnswerRecordStore:
    def __init__(self, path: str | Path | None = None):
        default_path = Path(os.getenv("NRG_ANSWER_RECORDS_DB", "data/answer_records.sqlite"))
        self.path = Path(path or default_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS answer_records (
                    answer_id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    tier INTEGER,
                    audit_event_id TEXT,
                    question TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(self, *, user_id: str, session_id: str | None, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO answer_records
                (answer_id, query_id, user_id, session_id, tier, audit_event_id, question, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["answer_id"],
                    payload["query_id"],
                    user_id,
                    session_id,
                    payload.get("tier"),
                    payload.get("audit_event_id"),
                    payload.get("question", ""),
                    json.dumps(payload, default=str),
                ),
            )

    def list_for_session(self, *, user_id: str, session_id: str | None, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM answer_records
                WHERE user_id = ? AND (? IS NULL OR session_id = ?)
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, session_id, session_id, limit),
            ).fetchall()
        return [
            {
                "answer_id": row["answer_id"],
                "query_id": row["query_id"],
                "session_id": row["session_id"],
                "tier": row["tier"],
                "audit_event_id": row["audit_event_id"],
                "question": row["question"],
                "created_at": row["created_at"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]


_store: AnswerRecordStore | None = None


def get_answer_record_store() -> AnswerRecordStore:
    global _store
    if _store is None:
        _store = AnswerRecordStore()
    return _store
