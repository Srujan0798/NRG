"""Text-to-SQL Sandbox - Read-only database execution."""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid
import json

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class Sandbox:
    """Read-only sandbox for SQL execution."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://nrg:nrg_secret@localhost:5432/nrg",
        )
        self.engine = create_engine(
            self.connection_string, echo=False, pool_pre_ping=True
        )
        self.audit_log_path = Path(".protocol/audit_log.jsonl")
        self._ensure_audit_log()

    def _ensure_audit_log(self):
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.audit_log_path.exists():
            self.audit_log_path.write_text("")

    def _log_audit(self, entry: Dict[str, Any]):
        """Append audit log entry."""
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute_readonly(self, sql: str, user_tier: int = 1) -> Dict[str, Any]:
        """
        Execute SELECT query in read-only sandbox.

        Only SELECT allowed - INSERT/UPDATE/DELETE blocked.
        Raises PermissionError for non-SELECT statements.
        """
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
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()

                columns = result.keys() if hasattr(result, "keys") else []
                if not columns and rows:
                    columns = list(rows[0]._keys) if hasattr(rows[0], "_keys") else []

                formatted_results = [
                    dict(zip(columns, row))
                    if hasattr(row, "_keys")
                    else dict(zip(columns, row))
                    for row in rows
                ]

                self._log_audit(
                    {
                        "query_id": query_id,
                        "row_count": len(formatted_results),
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "success",
                    }
                )

                return {
                    "query": sql,
                    "columns": columns,
                    "results": formatted_results,
                    "row_count": len(formatted_results),
                }

        except SQLAlchemyError as e:
            error_entry = {
                "query_id": query_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
            }
            self._log_audit(error_entry)
            raise RuntimeError(f"Sandbox execution failed: {e}") from e

    def test_connection(self) -> bool:
        """Test sandbox connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_tables(self) -> List[str]:
        """List available tables."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            return [row[0] for row in result.fetchall()]

    def close(self):
        self.engine.dispose()
