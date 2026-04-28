# NRG — Current Sprint State
> **Update this file at the end of every session.** Agents read this instead of BACKLOG.md for current priorities.
> Last updated: 2026-04-29

---

## System Status

| Item | State |
|------|-------|
| Quality Bar | **5/6** — C4 load bar still FAIL from latest 100-user evidence; local K-4 hot path now passes |
| Full test suite | ✅ 1585+ passed (Python 3.14 import errors in .venv, pass with Python 3.11) |
| Audit chain | ✅ valid, 24602 events (traceable genesis reseed documented in ADR-006) |
| Last commit | `6085c3b` — citation test patching and workflow evidence |
| Git tag | `v1.0.0-launch-ready` (unsigned — pending GPG ceremony) |

---

## Open Items (dispatch-ready)

| ID | Task | Assigned? | Blocker |
|----|------|-----------|---------|
| K-5A | Forbidden vocab cleanup — `forbidden_vocab_check.sh --all` exits 0 | Done locally | None |
| K-3 | Create PostgreSQL `trl_stages` VIEW + migration | Done locally | None |
| K-1 | Qdrant zero-vector must return CRITICAL in /health | Done locally | None |
| K-4 | Cold query latency <500ms P99 (code optimizations) | Verified locally | `tests/performance/test_query_latency_hot_path.py -m "slow or not slow"` passes |
| K-2 | Load test re-run (100 concurrent), fresh Locust evidence | Evidence captured, FAIL; backend profile added | Needs post-fix retry on isolated stack |
| K-6 | GPG signatures for handover | FOUNDER ONLY | Founder private key |

---

## Quality Bar

| C1 DPDP PII | C2 Audit | C3 Multi-hop | C4 SLO | C5 Drift | C6 Egress |
|:-----------:|:--------:|:------------:|:------:|:--------:|:---------:|
| ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

**C4 FAIL for load evidence**: aggregated P99=46,000ms and `/query` P99=38,000ms @ 100 users. The run had 0% request failures, but queueing under concurrency violates the latency bar. Local K-4 hot-path verification now passes after removing request-path Redis probing, full-chain audit recounting, per-request consent DDL setup, and synchronous training collector initialization. Re-run K-2 on an isolated stack before changing C4 status.

Everything else is code-complete locally.

---

## Cluster-Blocked (do not re-do locally)

- Live red-team replay (`scripts/red_team_live_replay.py`) — needs running API
- Qdrant vector baseline — needs populated Qdrant
- Locust 1000-user load test — needs sovereign cluster
- UX live browser recording + mobile Lighthouse — needs running stack
- GPG key ceremony + `v1.0.0-eternal` signed tag — founder-only

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
