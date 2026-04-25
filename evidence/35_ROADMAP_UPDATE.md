# Roadmap Update Evidence

**Skill**: roadmap-update
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/35_ROADMAP_UPDATE.md`

---

## Roadmap Analysis: NRG Project

### Current State (from BACKLOG.md)

**Phase**: Phase 6 (fine-tuning pipeline / Protocol #29 training data collection)
**Tag**: `v1.0.0-client-handover` re-pushed
**Quality Bar**: 4/6 in-process (C1✅ C2✅ C3✅ C6✅; C4⏳ C5⏳)
**Baseline Score**: 7.5/10 — 16 components verified working, 8 gaps (3 local P0, 5 cluster-dependent)

---

## Existing Roadmap Items (from BACKLOG.md)

### Completed (V4 Wrap)
| Item | Status | Evidence |
|------|--------|----------|
| Audit rebuild self-break | ✅ Done | `1562d694` |
| API SQL exposure fix | ✅ Done | SQL query in response |
| Quality Bar C5 partial | ✅ Done | Reports `partial` not hard fail |
| Grafana dashboard JSON | ✅ Done | Fixed malformed mapping |
| CLOUD_SYNTHESIS policy drift | ✅ Done | Pre-commit no longer forces |

### In Progress
| Item | Status | Notes |
|------|--------|-------|
| Phase 6: Fine-tuning pipeline | 🔄 In Progress | Protocol #29 training data collection |
| C4 SLO load test | ⏳ Blocked | Requires cluster access |
| C5 vector drift baseline | ⏳ Blocked | Requires Qdrant baseline |

### Blocked (This Session's Findings)
| Item | Priority | Blocker |
|------|----------|---------|
| SQL injection fix (line 479) | 🔴 P0 | CRITICAL — cannot deploy |
| nginx as root | 🔴 P0 | CRITICAL — security |
| Audit chain lock (line 244) | 🟡 P1 | Performance under concurrency |
| JWT refresh no revoke | 🟡 P1 | Security regression |
| Qdrant unhealthy | 🟡 P1 | Vector search broken |

---

## Updated Roadmap (Now/Next/Later)

### NOW (Current Sprint — P0 Items)

| Item | Owner | Effort | Deadline | Dependencies |
|------|-------|--------|----------|--------------|
| Fix SQL injection (main.py:479) | Backend | 2h | Immediate | None |
| Fix nginx as root (Dockerfile.frontend) | DevOps | 1h | Immediate | None |
| Fix JWT refresh revocation | Backend | 2h | Immediate | None |
| Fix audit chain lock (line 244) | Backend | 4h | This week | None |

### NEXT (1-4 weeks)

| Item | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Schema parity (add 11 missing tables) | P1 | 4h | Alembic migration |
| Fix Qdrant health check | P1 | 2h | Docker config |
| Add `updated_at` to all tables | P2 | 8h | Migration + code |
| Test suite parallelization (pytest-xdist) | P2 | 4h | None |
| Dev documentation (README, runbook) | P2 | 8h | None |

### LATER (1-3 months)

| Item | Priority | Dependencies |
|------|----------|--------------|
| C4 SLO load test | P2 | Cluster access |
| C5 vector drift baseline | P2 | Qdrant baseline |
| Prompt caching (claude-api skill) | P2 | SDK migration |
| Prompt engineering (CoT, few-shot) | P2 | After caching |
| Dashboard implementation (build-dashboard skill) | P3 | Data sources |

---

## Changes from Previous Roadmap

### What Changed
1. **Added P0 items** from this session's security audit:
   - SQL injection (CRITICAL)
   - nginx as root (CRITICAL)
   - JWT refresh revocation (MEDIUM → P1)
   - Audit chain lock (MEDIUM → P1)

2. **Removed cluster-only items** from immediate roadmap:
   - C4 SLO load test (blocked on cluster access — not a code gap)
   - C5 vector drift baseline (blocked on Qdrant — not a code gap)

### What Stayed Same
- Phase 6 fine-tuning pipeline (in progress)
- `v1.0.0-client-handover` tag (already pushed)

---

## Risks and Dependencies

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQL injection exploited before fix | 🔴 High | Critical | Immediate fix, no deploy until fixed |
| Qdrant stays unhealthy | 🟡 Medium | High | Disable RAG, continue without vector search |
| Test suite timeout blocks CI | 🟡 Medium | Medium | Add pytest-xdist parallelization |

### Dependencies
| Item | Depends On | Owner |
|------|-----------|-------|
| Schema parity | Alembic migration | Backend |
| C4 SLO test | Cluster access | DevOps/Platform |
| C5 baseline | Qdrant populated | DevOps |

---

## RICE Prioritization (Top Items)

| Item | Reach | Impact | Confidence | Effort | RICE |
|------|-------|--------|------------|--------|------|
| Fix SQL injection | 100% users | 3 | 100% | 1 day | 300 |
| Fix nginx as root | 100% users | 3 | 100% | 1 day | 300 |
| Fix JWT refresh | 100% users | 2 | 90% | 1 day | 180 |
| Fix audit chain lock | 100% users | 2 | 80% | 0.5 day | 320 |
| Schema parity | 50% (dev only) | 1 | 90% | 0.5 day | 90 |

**Top 3 by RICE**: Fix audit chain (320), Fix SQL injection (300), Fix nginx (300)

---

## Skill Deliverable

**Status**: COMPLETED

Roadmap updated based on this session's findings:
- 4 new P0/P1 items added (SQL injection, nginx, JWT, audit chain)
- 2 cluster-only items moved to "later" (not code gaps)
- Phase 6 continues unchanged
- RICE prioritization applied — audit chain lock has highest RICE score (320)
