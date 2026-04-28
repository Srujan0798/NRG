"""Text-to-SQL Sandbox - Read-only database execution."""

import os
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pathlib import Path
import uuid
import json

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError

from src.audit import log_sql as audit_log_sql
from src.config.database import register_sqlite_compat_functions, resolve_runtime_database_url


logger = logging.getLogger(__name__)


_MUTATING_SQL_PATTERN = re.compile(
    r"\b(ALTER|CALL|COPY|CREATE|DELETE|DROP|GRANT|INSERT|MERGE|REVOKE|TRUNCATE|UPDATE)\b",
    re.IGNORECASE,
)


class Sandbox:
    """Read-only sandbox for SQL execution."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string: str = connection_string or _default_connection_string()
        self.engine = create_engine(
            self.connection_string, echo=False, pool_pre_ping=True
        )
        if getattr(getattr(self.engine, "dialect", None), "name", None) == "sqlite":
            event.listen(self.engine, "connect", self._register_sqlite_functions)
        protocol_dir = Path(os.environ.get("NRG_PROTOCOL_DIR", ".protocol"))
        self.audit_log_path = protocol_dir / "audit_log.jsonl"
        self._ensure_audit_log()

    @staticmethod
    def _register_sqlite_functions(dbapi_connection: Any, _connection_record: Any) -> None:
        register_sqlite_compat_functions(dbapi_connection)

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

        Only read-only SELECT/CTE statements are allowed.
        Raises PermissionError for mutating statements.
        """
        sql_compact = re.sub(r"\s+", " ", sql.strip())
        sql_upper = sql_compact.upper()

        starts_readonly = sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")
        if not starts_readonly or _MUTATING_SQL_PATTERN.search(sql_compact):
            raise PermissionError(
                f"Only read-only SELECT queries allowed in sandbox. Got: {sql_upper[:50]}..."
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
                        "timestamp": datetime.now(UTC).isoformat(),
                        "status": "success",
                    }
                )

                # HMAC-chained audit log
                try:
                    audit_log_sql(
                        "sandbox",
                        sql,
                        {"row_count": len(formatted_results), "query_id": query_id},
                    )
                except Exception:
                    logger.warning("HMAC audit log_sql failed in sandbox", exc_info=True)

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
                "timestamp": datetime.now(UTC).isoformat(),
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
        dialect_name = getattr(getattr(self.engine, "dialect", None), "name", "sqlite")
        with self.engine.connect() as conn:
            if dialect_name == "sqlite":
                result = conn.execute(
                    text(
                        "SELECT name AS table_name FROM sqlite_master "
                        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                )
            else:
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            return [row[0] for row in result.fetchall()]

    def close(self):
        self.engine.dispose()


def _default_connection_string() -> str:
    """Prefer DATABASE_URL; otherwise use the dev SQLite file."""
    database_url = resolve_runtime_database_url((os.getenv("DATABASE_URL") or "").strip())
    if database_url:
        return database_url
    return "sqlite:///src/data/nrg_research.db"


def execute_sql(
    sql: str,
    user_tier: int = 1,
    connection_string: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience helper used by scripts/tests for one-shot read-only SQL."""
    sandbox = Sandbox(connection_string=connection_string)
    try:
        return sandbox.execute_readonly(sql, user_tier=user_tier)
    finally:
        sandbox.close()
