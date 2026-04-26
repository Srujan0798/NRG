---
name: Table partitioning + PITR backup testing for 600 GB scale
description: Composite indexes (LB-6) prevent seq-scans but do not solve maintenance. Tables expected to exceed 50M rows on the 600 GB feed must be range-partitioned by year/financial_year. Backups must be tested with point-in-time recovery (PITR) — a backup that has never been restored is not a backup.
type: feedback
---

LB-6 acceptance closes the missing-index problem on the 58-table production schema. Two additional database-engineering practices are required to survive the 600 GB load:

### 1. Range partitioning for high-cardinality tables

Tables expected to exceed ~50 million rows after the production-data import:
- `publications` (estimated 100M+ rows over 25 years)
- `combined_ipo_patent_data` (estimated 60M+ over the patent record window)
- `advance_search_data` (estimated 80M+)
- `innovation_grant_from_govt` (smaller per year but cumulative ≥ 30M)

For each: PostgreSQL declarative partitioning by `financial_year` (or `application_filing_date::date_trunc('year')` for patents). Benefits:
- Queries that filter on year prune entire partitions; ANALYZE runs faster per-partition.
- Maintenance (VACUUM, REINDEX) parallelisable per partition.
- Old partitions can be detached and archived to cheaper sovereign-cloud storage without touching the hot working set.

The semantic layer (LB-8) emits queries that the partition pruner can use; verify by `EXPLAIN (ANALYZE, BUFFERS)` showing only the relevant partition is scanned.

### 2. PITR backup testing — the only backup that counts

Master plan M2 (Database) lists "backup + restore tested" as an acceptance criterion. That criterion is hollow without explicit PITR tests:

- WAL archiving enabled to a separate sovereign-cloud bucket (NOT the same bucket as the WORM audit log — different blast radius).
- Daily `pg_basebackup` + continuous `archive_command` write-ahead-log shipping.
- **Quarterly DR drill**: spin up a fresh staging PostgreSQL, restore from the latest base backup, replay WAL to a chosen point-in-time (e.g., "12:00 IST yesterday"), verify the DB is consistent, run the 3 KILLER queries, document the wall-clock RTO. Drill report committed to `evidence/<date>/dr_drill_<quarter>.md`.
- Restore wall-clock RTO target: ≤ 4 hours. RPO target: ≤ 15 minutes (WAL ships at 15-min granularity).
- A backup that has not been restored within the last quarter is treated as broken and pages on-call.

**Why:** External reviewers consistently flag "what about disaster recovery?" Naming a backup tool is not the answer; a recent restore wall-clock is. Indian government procurement explicitly tests DR drills as part of CERT-In / MeitY clearance. Without quarterly evidence, the operator handover certification fails.

**How to apply:**
- LB-6 acceptance extended (in spirit, no protocol change required): partitioning DDL committed for the 4 named tables; partition pruner usage proven via EXPLAIN.
- Master plan M2 acceptance extended: "Quarterly PITR DR drill report under `evidence/<date>/dr_drill_*.md`; RTO ≤ 4h; RPO ≤ 15m".
- New script: `scripts/dr_drill.sh` — automates the spin-up + restore + WAL replay + smoke-test sequence; pageable when wall-clock exceeds RTO.
- Cross-reference Risk #9 (600 GB JOIN timeout) and Risk #25 (PgBouncer / connection pool) in `PRODUCTION_LAUNCH_RISK_REGISTER.md`.

**Source:** Principal Engineer & Product Auditor 2026-04-26 (Section 4). Promoted 2026-04-26.
