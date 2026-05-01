from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine

from scripts.data_quality_scorecard import _score_dropped
from src.observability.data_quality import (
    PILLAR_NAMES,
    DataQualityMonitor,
    DataQualityThresholds,
    run_data_quality_scorecard,
)


def _create_quality_fixture(db_path: Path, *, pii_leak: bool = False, orphan: bool = False) -> str:
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    now = datetime.now(UTC).isoformat()

    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE institutions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE researchers (
                id INTEGER PRIMARY KEY,
                institution_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                discipline TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(institution_id) REFERENCES institutions(id)
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE publications (
                id INTEGER PRIMARY KEY,
                researcher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                publication_year INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(researcher_id) REFERENCES researchers(id)
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE project_notes (
                id INTEGER PRIMARY KEY,
                institution_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.exec_driver_sql(
            "INSERT INTO institutions VALUES (1, 'IIT Bombay', 'MH', ?), (2, 'IISc', 'KA', ?)",
            (now, now),
        )
        conn.exec_driver_sql(
            """
            INSERT INTO researchers VALUES
                (1, 1, 'Ada Rao', 'AI', ?),
                (2, 2, 'Vik Mehta', 'Materials', ?)
            """,
            (now, now),
        )
        conn.exec_driver_sql(
            """
            INSERT INTO publications VALUES
                (1, 1, 'AI for Materials', 2026, ?),
                (2, 2, 'Materials for AI', 2026, ?)
            """,
            (now, now),
        )

        note = "Contact researcher@iitb.ac.in for raw record" if pii_leak else "Aggregate note only"
        institution_id = 99 if orphan else 1
        conn.exec_driver_sql(
            "INSERT INTO project_notes VALUES (1, ?, ?, ?), (2, 2, 'Clean note', ?)",
            (institution_id, note, now, now),
        )

    engine.dispose()
    return db_url


def _thresholds() -> DataQualityThresholds:
    return DataQualityThresholds(
        expected_table_count=4,
        min_core_rows=2,
        max_freshness_days=7,
        max_null_rate=0.05,
    )


def test_scorecard_measures_all_seven_pillars(tmp_path):
    db_url = _create_quality_fixture(tmp_path / "quality.sqlite")
    monitor = DataQualityMonitor(
        db_url,
        expected_tables={"institutions", "researchers", "publications", "project_notes"},
        core_tables={"institutions", "researchers", "publications", "project_notes"},
        non_pii_tables={"institutions", "researchers", "publications", "project_notes"},
        thresholds=_thresholds(),
    )

    scorecard = monitor.run()

    assert [result.name for result in scorecard.pillars] == list(PILLAR_NAMES)
    assert scorecard.overall_status == "PASS"
    assert scorecard.overall_score == 1.0
    assert not scorecard.alerts
    assert all(result.status == "PASS" for result in scorecard.pillars)

    payload = scorecard.to_dict()
    assert payload["ok"] is True
    assert payload["pillars"]["schema_coverage"]["observed"]["present_tables"] == 4
    assert "| Pillar | Status | Score | Threshold |" in scorecard.to_markdown()


def test_pii_leak_triggers_p0_alert(tmp_path):
    db_url = _create_quality_fixture(tmp_path / "pii.sqlite", pii_leak=True)
    scorecard = DataQualityMonitor(
        db_url,
        expected_tables={"institutions", "researchers", "publications", "project_notes"},
        core_tables={"institutions", "researchers", "publications", "project_notes"},
        non_pii_tables={"project_notes"},
        thresholds=_thresholds(),
    ).run()

    pii_result = scorecard.pillar("pii_sanitization")

    assert scorecard.overall_status == "FAIL"
    assert pii_result.status == "FAIL"
    assert pii_result.severity == "P0"
    assert any(alert.severity == "P0" and alert.pillar == "pii_sanitization" for alert in scorecard.alerts)


def test_referential_integrity_below_critical_threshold_triggers_p0(tmp_path):
    db_url = _create_quality_fixture(tmp_path / "orphan.sqlite", orphan=True)
    scorecard = DataQualityMonitor(
        db_url,
        expected_tables={"institutions", "researchers", "publications", "project_notes"},
        core_tables={"institutions", "researchers", "publications", "project_notes"},
        non_pii_tables={"institutions", "researchers", "publications", "project_notes"},
        thresholds=_thresholds(),
        consistency_relationships={("project_notes", "institution_id"): ("institutions", "id")},
    ).run()

    integrity_result = scorecard.pillar("referential_integrity")
    consistency_result = scorecard.pillar("consistency")

    assert integrity_result.status == "FAIL"
    assert integrity_result.severity == "P0"
    assert integrity_result.score < 0.90
    assert consistency_result.status == "FAIL"
    assert any(alert.pillar == "referential_integrity" and alert.severity == "P0" for alert in scorecard.alerts)


def test_scorecard_script_writes_json_and_markdown(tmp_path):
    db_url = _create_quality_fixture(tmp_path / "scorecard.sqlite")
    json_output = tmp_path / "scorecard.json"
    markdown_output = tmp_path / "scorecard.md"

    scorecard = run_data_quality_scorecard(
        database_url=db_url,
        json_output=json_output,
        markdown_output=markdown_output,
        expected_tables={"institutions", "researchers", "publications", "project_notes"},
        core_tables={"institutions", "researchers", "publications", "project_notes"},
        non_pii_tables={"institutions", "researchers", "publications", "project_notes"},
        thresholds=_thresholds(),
    )

    payload = json.loads(json_output.read_text())

    assert scorecard.overall_status == "PASS"
    assert payload["ok"] is True
    assert set(payload["pillars"]) == set(PILLAR_NAMES)
    assert markdown_output.read_text().startswith("# Data Quality Scorecard")


def test_baseline_check_tolerates_rounding_noise(tmp_path):
    db_url = _create_quality_fixture(tmp_path / "baseline.sqlite")
    scorecard = DataQualityMonitor(
        db_url,
        expected_tables={"institutions", "researchers", "publications", "project_notes"},
        core_tables={"institutions", "researchers", "publications", "project_notes"},
        non_pii_tables={"institutions", "researchers", "publications", "project_notes"},
        thresholds=_thresholds(),
    ).run()
    baseline = scorecard.to_dict()
    baseline["overall_score"] = scorecard.overall_score + 0.000000001

    assert _score_dropped(scorecard, baseline) is False


def test_null_rate_ignores_nullable_optional_columns(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'nullable.sqlite'}"
    engine = create_engine(db_url)
    now = datetime.now(UTC).isoformat()

    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE institutions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                optional_website TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.exec_driver_sql(
            """
            INSERT INTO institutions (id, name, state, optional_website, updated_at) VALUES
                (1, 'IIT Bombay', 'Maharashtra', NULL, ?),
                (2, 'IISc Bengaluru', 'Karnataka', NULL, ?)
            """,
            (now, now),
        )

    scorecard = DataQualityMonitor(
        db_url,
        expected_tables={"institutions"},
        core_tables={"institutions"},
        non_pii_tables={"institutions"},
        thresholds=DataQualityThresholds(
            expected_table_count=1,
            min_core_rows=2,
            max_null_rate=0.05,
            max_freshness_days=7,
        ),
    ).run()

    null_rate = scorecard.pillar("null_rate")

    assert null_rate.status == "PASS"
    assert null_rate.observed["columns_skipped_nullable"] == 1
    assert not null_rate.observed["violations"]


def test_freshness_reports_real_age_days_without_clamping(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'stale.sqlite'}"
    engine = create_engine(db_url)
    stale = (datetime.now(UTC) - timedelta(days=9, hours=3)).isoformat()

    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE institutions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.exec_driver_sql(
            "INSERT INTO institutions VALUES (1, 'IIT Bombay', 'Maharashtra', ?)",
            (stale,),
        )

    scorecard = DataQualityMonitor(
        db_url,
        expected_tables={"institutions"},
        core_tables={"institutions"},
        non_pii_tables={"institutions"},
        thresholds=DataQualityThresholds(
            expected_table_count=1,
            min_core_rows=1,
            max_freshness_days=7,
        ),
    ).run()

    freshness = scorecard.pillar("freshness")

    assert freshness.status == "FAIL"
    assert freshness.observed["worst_age_days"] > 9
    assert freshness.observed["stale_tables"][0]["age_days"] > 9
