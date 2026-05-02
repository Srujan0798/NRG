from scripts import batch4_data_sql_schema_audit as audit


def test_read_module_constant_handles_annotated_alembic_constants():
    source = """
revision: str = "d4_partition_audit_events_004"
down_revision: str | None = "d4_fk_type_alignment_003"
"""

    assert audit.read_module_constant(source, "revision") == "d4_partition_audit_events_004"
    assert audit.read_module_constant(source, "down_revision") == "d4_fk_type_alignment_003"


def test_upgrade_risk_markers_handles_typed_upgrade_signature():
    source = """
def upgrade() -> None:
    op.execute("CREATE TABLE useful_table (id integer)")

def downgrade() -> None:
    op.execute("DROP TABLE useful_table")
"""

    assert audit.upgrade_risk_markers(source) == []


def test_upgrade_risk_markers_only_flags_upgrade_body():
    source = """
def upgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN legacy")

def downgrade() -> None:
    op.execute("CREATE TABLE legacy (id integer)")
"""

    assert audit.upgrade_risk_markers(source) == ["alter_table_drop"]


def test_collect_plan_relations_returns_nested_relation_names():
    plan = {
        "Node Type": "Append",
        "Plans": [
            {"Node Type": "Seq Scan", "Relation Name": "audit_events_2026"},
            {
                "Node Type": "Nested Loop",
                "Plans": [
                    {"Node Type": "Index Scan", "Relation Name": "researchers"},
                    {"Node Type": "Index Scan", "Relation Name": "institutions"},
                ],
            },
        ],
    }

    assert audit.collect_plan_relations(plan) == [
        "audit_events_2026",
        "researchers",
        "institutions",
    ]
