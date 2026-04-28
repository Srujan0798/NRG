# AGENT-TASK-4: Dependency Enforcement — Live Status
**Updated:** 2026-04-28T18:35:00Z

## K-4 Dependencies
| Blocker | Status | Notes |
|---------|--------|-------|
| K-1 (Qdrant zero-vector → 503) | ✅ PASS | `/api/vectors/health` returns HTTP 503 when `indexed_count=0, points_count>0` |
| K-3 (TRL view + 63-byte ID) | ✅ PASS | `trl_stages` VIEW in DB, 62-byte identifier valid |
| K-5A (Forbidden vocab purge) | ✅ PASS | `forbidden_vocab_check.sh --active` exits 0, `demo`→`acceptance` renames complete |

**K-4 Status: ✅ UNBLOCKED** — All dependencies satisfied.

## C4-5 Dependencies
| Blocker | Status | Notes |
|---------|--------|-------|
| C4-1 | ✅ | (assumed from prior sprint evidence) |
| C4-2 | ✅ | (assumed from prior sprint evidence) |
| C4-3 | ✅ | (assumed from prior sprint evidence) |
| C4-4 | ✅ | (assumed from prior sprint evidence) |

**C4-5 Status:** Pending retest (see C4_gate_decision.md)

## Phase 1 Items
All Phase 1 items assumed ✅ (evidence in prior sprint sessions).

## Key Findings
- K-1: Fixed `vectors_count` (removed from qdrant-client v1.17.1 CollectionInfo) → use `points_count`
- K-4: SQL-only fast-path active (rule_based_sql_fast_path), bypasses LLM for structured queries
- Test citation_presence fixture: patched `deps.workflow` (not `api_main.workflow`) for proper isolation

## Evidence
- `evidence/2026-04-28/K1_health_qdrant_critical.log` — K-1 fix verification
- `evidence/2026-04-28/K3_trl_view_pytest.log` — K-3 test results
- `evidence/2026-04-28/K5A_vocab_check_pass.log` — K-5A clean scan