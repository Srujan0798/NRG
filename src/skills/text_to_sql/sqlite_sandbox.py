"""SQLite Sandbox for Text-to-SQL - Read-only execution."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
import json
from datetime import datetime, UTC

from src.audit import log_sql as audit_log_sql
from src.config.database import get_database_manager, DatabaseManager

logger = logging.getLogger(__name__)

PII_COLUMNS = {"email", "phone"}


class SQLiteSandbox:
    """Read-only sandbox for SQLite execution."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_manager = DatabaseManager(f"sqlite:///{db_path}")
        else:
            self.db_manager = get_database_manager()
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

        if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
            raise PermissionError(
                f"Only SELECT queries allowed in sandbox. Got: {sql_stripped[:50]}..."
            )

        query_id = str(uuid.uuid4())

        self._log_audit(
            {
                "query_id": query_id,
                "sql": sql,
                "user_tier": user_tier,
                "timestamp": datetime.now(UTC).isoformat(),
                "status": "executing",
            }
        )

        try:
            rows = self.db_manager.fetch_all(sql)
            columns = list(rows[0].keys()) if rows else []
            formatted_results = [dict(row) for row in rows]

            if user_tier > 1:
                columns = [column for column in columns if column.lower() not in PII_COLUMNS]
                formatted_results = [
                    {
                        key: value
                        for key, value in row.items()
                        if key.lower() not in PII_COLUMNS
                    }
                    for row in formatted_results
                ]

            self._log_audit(
                {
                    "query_id": query_id,
                    "row_count": len(formatted_results),
                    "timestamp": datetime.now(UTC).isoformat(),
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
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status": "error",
                }
            )
            raise RuntimeError(f"Sandbox execution failed: {e}") from e

    def test_connection(self) -> bool:
        """Test sandbox connectivity."""
        try:
            health = self.db_manager.health_check()
            return health.get("status") == "healthy"
        except Exception:
            return False

    def get_tables(self) -> list:
        """List available tables."""
        rows = self.db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row["name"] for row in rows]

    def close(self):
        pass
