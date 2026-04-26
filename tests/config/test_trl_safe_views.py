from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_LAYER = ROOT / "src/skills/text_to_sql/semantic_layer.yaml"
MIGRATION = ROOT / "alembic/versions/safe_trl_alias_views_001.py"


def test_semantic_layer_exposes_short_trl_views():
    layer = yaml.safe_load(SEMANTIC_LAYER.read_text())
    safe_views = layer["safe_views"]

    assert "trl_stages" in safe_views
    assert "tech_trl_stages" in safe_views
    assert safe_views["trl_stages"]["actual_table"] == (
        "innovations_at_various_stages_of_technology_readiness_level"
    )


def test_migration_creates_short_trl_views():
    source = MIGRATION.read_text()

    assert "CREATE OR REPLACE VIEW trl_stages AS" in source
    assert "CREATE OR REPLACE VIEW tech_trl_stages AS" in source
    assert "DROP VIEW IF EXISTS trl_stages" in source
    assert "DROP VIEW IF EXISTS tech_trl_stages" in source
