def test_migration_and_audit_investigation_scripts_import():
    import scripts.audit_investigate as audit_investigate
    import scripts.migrate_sqlite_to_pg as migrate_sqlite_to_pg

    assert callable(migrate_sqlite_to_pg.migrate_sqlite_to_postgres)
    assert callable(audit_investigate.investigate_chain)
