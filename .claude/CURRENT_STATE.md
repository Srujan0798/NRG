# NRG — Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-04-30

---

## System Status

| Item | State |
|------|-------|
| Repo structure | Cleaned and pruned; tracked dead docs/components/scripts removed in `516991a`, tracked test-run metadata removed in `6d0ac3a` |
| Working tree | Clean before live quantum recheck; current session adds the focused recheck evidence and auth cold-start timeout hardening |
| Quality Bar | **Not re-certified after cleanup** — last known state was 5/6 with C4 load bar failing |
| Full test suite | Not rerun in this session; use Python 3.11 venv for reliable results |
| Targeted recent checks | Wave 1 API tests, Wave 4 SQL/RAG/health tests, Wave 2 frontend build/browser tests, Wave 3 security/audit tests, Wave 5 local load/performance tests, and live local full-stack proof passed in targeted runs |
| Audit chain | Rebuilt after pre-fix concurrent profile, then verified on 2026-04-30 with `scripts/audit_investigate.py`: `ok=true`, `events_checked=38417`, no broken indices |
| Baseline commit before Wave 0 | `6d0ac3a` — drop tracked test run metadata |
| Latest committed wave | Current commit — live quantum query recheck and auth cold-start timeout hardening |
| Git tag | `v1.0.0-launch-ready` (unsigned — pending GPG ceremony) |

---

## Open Items (dispatch-ready)

| ID | Task | Assigned? | Blocker |
|----|------|-----------|---------|
| W0 | State lock and evidence commit | Done | Committed `ff975b6` |
| W1 | Backend answer-engine hardening for messy queries | Done | Committed `659ded4` |
| W2 | Frontend main-flow polish and contract adapter verification | Done | Mocked browser gate passed; live local backend browser proof passed on 2026-04-30 |
| W3 | Security, tier, and audit proof | Local gate passed | Blocked query audit IDs fixed; blocked envelopes now preserve authenticated tier |
| W4 | SQL/RAG retrieval truth and regression coverage | Done locally | Committed in current Wave 4 commit; live Qdrant/PostgreSQL proof remains environment-dependent |
| W5 | C4 concurrent query/load performance closure | Local gate improved | Local 100-query P99 2094.72ms; strict 500ms/1000-user C4 still needs live Locust proof |
| W6 | Final handover package | Done | Show-readiness report and final evidence index committed |
| K-6 | GPG signatures for handover | FOUNDER ONLY | Founder private key |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

**C4 status is improved but not fully closed**. Wave 5 local TestClient evidence improved from P99 15,854.71ms to P99 2,094.72ms with 100/100 successful queries and audit IDs on every response. Do not claim strict C4 production readiness until a live Locust run passes the official target.

**Main product risk now:** strict C4 remains the only local quality-bar miss. The system is locally show-ready with a live local browser replay, but external production claims need live Locust, deployed-environment replay, production Qdrant baseline, and founder signing.

---

## Cluster-Blocked (do not re-do locally)

- Live red-team replay (`scripts/red_team_live_replay.py`) — needs target API/deployment context
- Qdrant vector baseline — local `/health` reports `ready` with 1800 vectors; production corpus baseline still needs target deployment context
- Locust 1000-user load test — needs sovereign cluster
- UX deployed browser recording + mobile Lighthouse — needs target deployment context
- GPG key ceremony + `v1.0.0-eternal` signed tag — founder-only

## Recent State-Lock Evidence

| Evidence | Status |
|----------|--------|
| `evidence/2026-04-29/p0_backend_security_and_query_closure.md` | Preserved; contains P0 security/query closure commands and results |
| `evidence/2026-04-30/00_current_state.md` | Current state lock for the next agent wave |
| `659ded4` | Latest committed backend messy-query routing and stable response-contract fix |
| `evidence/2026-04-30/wave2_frontend_main_flow_build.md` | Frontend build, mocked browser main-flow, audit/citation proof, tier comparison, and screenshot evidence |
| `evidence/2026-04-30/wave3_security_tier_audit_acceptance.md` | Security, tier, and audit proof with raw tier JSON, blocked-query evidence, and audit-chain verification |
| `evidence/2026-04-30/wave3_blocked_query_responses.json` | Raw blocked-query TestClient JSON summary with audit IDs |
| `evidence/2026-04-30/09_tier1_query_response.json` | Raw Tier 1 query response evidence |
| `evidence/2026-04-30/10_tier2_query_response.json` | Raw Tier 2 query response evidence |
| `evidence/2026-04-30/11_tier3_query_response.json` | Raw Tier 3 query response evidence |
| Current commit | Wave 3 blocked-query audit-ID fix and security/tier/audit evidence |
| `evidence/2026-04-30/wave5_performance_load_acceptance.md` | Performance report with before/after local 100-query profile, load tests, and C4 blocker |
| `evidence/2026-04-30/wave5_local_100_query_profile_after.json` | Final local 100-query profile: P99 2094.72ms, 100/100 success, audit IDs present |
| `docs/handover/SHOW_READINESS_2026-04-30.md` | Current 90-second walkthrough, evidence map, and honest blocker list |
| `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md` | Final evidence index for current handover package |
| `evidence/2026-04-30/live_full_stack_proof/README.md` | Live local full-stack proof: login, messy query, streaming answer, citation/source/audit drawers, mobile screenshot, Tier 3 blocked JSON |
| `evidence/2026-04-30/live_quantum_query_recheck/README.md` | Fresh recheck that `best quantum researchers....` returns quantum-specific SQL evidence, citations, source/audit drawers, mobile screenshot, and Tier 3 blocked JSON |
| Current commit | Live quantum query recheck and auth cold-start timeout hardening |
| `d207b54` | Prior backend messy-query fix |
| `516991a` | Verified dead artifact prune |
| `6d0ac3a` | Tracked test-run metadata removal |

---

## Key Files (agent must-reads per task type)

| Task type | Must read |
|-----------|-----------|
| Any task | `BACKLOG.md` (last 50 lines), `db_struct.sql` header, `Core_Idea_Clean.md` §1-2 |
| SQL/schema | `db_struct.sql` (full), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| Security/PII | `src/security/`, `.claude/rules/security.md` |
| API/auth | `src/api/main.py`, `src/auth/` |
| Frontend | `frontend/src/`, `.claude/rules/frontend.md` |
| Evidence | `.claude/rules/audit/protocol.md` §2 |
