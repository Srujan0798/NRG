"""Align legacy Batch 4 primary keys with db_struct.sql.

Revision ID: d4_primary_key_alignment_005
Revises: d4_partition_audit_events_004
Create Date: 2026-05-05
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "d4_primary_key_alignment_005"
down_revision: Union[str, None] = "d4_partition_audit_events_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PK_ALIGNMENTS: tuple[tuple[str, str, str], ...] = (
    ("fdi_investment", "fdi_investment_pkey", "fdi_investment_id_seq"),
    ("fdp_details", "fdp_details_pkey", "fdp_details_id_seq"),
    (
        "founders_of_fortune_500_companies",
        "founders_of_fortune_500_companies_pkey",
        "founders_of_fortune_500_companies_id_seq",
    ),
    (
        "startup_receiving_vc_investment",
        "startup_receiving_vc_investment_pkey",
        "startup_receiving_vc_investment_id_seq",
    ),
    ("startup_recognition_old", "startup_recognition_pkey", "startup_recognition_id_seq"),
    ("startup_recognition", "startup_recognition_pkey1", "startup_recognition_id_seq"),
)


def _table_exists(table_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _pk_columns(table_name: str) -> list[str]:
    inspector = inspect(op.get_bind())
    constraint = inspector.get_pk_constraint(table_name) if _table_exists(table_name) else {}
    return list(constraint.get("constrained_columns") or [])


def _column_names(table_name: str) -> list[str]:
    inspector = inspect(op.get_bind())
    if not _table_exists(table_name):
        return []
    return [column["name"] for column in inspector.get_columns(table_name)]


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _drop_postgres_primary_key(table_name: str) -> None:
    bind = op.get_bind()
    constraint_name = bind.execute(
        sa.text(
            """
            SELECT con.conname
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'public'
              AND rel.relname = :table_name
              AND con.contype = 'p'
            """
        ),
        {"table_name": table_name},
    ).scalar()
    if constraint_name:
        op.execute(f"ALTER TABLE {_quote(table_name)} DROP CONSTRAINT {_quote(constraint_name)}")


def _align_postgres_primary_key(table_name: str, pk_name: str, sequence_name: str) -> None:
    if not _table_exists(table_name) or _pk_columns(table_name) == ["id"]:
        return

    if "id" not in _column_names(table_name):
        op.add_column(table_name, sa.Column("id", sa.Integer(), nullable=True))

    op.execute(f"CREATE SEQUENCE IF NOT EXISTS {_quote(sequence_name)} AS integer")
    op.execute(
        f"""
        ALTER TABLE {_quote(table_name)}
        ALTER COLUMN id SET DEFAULT nextval('{sequence_name}'::regclass)
        """
    )
    op.execute(
        f"""
        WITH numbered AS (
            SELECT ctid, row_number() OVER (ORDER BY ctid)::integer AS row_id
            FROM {_quote(table_name)}
        )
        UPDATE {_quote(table_name)} AS target
        SET id = numbered.row_id
        FROM numbered
        WHERE target.ctid = numbered.ctid
        """
    )
    _drop_postgres_primary_key(table_name)
    op.execute(f"ALTER TABLE {_quote(table_name)} ALTER COLUMN id SET NOT NULL")
    op.execute(f"ALTER TABLE {_quote(table_name)} ADD CONSTRAINT {_quote(pk_name)} PRIMARY KEY (id)")
    op.execute(f"ALTER SEQUENCE {_quote(sequence_name)} OWNED BY {_quote(table_name)}.id")
    op.execute(
        f"""
        SELECT setval(
            '{sequence_name}'::regclass,
            COALESCE((SELECT MAX(id) FROM {_quote(table_name)}), 0) + 1,
            false
        )
        """
    )


def _sqlite_column_rows(table_name: str) -> list[sa.engine.Row]:
    return list(op.get_bind().execute(sa.text(f"PRAGMA table_info({_quote(table_name)})")).fetchall())


def _align_sqlite_primary_key(table_name: str) -> None:
    if not _table_exists(table_name) or _pk_columns(table_name) == ["id"]:
        return

    rows = _sqlite_column_rows(table_name)
    if not rows:
        return

    columns = [row[1] for row in rows]
    if "id" not in columns:
        op.add_column(table_name, sa.Column("id", sa.Integer(), nullable=True))
        rows = _sqlite_column_rows(table_name)
        columns = [row[1] for row in rows]

    temp_table = f"__{table_name}_pk_align_tmp"
    op.execute(f"DROP TABLE IF EXISTS {_quote(temp_table)}")

    definitions: list[str] = []
    for row in rows:
        name = row[1]
        column_type = row[2] or "TEXT"
        if name == "id":
            definitions.append(f"{_quote(name)} INTEGER PRIMARY KEY AUTOINCREMENT")
            continue

        definition = f"{_quote(name)} {column_type}"
        if row[4] is not None:
            definition += f" DEFAULT {row[4]}"
        if row[3] and not row[5]:
            definition += " NOT NULL"
        definitions.append(definition)

    op.execute(f"CREATE TABLE {_quote(temp_table)} ({', '.join(definitions)})")
    insert_columns = ", ".join(_quote(column) for column in columns)
    select_columns = ", ".join(
        "COALESCE(id, row_number() OVER (ORDER BY rowid))" if column == "id" else _quote(column)
        for column in columns
    )
    op.execute(
        f"""
        INSERT INTO {_quote(temp_table)} ({insert_columns})
        SELECT {select_columns}
        FROM {_quote(table_name)}
        """
    )
    op.execute(f"DROP TABLE {_quote(table_name)}")
    op.execute(f"ALTER TABLE {_quote(temp_table)} RENAME TO {_quote(table_name)}")


def upgrade() -> None:
    dialect_name = op.get_context().dialect.name
    for table_name, pk_name, sequence_name in PK_ALIGNMENTS:
        if dialect_name == "postgresql":
            _align_postgres_primary_key(table_name, pk_name, sequence_name)
        elif dialect_name == "sqlite":
            _align_sqlite_primary_key(table_name)


def downgrade() -> None:
    # Forward-only: db_struct.sql declares id primary keys for these tables.
    return
