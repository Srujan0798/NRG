# NRG — Cloud Agent Context File

> **For any cloud-based AI agent working on NRG.**
> Give these files in order. Each tier builds on the previous.

---

## TIER 1 — Project Core (Start Here)

### `Core_Idea_Clean.md`
Defines what NRG is: a 3-tier (Researcher / Government / Industry) Indian research knowledge graph.
All Hard Constraints, protocol philosophy, and the "why" of the system lives here.

### `BACKLOG.md`
Full project state at a glance — 33 protocols, quality bar scorecard (C1-C6), what's done vs pending.
Updated 2026-04-24. The single source of truth for "where are we."

### `NRG_SELF_AUDIT_REPORT_2026-04-24.md`
Recent self-audit (7.5/10) — 7 Dhairya failure patterns documented, C2/C5 gaps identified and fixed.
Read this to understand what was recently changed and why.

---

## TIER 2 — Architecture & Operations

### `docs/handover/ARCHITECTURE.md`
5-layer system architecture (API → Orchestration → Skills → Data → Infrastructure),
6-node deployment topology, Hard Constraints that must never be violated.

### `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md`
Quality Bar 6/6 evidence, DPDP Act compliance mapping per constraint.
Proof that the system meets India's data protection requirements.

### `docs/handover/OPERATIONS_RUNBOOK.md`
How to operate NRG: boot procedure, backup cadence, SLO definitions,
vector drift monitoring, incident response playbook.

### `docs/handover/DATA_INTAKE_PROTOCOL.md`
How external data enters the system — SFTP + GPG signature + HMAC verification chain.
Critical for understanding data integrity guarantees.

---

## TIER 3 — Key Source Code

### `src/audit/__init__.py` — Audit Chain
Immutable append-only HMAC-SHA256 audit log.
- Chain: each event hashed with previous hash
- Per-user binding: HMAC over (user_key : prev_hash : event)
- DB co-sign: fire-and-forget thread writes to `audit_db_cosign` table after each append
- Key rotation with dual-signature transition events
- Merkle root persisted daily

### `src/security/egress_guard/__init__.py` — Egress Firewall
Schema allowlist egress firewall — 35/35 tests passing (Quality Bar C6).
- 80+ allowed tables, 100+ allowed columns
- 25 blocked dangerous SQL patterns (DROP, TRUNCATE, pg_* etc.)
- Blocked tables that should never be queried (e.g., `users`, `audit_logs`)
- Violations are logged to `audit_violations` table

### `src/orchestration/nodes/planner.py` — Multi-Hop DAG Planner
Decomposes complex queries into a DAG of subqueries.
- Topological executor with parent→child context passing
- Handles cycles, parallel branches, multi-hop relationships
- 28 tests proving correctness (Quality Bar C3)

### `src/skills/text_to_sql/skill.py` — Text-to-SQL
Converts natural language to PostgreSQL using self-correction loop:
generate → validate → execute → retry ONCE on zero-rowcount/error.
- 42-test Dhairya regression suite
- Confidence scoring: schema_match × fewshot_similarity × validator_pass
- Hall of Shame adversarial fixtures in `src/data/schema/failed_queries/HALL_OF_SHAME.md`

### `src/security/pii/verhoeff.py` — Indian PII
Verhoeff checksum for Aadhaar numbers (not encryption — checksum validation only).
Part of Quality Bar C1 (10/10 tests passing).

### `src/config/llm_config.py` — LLM Routing
- Health-weighted routing: 1/(latency_p95 × (1+error_rate))
- Circuit breakers: 5 fail→open, 30s→half-open, 2 succ→close
- Cascade: minimax → nvidia → local → rule-based
- Cost-aware: trivial→rule-based, simple→local SLM, complex→cloud

---

## TIER 4 — Schema & Tests

### `db_struct.sql`
Official 58-table PostgreSQL schema. The production database structure.
Dev uses SQLite (18 tables). All SQL generation must target this schema.

### `src/data/schema/failed_queries/HALL_OF_SHAME.md`
5 adversarial SQL failure patterns from Dhairya's audit:
- Q4: DISTINCT ORDER BY without aggregation → GROUP BY pattern
- Q6: TRL 9 vs "Level 9" synonym mapping
- Q7: JOIN on wrong column (institute vs applicants)
- Q15: Multi-step CTE for "rising stars" vs average
- Q16: Truncated query missing HAVING clause

