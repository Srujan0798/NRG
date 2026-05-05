# POINTER: Testing Strategy

> **Do not trust this file as the source of truth.** Read the actual files listed below to verify tests exist and pass.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Test config** | `pytest.ini` | Markers, plugins, defaults |
| **API tests** | `tests/api/` | Endpoint tests |
| **Security tests** | `tests/security/` | PII, egress, audit chain |
| **Orchestration tests** | `tests/orchestration/` | Planner, multi-hop |
| **Performance tests** | `tests/performance/`, `tests/load/` | SLO, Locust |
| **E2E tests** | `tests/e2e/`, `frontend/tests/e2e/` | Playwright browser tests |
| **Benchmarks** | `tests/benchmarks/` | Dhairya regression, adversarial |

## Verification Commands

```bash
# Test structure
ls tests/

# Check pytest config
cat pytest.ini

# Count test files
find tests/ -name "test_*.py" | wc -l

# Check CI
ls .github/workflows/

# Run a quick test subset
.venv/bin/python -m pytest tests/security/test_pii_indian.py -q --tb=short --no-cov
```

## Requirements to Verify Against

From `quality/quality_bar.md`:
- C1: `tests/security/test_pii_*.py`
- C2: `tests/security/test_per_user_audit_binding.py`, `tests/audit/test_chain_integrity.py`
- C3: `tests/orchestration/test_multi_hop_planner.py`
- C4: `tests/performance/test_slo_compliance.py`, `tests/load/test_slo_under_load.py`
- C5: `tests/observability/test_vector_drift.py`
- C6: `tests/security/test_egress_allowlist.py`

**Read the actual source files. Do not trust this pointer.**
