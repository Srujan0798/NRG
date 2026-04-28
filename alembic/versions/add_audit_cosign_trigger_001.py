"""Add audit_db_cosign table and DB co-sign trigger.

Revision ID: add_audit_cosign_trigger_001
Revises: add_production_tables_001
Create Date: 2026-04-24

This migration adds the multi-party attestation table for Protocol #35 Phase 2.
A compromised API process alone cannot forge the audit chain — the DB co-sign
provides an independent HMAC over (event_id, chain_hash, per_user_binding)
using a DB-only secret (AUDIT_DB_COSIGN_KEY).

Usage:
    AUDIT_DB_COSIGN_KEY must be set in the environment (ideally via Vault).
    Set it once: openssl rand -hex 32
"""

from alembic import op

from src.audit.db_cosign import generate_audit_cosign_trigger_sql

revision = "add_audit_cosign_trigger_001"
down_revision = "schema_parity_columns_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        op.execute("""
            CREATE TABLE IF NOT EXISTS audit_db_cosign (
                event_id     TEXT NOT NULL PRIMARY KEY,
                chain_hash   TEXT NOT NULL,
                user_id      TEXT NOT NULL,
                event_type   TEXT NOT NULL,
                db_signature TEXT NOT NULL,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_db_cosign_chain_hash
            ON audit_db_cosign (chain_hash)
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_db_cosign_created_at
            ON audit_db_cosign (created_at)
        """)
        return

    op.execute(generate_audit_cosign_trigger_sql())

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_db_cosign (
            event_id         TEXT    NOT NULL PRIMARY KEY,
            chain_hash       TEXT    NOT NULL,
            user_id          TEXT    NOT NULL,
            event_type       TEXT    NOT NULL,
            db_signature     TEXT    NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_db_cosign_chain_hash
        ON audit_db_cosign (chain_hash)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_db_cosign_created_at
        ON audit_db_cosign (created_at)
    """)

    op.execute("COMMENT ON TABLE audit_db_cosign IS 'Multi-party audit co-signatures — API cannot forge chain alone'")


def downgrade() -> None:
    context = op.get_context()
    if context.dialect.name != "postgresql":
        op.execute("DROP TABLE IF EXISTS audit_db_cosign")
        return

    op.execute("DROP TRIGGER IF EXISTS audit_cosign_trigger ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS audit_cosign_event()")
    op.execute("DROP TABLE IF EXISTS audit_db_cosign")
