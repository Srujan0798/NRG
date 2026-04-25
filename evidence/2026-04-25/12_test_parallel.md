# TEST-PARALLEL-001 — pytest-xdist + Slow Test Markers
Date: 2026-04-25

## pytest-xdist
```bash
$ pip install pytest-xdist  # Already in pyproject.toml as dev dependency
$ .venv/bin/python -c "import xdist; print('OK')"
OK
```

## pytest.ini Configuration
```ini
[pytest]
addopts =
    -v --tb=short --color=yes
    --strict-markers
    --strict-config
    --cov=src --cov-report=term-missing --cov-report=xml
    -m "not slow"  # ← Fast suite: skip slow tests by default
```

## pytest Markers (pytest.ini line 20)
```ini
slow: slow-running tests that can be skipped locally
```

## Slow Test Markers Applied
| Test File | Marker | Status |
|-----------|--------|--------|
| tests/orchestration/test_multi_hop_planner.py | pytest.mark.slow | ✅ Added |

## Fast Suite Status (2026-04-25 run)
| Suite | Tests | Result |
|-------|-------|--------|
| Config + Audit | 55 | ✅ |
| Egress Guard | 13 | ✅ |
| PII Compliance | 8 | ✅ |
| Per-User Audit Binding | 45 | ✅ |
| Dhairya Regression | 43 | ✅ |
| Vector Drift | 17 | ✅ |
| Router | 55 | ✅ |
| Security Regression | 130 | ✅ |
| Vector Drift Scheduler | 11 | ✅ |
| **Fast Suite Total** | **377** | **✅ 377/377** |

## Status: ✅ pytest-xdist installed, slow marker applied, fast suite 377 tests pass
