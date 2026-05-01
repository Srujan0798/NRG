# Audit Binding Rebuild After Validation

## What Went Wrong

Broad local validation and live API probes appended audit events that kept hash continuity valid but broke per-user binding verification for 367 events.

`scripts/audit_investigate.py` reported OK because it checks chain continuity, while `verify_chain()` reported per-user binding mismatches. Health then returned CRITICAL until the binding-aware chain was repaired.

## Root Cause

Not fully isolated yet. The observed failure mode is a mismatch between continuity-only audit checks and per-user binding checks after mixed local validation runs.

## Fix Applied

Ran:

```bash
.venv/bin/python scripts/audit_rebuild.py --rebuild --preserve-lineage
```

The tool archived `.audit/chain_corrupted_backup_20260501T215637Z.jsonl`, rebuilt 55,141 events, appended a rebuild event, and final `verify_chain()` returned valid with 55,212 events and 0 errors.

## Prevention Check

After any live validation run that appends audit events, run binding-aware verification, not only continuity investigation:

```bash
.venv/bin/python - <<'PY'
from src.audit import verify_chain
valid, errors, count = verify_chain()
print(valid, len(errors), count)
raise SystemExit(0 if valid else 1)
PY
```

Do not claim audit health from `audit_investigate.py` alone.
