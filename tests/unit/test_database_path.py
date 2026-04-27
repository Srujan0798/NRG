from pathlib import Path


def test_relative_database_url_resolves_from_repo_root(monkeypatch, tmp_path):
    from src.data.database import resolve_database_path

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nrg_research.db")

    assert resolve_database_path() == Path(__file__).resolve().parents[2] / "nrg_research.db"


def test_absolute_database_url_is_preserved(monkeypatch, tmp_path):
    from src.data.database import resolve_database_path

    db_file = tmp_path / "custom.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    assert resolve_database_path() == db_file


def test_nrg_database_uses_database_url(monkeypatch, tmp_path):
    from src.data.database import NRGDatabase

    db_file = tmp_path / "custom.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    db = NRGDatabase()

    assert Path(db.db_path) == db_file


def test_postgresql_database_url_uses_configured_auth_sidecar(monkeypatch, tmp_path):
    from src.data.database import resolve_database_path

    auth_db = tmp_path / "auth" / "nrg_auth.db"
    monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@postgres:5432/nrg")
    monkeypatch.setenv("NRG_AUTH_DB_PATH", f"sqlite:///{auth_db}")

    assert resolve_database_path() == auth_db


def test_sqlite_connection_creates_parent_directory(monkeypatch, tmp_path):
    from src.data.database import get_sqlite_connection

    auth_db = tmp_path / "nested" / "auth" / "nrg_auth.db"
    monkeypatch.setenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@postgres:5432/nrg")
    monkeypatch.setenv("NRG_AUTH_DB_PATH", f"sqlite:///{auth_db}")

    conn = get_sqlite_connection()
    conn.close()

    assert auth_db.exists()
