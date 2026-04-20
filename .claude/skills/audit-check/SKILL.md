---
name: audit-check
description: Verify audit chain integrity and check for tampering. Use /audit-check to run.
allowed-tools: Bash(.venv/bin/python *) Read
---

# Audit Chain Verification

1. Run the audit investigation script:
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python scripts/audit_investigate.py
```

2. Also verify via the API audit module:
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "from src.audit import verify_chain; valid, errors = verify_chain(); print(f'Valid: {valid}, Errors: {len(errors)}'); [print(f'  - {e}') for e in errors[:10]]"
```

3. Report chain status: valid/corrupted, event count, any mismatches
