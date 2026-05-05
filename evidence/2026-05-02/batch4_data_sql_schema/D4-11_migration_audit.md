# D4-11 Migration Audit

- Migration files: 15
- Heads: d4_primary_key_alignment_005
- Risky upgrade marker count: 0

| File | Revision | Down revision | Upgrade risk markers |
|---|---|---|---|
| `src/migrations/versions/6d878bf70def_initial_schema.py` | `6d878bf70def` | `None` |  |
| `src/migrations/versions/a1b2c3d4e002_add_check_constraints.py` | `a1b2c3d4e002` | `b1c2d3e4f001` |  |
| `src/migrations/versions/add_audit_cosign_trigger_001.py` | `add_audit_cosign_trigger_001` | `schema_parity_columns_001` |  |
| `src/migrations/versions/add_production_tables_001.py` | `add_production_tables_001` | `a1b2c3d4e002` |  |
| `src/migrations/versions/add_tech_trl_stages_view_002.py` | `add_tech_trl_stages_view_002` | `add_trl_stages_view_001` |  |
| `src/migrations/versions/add_trl_stages_view_001.py` | `add_trl_stages_view_001` | `lb6_indexes_rls_001` |  |
| `src/migrations/versions/b1c2d3e4f001_add_missing_foreign_keys.py` | `b1c2d3e4f001` | `6d878bf70def` |  |
| `src/migrations/versions/d4_data_constraints_indexes_001.py` | `d4_data_constraints_indexes_001` | `add_tech_trl_stages_view_002` |  |
| `src/migrations/versions/d4_fk_type_alignment_003.py` | `d4_fk_type_alignment_003` | `d4_hot_path_indexes_002` |  |
| `src/migrations/versions/d4_hot_path_indexes_002.py` | `d4_hot_path_indexes_002` | `d4_data_constraints_indexes_001` |  |
| `src/migrations/versions/d4_partition_audit_events_004.py` | `d4_partition_audit_events_004` | `d4_fk_type_alignment_003` |  |
| `src/migrations/versions/d4_primary_key_alignment_005.py` | `d4_primary_key_alignment_005` | `d4_partition_audit_events_004` |  |
| `src/migrations/versions/lb6_indexes_rls_001.py` | `lb6_indexes_rls_001` | `llm_cost_log_001` |  |
| `src/migrations/versions/llm_cost_log_001.py` | `llm_cost_log_001` | `add_audit_cosign_trigger_001` |  |
| `src/migrations/versions/schema_parity_columns_001.py` | `schema_parity_columns_001` | `add_production_tables_001` |  |
