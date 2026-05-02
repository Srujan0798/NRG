"""Batch 4 partition audit_events by created_at.

Revision ID: d4_partition_audit_events_004
Revises: d4_fk_type_alignment_003
Create Date: 2026-05-02
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.audit.db_cosign import generate_audit_cosign_trigger_sql


revision: str = "d4_partition_audit_events_004"
down_revision: Union[str, None] = "d4_fk_type_alignment_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCE_TABLE = "audit_events"
BACKUP_TABLE = "audit_events_unpartitioned_d4_backup"


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text("SELECT to_regclass(:table_name)"),
            {"table_name": f"public.{table_name}"},
        ).scalar()
    )


def _is_partitioned(table_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    bind = op.get_bind()
    relkind = bind.execute(
        sa.text(
            """
            SELECT cls.relkind
            FROM pg_class cls
            JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
            WHERE nsp.nspname = 'public'
              AND cls.relname = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return relkind == "p"


def _rename_index_if_exists(old_name: str, new_name: str) -> None:
    bind = op.get_bind()
    exists = bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM pg_class cls
                JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
                WHERE nsp.nspname = 'public'
                  AND cls.relkind = 'i'
                  AND cls.relname = :index_name
                """
            ),
            {"index_name": old_name},
        ).scalar()
    )
    if exists:
        op.execute(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"')


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    if not _table_exists(SOURCE_TABLE) or _is_partitioned(SOURCE_TABLE):
        return
    if _table_exists(BACKUP_TABLE):
        raise RuntimeError(f"{BACKUP_TABLE} already exists; refusing to overwrite audit backup")

    op.execute(f'ALTER TABLE "{SOURCE_TABLE}" RENAME TO "{BACKUP_TABLE}"')
    _rename_index_if_exists("audit_events_pkey", "audit_events_unpartitioned_d4_backup_pkey")
    _rename_index_if_exists(
        "idx_audit_events_created_at_brin",
        "idx_audit_events_backup_created_at_brin",
    )
    _rename_index_if_exists(
        "idx_audit_events_event_type_created_at",
        "idx_audit_events_backup_event_type_created_at",
    )

    op.execute(
        f"""
        CREATE TABLE "{SOURCE_TABLE}" (
            LIKE "{BACKUP_TABLE}" INCLUDING DEFAULTS INCLUDING COMMENTS
        ) PARTITION BY RANGE (created_at)
        """
    )
    op.execute(
        f"""
        ALTER TABLE "{SOURCE_TABLE}"
        ADD CONSTRAINT audit_events_pkey PRIMARY KEY (event_id, created_at)
        """
    )
    op.execute(
        f"""
        CREATE TABLE audit_events_before_2026
        PARTITION OF "{SOURCE_TABLE}"
        FOR VALUES FROM (MINVALUE) TO ('2026-01-01')
        """
    )
    op.execute(
        f"""
        CREATE TABLE audit_events_2026
        PARTITION OF "{SOURCE_TABLE}"
        FOR VALUES FROM ('2026-01-01') TO ('2027-01-01')
        """
    )
    op.execute(
        f"""
        CREATE TABLE audit_events_after_2026
        PARTITION OF "{SOURCE_TABLE}"
        FOR VALUES FROM ('2027-01-01') TO (MAXVALUE)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_event_ids (
            event_id TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_audit_event_id_unique()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO audit_event_ids (event_id, created_at)
            VALUES (NEW.event_id, NEW.created_at);
            RETURN NEW;
        EXCEPTION WHEN unique_violation THEN
            RAISE EXCEPTION 'duplicate audit event_id: %', NEW.event_id
                USING ERRCODE = '23505';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER audit_event_id_unique_trigger
        BEFORE INSERT ON "{SOURCE_TABLE}"
        FOR EACH ROW
        EXECUTE FUNCTION enforce_audit_event_id_unique()
        """
    )
    op.execute(f'INSERT INTO "{SOURCE_TABLE}" SELECT * FROM "{BACKUP_TABLE}"')
    op.execute(
        f"""
        CREATE INDEX idx_audit_events_created_at_brin
        ON "{SOURCE_TABLE}" USING BRIN (created_at)
        """
    )
    op.execute(
        f"""
        CREATE INDEX idx_audit_events_event_type_created_at
        ON "{SOURCE_TABLE}" (event_type, created_at)
        """
    )
    op.execute(f'CREATE INDEX idx_audit_events_event_id ON "{SOURCE_TABLE}" (event_id)')
    op.execute(generate_audit_cosign_trigger_sql(SOURCE_TABLE))
    op.execute(f'COMMENT ON TABLE "{BACKUP_TABLE}" IS '
               "'Batch 4 rollback backup for partitioned audit_events'")


def downgrade() -> None:
    # Forward-only migration. The unpartitioned backup table is retained by upgrade
    # so operators can restore manually after reviewing any newer audit rows.
    return
