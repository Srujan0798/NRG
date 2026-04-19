"""SQLite Sandbox for Text-to-SQL - Read-only execution."""

import sqlite3
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
import json
from datetime import datetime

from src.audit import log_sql as audit_log_sql

logger = logging.getLogger(__name__)


class SQLiteSandbox:
    """Read-only sandbox for SQLite execution."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "nrg_research.db"
        self.audit_log_path = Path(".protocol/audit_log.jsonl")
        self._ensure_audit_log()

    def _ensure_audit_log(self):
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.audit_log_path.exists():
            self.audit_log_path.write_text("")

    def _log_audit(self, entry: Dict[str, Any]):
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute_readonly(self, sql: str, user_tier: int = 1) -> Dict[str, Any]:
        """Execute SELECT query in read-only sandbox."""
        sql_stripped = sql.strip().upper()

        if not sql_stripped.startswith("SELECT"):
            raise PermissionError(
                f"Only SELECT queries allowed in sandbox. Got: {sql_stripped[:50]}..."
            )

        query_id = str(uuid.uuid4())

        self._log_audit(
            {
                "query_id": query_id,
                "sql": sql,
                "user_tier": user_tier,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "executing",
            }
        )

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            formatted_results = [dict(row) for row in rows]
            conn.close()

            self._log_audit(
                {
                    "query_id": query_id,
                    "row_count": len(formatted_results),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                }
            )

            # HMAC-chained audit log
            try:
                audit_log_sql(
                    "sqlite-sandbox",
                    sql,
                    {"row_count": len(formatted_results), "query_id": query_id},
                )
            except Exception:
                logger.warning("HMAC audit log_sql failed in sqlite sandbox", exc_info=True)

            return {
                "query": sql,
                "columns": columns,
                "results": formatted_results,
                "row_count": len(formatted_results),
            }

        except Exception as e:
            self._log_audit(
                {
                    "query_id": query_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "error",
                }
            )
            raise RuntimeError(f"Sandbox execution failed: {e}") from e

    def test_connection(self) -> bool:
        """Test sandbox connectivity."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False

    def get_tables(self) -> list:
        """List available tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def close(self):
        pass
