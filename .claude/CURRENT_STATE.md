# NRG — Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-04-30

---

## System Status

| Item | State |
|------|-------|
| Repo structure | Cleaned and pruned; tracked dead docs/components/scripts removed in `516991a`, tracked test-run metadata removed in `6d0ac3a` |
| Working tree | Wave 1 and Wave 4 backend/retrieval fixes are committed; Wave 2 frontend compile fix is in progress; unrelated cleanup deletions and new ADR files remain uncommitted |
| Quality Bar | **Not re-certified after cleanup** — last known state was 5/6 with C4 load bar failing |
| Full test suite | Not rerun in this session; use Python 3.11 venv for reliable results |
| Targeted recent checks | Wave 1 API tests, Wave 4 SQL/RAG/health tests, and Wave 2 frontend build/component-contract tests passed in targeted runs |
| Audit chain | Last known valid from prior evidence; rerun `scripts/audit_investigate.py` before any fresh audit claim |
| Baseline commit before Wave 0 | `6d0ac3a` — drop tracked test run metadata |
| Latest committed wave | Wave 4 retrieval/schema health (current commit); `659ded4` Wave 1 messy query routing |
| Git tag | `v1.0.0-launch-ready` (unsigned — pending GPG ceremony) |

---

## Open Items (dispatch-ready)

| ID | Task | Assigned? | Blocker |
|----|------|-----------|---------|
| W0 | State lock and evidence commit | Done | Committed `ff975b6` |
| W1 | Backend answer-engine hardening for messy queries | Done | Committed `659ded4` |
| W2 | Frontend main-flow polish and contract adapter verification | Build gate fixed | Browser screenshots and live main-flow proof still pending |
| W3 | Security, tier, and audit proof | Pending W1 | Needs audit IDs on query responses |
| W4 | SQL/RAG retrieval truth and regression coverage | Done locally | Committed in current Wave 4 commit; live Qdrant/PostgreSQL proof remains environment-dependent |
| W5 | C4 concurrent query/load performance closure | Pending W1 backend path | Last known 100-user evidence failed |
| W6 | Final handover package | Last | Requires evidence from W1-W5 |
| K-6 | GPG signatures for handover | FOUNDER ONLY | Founder private key |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

**C4 status must be treated as stale until rerun**. Prior evidence said the 100-user rerun failed with P95=9,500ms, P99=13,000ms, 0.45% failure rate, and 20.21 RPS. Do not claim load readiness without fresh Wave 5 evidence.

**Main product risk now:** answer-engine relevance for messy natural-language queries. The next implementation wave must focus on backend query classification/retrieval and proof-bearing answer contracts before more UI polish or cleanup.

---

## Cluster-Blocked (do not re-do locally)

- Live red-team replay (`scripts/red_team_live_replay.py`) — needs running API
- Qdrant vector baseline — needs populated Qdrant
- Locust 1000-user load test — needs sovereign cluster
- UX live browser recording + mobile Lighthouse — needs running stack
- GPG key ceremony + `v1.0.0-eternal` signed tag — founder-only

## Recent State-Lock Evidence

| Evidence | Status |
|----------|--------|
| `evidence/2026-04-29/p0_backend_security_and_query_closure.md` | Preserved; contains P0 security/query closure commands and results |
| `evidence/2026-04-30/00_current_state.md` | Current state lock for the next agent wave |
| `659ded4` | Latest committed backend messy-query routing and stable response-contract fix |
| `evidence/2026-04-30/wave2_frontend_main_flow_build.md` | Frontend compile failure/fix evidence for the deleted `PersonaSheet` dependency |
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
