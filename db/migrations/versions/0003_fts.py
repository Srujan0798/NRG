"""Full-text search indexes

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS publications_fts
        USING fts5(title, abstract, content='publications', content_rowid=rowid)
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS publications_fts_insert AFTER INSERT ON publications
        BEGIN
            INSERT INTO publications_fts(rowid, title, abstract)
            VALUES (new.rowid, new.title, new.abstract);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS publications_fts_delete AFTER DELETE ON publications
        BEGIN
            INSERT INTO publications_fts(publications_fts, rowid, title, abstract)
            VALUES ('delete', old.rowid, old.title, old.abstract);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS publications_fts_update AFTER UPDATE ON publications
        BEGIN
            INSERT INTO publications_fts(publications_fts, rowid, title, abstract)
            VALUES ('delete', old.rowid, old.title, old.abstract);
            INSERT INTO publications_fts(rowid, title, abstract)
            VALUES (new.rowid, new.title, new.abstract);
        END
    """)

    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS researchers_fts
        USING fts5(name, research_area, content='researchers', content_rowid=rowid)
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS researchers_fts_insert AFTER INSERT ON researchers
        BEGIN
            INSERT INTO researchers_fts(rowid, name, research_area)
            VALUES (new.rowid, new.name, new.research_area);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS researchers_fts_delete AFTER DELETE ON researchers
        BEGIN
            INSERT INTO researchers_fts(researchers_fts, rowid, name, research_area)
            VALUES ('delete', old.rowid, old.name, old.research_area);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS researchers_fts_update AFTER UPDATE ON researchers
        BEGIN
            INSERT INTO researchers_fts(researchers_fts, rowid, name, research_area)
            VALUES ('delete', old.rowid, old.name, old.research_area);
            INSERT INTO researchers_fts(rowid, name, research_area)
            VALUES (new.rowid, new.name, new.research_area);
        END
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS researchers_fts_update")
    op.execute("DROP TRIGGER IF EXISTS researchers_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS researchers_fts_insert")
    op.execute("DROP TABLE IF EXISTS researchers_fts")
    op.execute("DROP TRIGGER IF EXISTS publications_fts_update")
    op.execute("DROP TRIGGER IF EXISTS publications_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS publications_fts_insert")
    op.execute("DROP TABLE IF EXISTS publications_fts")
