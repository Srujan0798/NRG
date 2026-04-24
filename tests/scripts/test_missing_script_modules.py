def test_migration_and_audit_investigation_scripts_import():
    import scripts.audit_investigate as audit_investigate
    import scripts.migrate_sqlite_to_pg as migrate_sqlite_to_pg

    assert callable(migrate_sqlite_to_pg.migrate_sqlite_to_postgres)
    assert callable(audit_investigate.investigate_chain)


def test_seed_relations_script_invocation_can_import_src():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/seed_relations.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout
