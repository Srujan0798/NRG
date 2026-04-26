"""Add LB-6 hot-path indexes, TRL view, and tier row policies.

Revision ID: lb6_indexes_rls_001
Revises: llm_cost_log_001
Create Date: 2026-04-26
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Sequence, Union


revision: str = "lb6_indexes_rls_001"
down_revision: Union[str, None] = "llm_cost_log_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_impl():
    path = Path(__file__).resolve().parents[3] / "alembic/versions/lb6_schema_parity_indexes_rls_001.py"
    spec = importlib.util.spec_from_file_location("lb6_schema_parity_indexes_rls_001", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load LB-6 migration implementation from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_impl = _load_impl()

COMPOSITE_INDEXES = _impl.COMPOSITE_INDEXES
EXPRESSION_INDEXES = _impl.EXPRESSION_INDEXES
RLS_TABLES = _impl.RLS_TABLES


def upgrade() -> None:
    _impl.upgrade()


def downgrade() -> None:
    _impl.downgrade()
