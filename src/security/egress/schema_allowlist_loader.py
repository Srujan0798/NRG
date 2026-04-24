"""Schema allowlist loader - Protocol #39: Schema Allowlist.

Loads egress_allowlist.yaml and provides methods to check table/column access.
File-mtime caching enables hot-reload without restart.
"""

from pathlib import Path
from typing import Optional
import yaml
import os

PATH = Path(__file__).resolve().parents[1] / "egress_allowlist.yaml"


class EgressSchemaAllowlist:
    """Singleton allowlist loaded from egress_allowlist.yaml."""

    _instance: Optional["EgressSchemaAllowlist"] = None
    _cache: dict = {}
    _mtime: float = 0

    def __new__(cls) -> "EgressSchemaAllowlist":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load(self) -> dict:
        """Load YAML, hot-reloading if file mtime changed."""
        try:
            current_mtime = os.path.getmtime(PATH)
        except OSError:
            current_mtime = 0

        if current_mtime != self._mtime or not self._cache:
            with open(PATH, "r") as f:
                self._cache = yaml.safe_load(f) or {}
            self._mtime = current_mtime

        return self._cache

    def is_table_allowed(self, table: str) -> bool:
        """Check if table is allowlisted for egress."""
        data = self._load()
        return table in (data.get("tables") or {})

    def is_column_allowed(self, table: str, column: str) -> bool:
        """Check if column is allowed for given table."""
        data = self._load()
        tables = data.get("tables") or {}
        table_data = tables.get(table, {})
        allowlisted = table_data.get("allowlisted_columns") or []
        return column in allowlisted

    def get_blocked_content(self) -> frozenset:
        """Get set of field names that are never allowed to egress."""
        data = self._load()
        blocked = data.get("blocked_content") or []
        return frozenset(blocked)

    def is_llm_prompt_allowed(self, field_name: str) -> bool:
        """Check if a prompt field name is allowed for LLM egress."""
        data = self._load()
        llm_prompts = data.get("llm_prompts") or {}
        return bool(llm_prompts.get(field_name))

    def get_allowed_tables(self) -> frozenset:
        """Get all allowlisted table names."""
        data = self._load()
        return frozenset((data.get("tables") or {}).keys())

    def get_table_columns(self, table: str) -> tuple[list[str], list[str]]:
        """Get (allowlisted_columns, blocked_columns) for a table."""
        data = self._load()
        tables = data.get("tables") or {}
        table_data = tables.get(table, {})
        return (
            table_data.get("allowlisted_columns") or [],
            table_data.get("blocked_columns") or [],
        )

    def is_blocked_column_name(self, column_name: str) -> bool:
        """Check if column name appears in any table's blocked_columns list."""
        data = self._load()
        tables = data.get("tables") or {}
        for table_data in tables.values():
            if column_name in (table_data.get("blocked_columns") or []):
                return True
        return False


def get_allowlist() -> EgressSchemaAllowlist:
    """Get singleton allowlist instance."""
    return EgressSchemaAllowlist()