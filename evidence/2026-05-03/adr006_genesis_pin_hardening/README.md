# ADR-006 Genesis Pin Hardening Evidence

Date: 2026-05-03

## Scope

Implemented local genesis pin hardening for the audit chain lineage anchor.

Changed surfaces:

- `src/audit/__init__.py`
- `scripts/audit_rebuild.py`
- `tests/audit/test_chain_integrity.py`
- `docs/adr/ADR-006-audit-chain-auto-repair-lineage-break.md`
- `docs/specs/SPRINT_PHASE2_2026-04-28.md`
- `BACKLOG.md`

## Behavior

- Creates `.audit/genesis_hash.pin` once with exclusive file creation.
- Flushes and fsyncs the pin before close.
- Hardens the pin to `0444`.
- Does not replace an existing pin during append or rebuild flows.
- Keeps `--preserve-lineage` rebuild behavior tied to the pinned genesis hash.

## Fresh Checks

```text
python3 -m py_compile scripts/audit_rebuild.py src/audit/__init__.py \
  tests/audit/test_chain_integrity.py scripts/batch4_data_sql_schema_audit.py
PASS

.venv/bin/ruff check scripts/audit_rebuild.py src/audit/__init__.py \
  tests/audit/test_chain_integrity.py scripts/batch4_data_sql_schema_audit.py
PASS

pytest tests/audit/test_chain_integrity.py tests/audit/test_audit_singleton_reset.py \
  tests/security/test_audit_chain.py tests/security/test_per_user_audit_binding.py -q
72 passed in 0.61s
```

## Preserved Agent Evidence

This directory also contains earlier local proof logs for:

- audit-chain regression;
- query-service regression;
- selected API pytest;
- broad local pytest replay;
- Batch 4 evidence-script help output.

The logs are local proof only. Production object-lock or immutable-storage proof
remains a deployment control.
