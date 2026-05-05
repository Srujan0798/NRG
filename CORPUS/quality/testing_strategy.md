# NRG Testing Strategy

## Test Structure

```
tests/
├── api/              # FastAPI endpoint tests
├── audit/            # Audit chain integrity tests
├── auth/             # Authentication & RBAC tests
├── benchmarks/       # Dhairya regression & adversarial tests
├── chaos/            # Chaos engineering tests
├── config/           # Configuration tests
├── contract/         # API contract tests
├── data/             # Data quality & schema tests
├── db/               # Database migration tests
├── e2e/              # End-to-end browser tests (Playwright)
├── evals/            # LLM evaluation tests
├── fixtures/         # Shared test fixtures
├── frontend/         # Frontend component tests (Jest)
├── ingestion/        # Data ingestion tests
├── integration/      # Integration tests
├── load/             # Load tests (Locust)
├── misc/             # Miscellaneous tests
├── observability/    # Metrics & drift tests
├── orchestration/    # LangGraph planner tests
├── performance/      # SLO compliance tests
├── scripts/          # Script tests
├── security/         # Security & PII tests
└── conftest.py       # Shared pytest fixtures
```

## Key Test Commands

```bash
# Full suite (non-live)
.venv/bin/python -m pytest tests/ -q --tb=short --no-cov

# Live API tests (requires running stack)
bash scripts/run_test_suite.sh --live-api

# Security tests
.venv/bin/python -m pytest tests/security/ -q --tb=short --no-cov

# Orchestration / planner tests
.venv/bin/python -m pytest tests/orchestration/ -q --tb=short --no-cov

# Performance / SLO tests
.venv/bin/python -m pytest tests/performance/ tests/load/ -q --tb=short --no-cov

# Dhairya regression (slow — LLM calls)
.venv/bin/python -m pytest tests/benchmarks/test_dhairya_regression.py -v --timeout=600

# Killer queries (e2e)
.venv/bin/python -m pytest tests/e2e/test_three_killer_queries.py -v -m e2e

# Frontend tests
cd frontend && npm run test -- --watchAll=false

# Quality bar scorecard
.venv/bin/python scripts/quality_bar_scorecard.py
```

## Test Categories

| Category | Marker | Purpose |
|----------|--------|---------|
| Unit | (no marker) | Individual functions/classes |
| Integration | `integration` | External services |
| E2E | `e2e` | Full browser/API flows |
| Smoke | `smoke` | Fast health checks |
| Security | `security` | Blocks deployment if fails |
| Slow | `slow` | Long-running tests |

## Quality Bar Tests

| Constraint | Test Files |
|-----------|-----------|
| C1 DPDP PII | `tests/security/test_pii_*.py` |
| C2 Audit Binding | `tests/security/test_per_user_audit_binding.py`, `tests/audit/test_chain_integrity.py` |
| C3 Multi-hop | `tests/orchestration/test_multi_hop_planner.py` |
| C4 SLO | `tests/performance/test_slo_compliance.py`, `tests/load/test_slo_under_load.py` |
| C5 Vector Drift | `tests/observability/test_vector_drift.py` |
| C6 Egress | `tests/security/test_egress_allowlist.py`, `tests/security/test_egress_guard.py` |

## CI Integration

- `.github/workflows/cd.yml` runs quality bar before build
- Scorecard blocks deployment if not 6/6
- Nightly cron runs full suite
