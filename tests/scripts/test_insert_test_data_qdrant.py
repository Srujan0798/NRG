from pathlib import Path


def test_qdrant_test_data_seeder_uses_supported_client_kwargs():
    source = Path("scripts/insert_test_data.py").read_text(encoding="utf-8")

    assert "check_compatibility" not in source
