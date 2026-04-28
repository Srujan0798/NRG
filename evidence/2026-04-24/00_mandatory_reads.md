# Mandatory Source File Reads — Step 0 Confirmation

**Agent:** Codex
**Date:** 2026-04-24 protocol folder; refreshed 2026-04-28
**Protocol:** NRG ULTIMATE PRINCIPAL ENGINEER VERIFICATION & FORCED COMPLETION PROTOCOL v4.0

---

## 1. Source Files Read

| File | Read? | Key Takeaways |
|------|-------|---------------|
| `Core_Idea_Clean.md` | ✅ YES | 5-layer architecture, 6-node LangGraph, 3 tiers, zero-data-leakage, two-brain endgame SLM, 24-month roadmap |
| `db_struct.sql` | ✅ YES | 58 PostgreSQL tables documented, exact column types, composite PKs, FK relationships |
| `BACKLOG.md` | ✅ YES | Phase 3–5 claimed DONE, Quality Bar 5/6, 10 remaining handover items, GAP-A/B/C local-fixable |
| `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | ✅ YES | 41% baseline (7/17), 7 failure patterns, 7.2s avg latency vs 3s SLO |
| `docs/archive/2026-Q1/NRG_SELF_AUDIT_REPORT_2026-04-24.md` | ✅ YES | Prior local audit result, evidence failures, and the known local/cluster gap split |

---

## 2. All 58 Table Names from `db_struct.sql`

```
academic_courses_details
actual_student_strength
adv_se
advance_search_data
advance_search_data_15_12
advance_search_data_old
auth_group
auth_group_permissions
auth_permission
auth_user
auth_user_groups
auth_user_user_permissions
combined_ipo_patent_data
combined_ipo_patent_data_old
django_admin_log
django_content_type
django_migrations
django_session
expertise
faculty_details
faculty_strength
fdi_investment
fdp_details
financial_expenses_capital
financial_expenses_operational
founders_of_fortune_500_companies
incubation_details
innovation_grant_from_govt
innovations_at_various_stages_of_technology_readiness_level
ipo_patent_details_flat
ipo_patent_details_flat_old
master_expertise
nirf_extracted_table
nirf_pdf_record
nirf_table_row
package_data
patents_details
phd_students
placements_and_higher_studies
research_consultancy_details_consultancy
research_consultancy_details_sponsered
role_data
sanctioned_intake
scraped_data
scraped_data_save
scraped_raw_data
seed_funding
startup_receiving_vc_investment
startup_recognition
startup_recognition_old
startups_turnover_50_lacs
tb_academic_year_mstr
tb_course_program_types
tb_goi_ministries_mstr
tb_institute_mstr
tb_institute_scrap_data_url
user_registration
user_registration_old
```

**Note:** The 62-character table name is `innovations_at_various_stages_of_technology_readiness_level`.

---

## 3. Python Type and Format of `total_credit_score`

- **Python type:** `str`
- **SQL type:** `text` (`db_struct.sql` table `academic_courses_details`)
- **Alembic migration type:** `sa.Text()` (`src/migrations/versions/add_production_tables_001.py` line 166)
- **ORM type:** `String`/`Text` (not `Integer`)
- **Format:** `"X:Y"` where X = lecture credits, Y = tutorial credits (e.g., `"3:1"`)
- **Parsing rule:** `SPLIT_PART(total_credit_score, ':', 1)::double precision` for the lecture component

---

## 4. The 7 Dhairya Failure Patterns with Fix Applied

| Pattern | Queries | Failure | Fix Applied |
|---------|---------|---------|-------------|
| **P1: SPLIT_PART Format Blind** | Q1 | AI cast `total_credit_score` directly to integer instead of parsing `"3:1"` with `SPLIT_PART` | Enforce `SPLIT_PART(total_credit_score, ':', 1)::double precision` in SQL generation prompt + validator |
| **P2: Aggregation Scope Error** | Q4 | Used `DISTINCT` + alphabetical `ORDER BY` instead of `GROUP BY` + `ORDER BY SUM(grant_received) DESC` | Prompt rule enforces `GROUP BY + ORDER BY SUM(metric) DESC LIMIT N` for "top N by metric" queries |
| **P3: Year-Over-Year Row Comparison** | Q3, Q11 | Row-level comparison instead of CTE with `GROUP BY institute, year` then self-join | CTE pattern: aggregate by institute+year first, then self-join for YoY growth |
| **P4: TRL Synonym Leakage** | Q6 | Searched for `'TRL 9'` instead of DB value `'Level 9'` | Synonym map: `TRL-9 = TRL9 = Level 9 = Market Ready = Stage 9` → normalize to `'Level 9'` |
| **P5: Follow-Up Context Loss** | Q10, Q12 | Switched to wrong table (`actual_student_strength` / `phd_students`) on follow-up | `active_domain` persists across turns; follow-ups stay in original table context unless explicitly changed |
| **P6: JOIN Key Mismatch** | Q7, Q13 | Joined `institute` to wrong patent column; skipped `status = 'Granted'` | Join on `lower(trim(g.institute)) = lower(trim(p.applicants))` with `p.status = 'Granted'` filter |
| **P7: Multi-Stage HAVING / Complete Failure** | Q14, Q15, Q16 | Truncated SQL, missing `HAVING`, or `Error` returned | Completeness validator rejects truncated SQL; anomaly detector triggers correction or clarification fallback |

---

## 5. The 3 Local-Fixable Gaps (GAP-A, GAP-B, GAP-C) — Fix Plan

### GAP-A — DB Co-Sign Module
- **Status:** FIXED and VERIFIED
- **Files:** `src/audit/db_cosign.py` (Postgres trigger + HMAC logic), `tests/security/test_per_user_audit_binding.py`
- **Fix:** Created `DBCoSignStore` singleton, `compute_db_cosign_hmac()`, `generate_audit_cosign_trigger_sql()`, `verify_db_cosign()`. Postgres trigger `audit_cosign_trigger` fires on INSERT to `audit_events` and writes `db_cosign_hmac` using `hmac()` inside the database.
- **Tests:** `TestDatabaseCoSign` — 3/3 passed (deterministic HMAC, trigger DDL contains required clauses, recent verify reports disabled when DB absent)
- **Git hash:** `b873b71`

### GAP-B — 60-Second Drift Scheduler
- **Status:** FIXED and VERIFIED
- **Files:** `scripts/vector_drift_scheduler.py`, `tests/scripts/test_vector_drift_scheduler.py`, `tests/observability/test_vector_drift_scheduler.py`
- **Fix:** Added `scheduler_loop()` with `asyncio.sleep(60)`, `run_once()` calls drift check and emits to `/api/reindex` on threshold breach (`COSINE_SHIFT_THRESHOLD = 0.05`). Supports `--once`, `--dry-run`, `--interval-seconds`.
- **Tests:** 12 passed in `tests/scripts/test_vector_drift_scheduler.py` (trigger logic, loop, interval), 4 passed in `tests/observability/test_vector_drift_scheduler.py` (60s interval, sleep, reindex)
- **Git hash:** `527af23`

### GAP-C — HALL_OF_SHAME.md
- **Status:** FIXED and VERIFIED
- **File:** `src/data/schema/failed_queries/HALL_OF_SHAME.md`
- **Fix:** Created with all 7 Dhairya failure patterns (P1–P7). Each pattern includes: original question, wrong SQL generated, why it failed, fix applied, and test covering it.
- **Git hash:** `4c743b8`

---

*Step 0 complete. Proceeding to evidence generation.*