### `tests/security/test_per_user_audit_binding.py`
26 tests proving Quality Bar C2 — per-user audit binding works.
Tests JWT kid binding, request fingerprint binding, per-user hash verification.

### `tests/security/test_egress_allowlist.py`
35 tests proving Quality Bar C6 — egress firewall blocks dangerous queries.
Tests blocked patterns, allowed tables, violations logging.

### `scripts/vector_drift_check.py`
Drift detection: compares retrieval results against known-good benchmark queries.
SLO: drift_score >= 0.85 | WARNING < 0.60 | CRITICAL < 0.40
Daemon at `infrastructure/cron/nrg-drift-monitor` runs every 60 seconds.

---

## TIER 5 — Deployment (requires cluster access)

### `infrastructure/helm/nrg/Chart.yaml`
Helm 3 chart — 19 templates, HPA (3-20 replicas), PDB, Vault Agent sidecar,
internal CA (nrg-internal-ca), NetworkPolicies, backup CronJobs.

### `docker-compose.prod.yml`
Production Docker: multi-stage build (<300MB), nginx + TLS, zero-downtime deploy.

### `scripts/sovereign_deploy.py`
Blue-green deploy script, disaster recovery (4-hour RTO).

---

## Alembic Migrations

### `alembic/versions/add_audit_cosign_trigger_001.py`
Creates `audit_db_cosign` table (event_id PK, chain_hash, user_id, event_type, db_signature, created_at).
Run with: `alembic upgrade head`

### `alembic/versions/add_production_tables_001.py`
47-table production migration — creates the full 58-table schema.
Chained after existing migration chain.

---

## Quality Bar Scorecard (2026-04-24)

| # | Constraint | Status | Evidence |
|---|---|---|---|
| C1 | DPDP Indian PII | ✅ PASS (10/10) | `tests/security/test_pii_compliance.py` |
| C2 | Per-user audit binding | ✅ PASS (26/26) | `tests/security/test_per_user_audit_binding.py` |
| C3 | Multi-hop DAG planner | ✅ PASS (28/28) | `tests/orchestration/test_multi_hop_planner.py` |
| C4 | P99<500ms @ 1000 concurrent | ⏳ PENDING | Needs sovereign cluster |
| C5 | Vector drift auto-retrain | ✅ PASS | `scripts/vector_drift_check.py` + cron daemon |
| C6 | Schema allowlist egress | ✅ PASS (35/35) | `tests/security/test_egress_allowlist.py` |

**Overall: 5/6 PASS — C4 needs live sovereign cluster load test.**

---

## Recommended Prompt for Cloud Agent

```
Here are the core project files for NRG — an Indian research knowledge graph
with a 3-tier (Researcher / Government / Industry) access model.

START HERE:
1. Read Core_Idea_Clean.md to understand what the system is
2. Read BACKLOG.md to see current project state
3. Read NRG_SELF_AUDIT_REPORT_2026-04-24.md for recent changes

KEY RULES:
- All SQL must target the 58-table schema in db_struct.sql
- Never generate SQL that queries blocked tables (users, audit_logs)
- All PII handling must use Verhoeff checksum, not encryption
- Audit chain must never be modified after write
- Egress firewall must block all patterns in blocked_tables/blocked_columns

MY TASK: [describe what you need the agent to do]
```

---

## Files to Attach (in priority order)

```
Tier 1 (always):
  Core_Idea_Clean.md
  BACKLOG.md
  NRG_SELF_AUDIT_REPORT_2026-04-24.md

Tier 2 (for architecture/ops tasks):
  docs/handover/ARCHITECTURE.md
  docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md
  docs/handover/OPERATIONS_RUNBOOK.md
  docs/handover/DATA_INTAKE_PROTOCOL.md

Tier 3 (for code/implementation tasks):
  src/audit/__init__.py
  src/security/egress_guard/__init__.py
  src/orchestration/nodes/planner.py
  src/skills/text_to_sql/skill.py
  src/security/pii/verhoeff.py
  src/config/llm_config.py

Tier 4 (for data/quality tasks):
  db_struct.sql
  src/data/schema/failed_queries/HALL_OF_SHAME.md
  tests/security/test_per_user_audit_binding.py
  tests/security/test_egress_allowlist.py
  scripts/vector_drift_check.py

Tier 5 (for deployment tasks):
  infrastructure/helm/nrg/Chart.yaml
  docker-compose.prod.yml
  scripts/sovereign_deploy.py
```
