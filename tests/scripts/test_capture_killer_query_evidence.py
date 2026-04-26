from pathlib import Path

import scripts.capture_killer_query_evidence as capture


def test_capture_harness_respects_explicit_database_url(monkeypatch):
    configured = "sqlite:////tmp/nrg-explicit.db"

    monkeypatch.setenv("DATABASE_URL", configured)
    monkeypatch.delenv("NRG_TEST_DATABASE_URL", raising=False)

    assert capture.resolve_local_database_url() == configured
    assert capture.sqlite_path() == Path("/tmp/nrg-explicit.db")


def test_capture_harness_defaults_to_populated_local_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("NRG_TEST_DATABASE_URL", raising=False)

    assert capture.resolve_local_database_url() == f"sqlite:///{capture.ROOT / 'data/nrg_research.db'}"
    assert capture.sqlite_path() == capture.ROOT / "data/nrg_research.db"


def test_capture_harness_upgrades_default_root_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nrg_research.db")
    monkeypatch.delenv("NRG_TEST_DATABASE_URL", raising=False)

    assert capture.resolve_local_database_url() == f"sqlite:///{capture.ROOT / 'data/nrg_research.db'}"
    assert capture.sqlite_path() == capture.ROOT / "data/nrg_research.db"


def test_explain_writer_registers_sqlite_split_part(monkeypatch, tmp_path):
    db_path = tmp_path / "explain.db"
    db_path.touch()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("NRG_TEST_DATABASE_URL", raising=False)

    explain_path = tmp_path / "explain.txt"
    capture.write_explain("SELECT SPLIT_PART('3:1', ':', 1)", explain_path, "KILLER-TEST")

    assert "KILLER-TEST" in explain_path.read_text(encoding="utf-8")
