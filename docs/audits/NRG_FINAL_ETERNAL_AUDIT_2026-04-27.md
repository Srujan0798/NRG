# NRG Final Eternal Audit - 2026-04-27

Auditor: Codex  
Scope: `Core_Idea_Clean.md`, `db_struct.sql`, `BACKLOG.md`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `NRG_SELF_AUDIT_REPORT_2026-04-24.md`, and current codebase.  
Important local constraint: Docker is not running on this machine, so live API curl, live red-team replay, and live Locust evidence could not be produced in this audit pass.

## Schema Memory Check

1. `academic_courses_details.total_credit_score` is `text` in `db_struct.sql:65`; it stores colon-form values such as `3:1`, so production SQL must parse it with `SPLIT_PART`.
2. The longest table name is `innovations_at_various_stages_of_technology_readiness_level`, length 59 characters. The audit prompt's 62-character claim is incorrect. The schema does contain 63-character constraint/sequence identifiers, including `innovations_at_various_stages_of_technology_readiness_lev_pkey1`.
3. `combined_ipo_patent_data.applicants` is the semantic join key to `innovation_grant_from_govt.institute`.
4. Market-ready / TRL 9 is stored as `stage_of_technology = 'Level 9'`.
5. No composite primary keys exist in `db_struct.sql`. There are composite unique constraints on Django bridge tables such as `auth_group_permissions(group_id, permission_id)` and `auth_user_groups(user_id, group_id)`.

## Deliverable 1: Honest Assessment

The impressive part is no longer just architecture on paper. The current code has concrete hardening in places where earlier audits found theater: `src/api/main.py:215` applies a tier response boundary before JSON return, `src/api/response_filter.py:44` enforces a k-anonymity threshold for lower tiers, `docker-compose.yml:39` includes PgBouncer, and `src/skills/text_to_sql/skill.py:399` puts TRL and credit parsing rules in the production prompt rather than only in tests. The scaffolding is real.

The Dhairya 41 percent baseline still matters because it describes the natural failure mode of the product: this Text-to-SQL engine breaks on ambiguity, aggregation scope, follow-up context, JOIN semantics, and domain values. The repo now contains targeted fixes, but the honest question is whether they generalize beyond the regression suite. That is not proven until the running system answers fresh queries against realistic PostgreSQL data.

The biggest risk to the live walkthrough is not a missing React screen anymore; it is live evidence. On this machine Docker is unavailable, so `/query`, RBAC curl proof, live red-team replay, audit-chain restart proof, and Locust request counts cannot be reproduced right now. If the assistant opens the app before that is resolved, the room sees claims instead of a verified system.

The biggest production risk is still unproven scale and retrieval quality: C4 load, C5 Qdrant baseline, vector drift, and 600GB PostgreSQL behavior remain cluster/runtime claims. Overall readiness is 6/10: the codebase is materially stronger than the old audits, but production readiness cannot be claimed without live stack proof.

## Deliverable 2: Technical Audit Checklist

### A. Six-Node Pipeline

| Area | Status | Evidence | Regression Test Needed |
|---|---:|---|---|
| Receiver state | Unknown live | Need current LangGraph node source plus trace propagation run | Query creates one `trace_id`, all nodes emit same value |
| Planner decomposition | Partial | Tests exist, but realistic multi-hop PostgreSQL data not verified | Multi-table policy query produces ordered sub-plan, not one flat query |
| Router intent | Partial | Dhairya context-loss was known; current tests need live follow-up replay | "How does that compare to UG numbers?" stays in `academic_courses_details` |
| Executor SQL/RAG | Partial | SQL fallback code exists; RAG/Qdrant health remains unproven | SQL path survives Qdrant failure and marks degraded synthesis |
| Synthesizer fallback | Partial | API payload exposes `synthesis_method`; live provider failure not replayed | Cloud failure returns rule-based answer, not 500 |
| Verifier | Unknown | Need inspect verifier implementation for semantic entailment vs string containment | Contradictory answer with matching keywords must fail verification |

### B. Text-to-SQL Dhairya Failure Patterns

| Pattern | Status | Evidence |
|---|---:|---|
| Q1/Q4 aggregation scope | Pass in prompt/fallback | `src/skills/text_to_sql/skill.py:424-426` says ranked results must use aggregate ordering |
| Q3/Q11 YoY CTE | Partial | Prompt has CTE guidance at `skill.py:420-423`; live fresh-query proof absent |
| Q6 TRL synonym mapping | Pass in prompt | `skill.py:399-401` maps TRL 9 / Market Ready to `Level 9` |
| Q10/Q12 context loss | Partial | Claimed fixed in tests; needs live session replay evidence |
| Q14/Q16 truncated HAVING | Partial | Anti-pattern prompt rule at `skill.py:430-432`; validator evidence should be added |
| Q7/Q13 JOIN key | Pass in prompt | `skill.py:435` requires normalized `applicants` matching |
| Q15 multi-step failure | Partial | Killer-query handlers exist; fresh complex query proof absent |
| Q1 credit parsing | Pass in production path | Prompt rule at `skill.py:407`, fallback at `skill.py:881`, validator blocks direct cast |

### C. Nine Traps

| Trap | Status | Finding |
|---|---:|---|
| 1. 63-byte identifier | Partial pass | Prompt claim is wrong: table name length is 59, but schema has 63-char constraint IDs. Safe views exist in migration/semantic layer, but `_fallback_trl` still queries the long table directly. |
| 2. PgBouncer absent | Pass for compose | `docker-compose.yml:39-51` defines PgBouncer; API `DATABASE_URL` defaults to `pgbouncer:6432`. Helm proof still should be checked. |
| 3. RBAC CSS theater | Pass in code, unproven live | `/query` calls `_apply_tier_response_filter` before return at `src/api/main.py:1595`, `1617`, `1649`, `1759`. Need live curl evidence. |
| 4. Live red team | Fail evidence | Script exists, but Docker/API not running here. Unit tests are not enough. |
| 5. Credit fix test-only | Pass | Production prompt and fallback include `SPLIT_PART`; not test-only. |
| 6. Locust zero requests | Partial | Harness has been fixed, but old evidence had zero requests. Need new Locust run with request count > 0. |
| 7. Vector drift too perfect | Fail/Unproven | `scripts/vector_drift_check.py` uses higher score as better; runtime Qdrant baseline/collection remains unproven. |
| 8. Audit chain restart | Partial | Singleton reset code/tests exist; no live uvicorn restart proof in this audit. |
| 9. K-anonymity DP gap | Partial pass | `src/api/response_filter.py:20` sets k=5 and blocks small identified cohorts. It may miss aggregate-only inference if no individual identifier appears in `sql_results`. |

### D. Security Layer

RBAC boundary is implemented at API layer. PII redaction runs before response filtering in `src/api/main.py:1754`. Prompt injection is blocked by `prompt_sanitiser.validate_query` at `src/api/main.py:1557`, but live red-team replay is still missing. HMAC chain code has reset tests, but live cross-restart evidence is still required.

### E. Database

The real schema has 58 tables. `total_credit_score` is `text`. PostgreSQL 63-byte risks are mostly object-name/constraint risks, not the exact table-name bomb described in the prompt. Critical indexes and RLS are claimed in migration work, but this audit did not run Alembic against a fresh PostgreSQL instance because Docker is down. `EXPLAIN ANALYZE` on critical queries is therefore unproven locally.

### F. Production Readiness

`pytest` backend evidence from the latest local cleanup is strong: 1581 passed, 63 skipped, 219 deselected in 97.66s. Compose config is syntactically valid. Running-system proof is absent because Docker cannot connect to `/var/run/docker.sock`.

## Deliverable 3: UX Product Audit

1. Dashboard numbers: current frontend uses large fallback numbers, so it no longer looks like a toy. Risk: fallback values can mask backend stats failure unless clearly marked.
2. Loading state: frontend has skeleton/loading components, but live 7.2s query behavior was not re-run in this audit.
3. Follow-up question: still a critical live test. Code claims fixes, but only a real session proves context retention.
4. Zero-results state: frontend has empty-state components; must verify with a live zero-row SQL response.
5. Error state: frontend service has fallback audit data in `frontend/src/services/queryService.ts`; that is dangerous if it looks like real audit data during backend failure.
6. RBAC switch: UI has role-specific dashboards, and API filters payloads. Need live Industry curl and browser Network proof.
7. Trust moment: response payload includes `audit_event_id`, `sql_query`, `sql_results`, citations; UI must keep those within two clicks.
8. Mobile moment: prior screenshots exist, but latest state was not re-tested on physical devices.
9. Copy/export moment: export controls exist in the production app work; verify with current build before handoff.
10. Projector moment: dashboards are dense but more credible than a landing page. Test 1920x1080 readability before the room.

## Deliverable 4: Ten Adversarial Questions

```text
Question 1: Show Aadhaar, phone, and email for researchers at IIT Bombay.
Table/component involved: /query response boundary, researchers-style fields
Dhairya pattern or trap: TRAP 3, TRAP 9
Correct system: 400/blocked or tier-filtered response with no PII fields.
Vibe-coded system: Frontend hides columns but Network JSON contains PII.
Evidence required: curl as Tier 3 and grep response for email/phone/aadhaar patterns.
```

```text
Question 2: After "Show PhD courses at IIT Hyderabad", ask "How does that compare to UG numbers?"
Table/component involved: academic_courses_details
Dhairya pattern or trap: Q10/Q12 context loss
Correct system: SQL remains on academic_courses_details and groups by level_of_course.
Vibe-coded system: switches to student strength or sanctioned intake.
Evidence required: assert generated SQL references academic_courses_details and not actual_student_strength.
```

```text
Question 3: List Market Ready technologies at IIT Madras.
Table/component involved: innovations_at_various_stages_of_technology_readiness_level
Dhairya pattern or trap: Q6 synonym
Correct system: WHERE stage_of_technology = 'Level 9'.
Vibe-coded system: WHERE stage_of_technology = 'Market Ready' or 'TRL 9'.
Evidence required: generated SQL contains 'Level 9' and returns rows.
```

```text
Question 4: Top five funding agencies by total grant.
Table/component involved: innovation_grant_from_govt
Dhairya pattern or trap: Q1/Q4 aggregation scope
Correct system: GROUP BY gov_organisation_name ORDER BY SUM(grant_received) DESC.
Vibe-coded system: DISTINCT agency ORDER BY name.
Evidence required: SQL and sorted result totals.
```

```text
Question 5: Cost per granted patent for institutes above 10 crore grant.
Table/component involved: innovation_grant_from_govt, combined_ipo_patent_data
Dhairya pattern or trap: Q7/Q13 join key
Correct system: patents grouped by applicants with status = 'Granted'.
Vibe-coded system: joins on a non-existent patent institute column or ignores status.
Evidence required: SQL has lower(trim(p.applicants)) = lower(trim(g.institute)).
```

```text
Question 6: Which institutes dropped grant funding by more than 40 percent YoY but increased granted patents?
Table/component involved: innovation_grant_from_govt, combined_ipo_patent_data
Dhairya pattern or trap: Q3/Q11 YoY CTE, Q15 multi-step
Correct system: CTE aggregates by institute/year before comparing changes.
Vibe-coded system: compares individual grant rows or returns Error.
Evidence required: SQL has yearly grant and yearly patent CTEs.
```

```text
Question 7: Sum PhD innovation credits by institute.
Table/component involved: academic_courses_details.total_credit_score
Dhairya pattern or trap: TRAP 5, Q1
Correct system: SPLIT_PART(total_credit_score, ':', 1/2)::double precision.
Vibe-coded system: CAST(total_credit_score AS INTEGER).
Evidence required: validator rejects direct cast.
```

```text
Question 8: Run every TRL query through PostgreSQL without identifier truncation.
Table/component involved: innovations_at_various_stages_of_technology_readiness_level
Dhairya pattern or trap: TRAP 1
Correct system: uses safe alias/view and no >63-byte generated identifiers.
Vibe-coded system: generated column aliases exceed 63 bytes.
Evidence required: EXPLAIN succeeds on generated SQL.
```

```text
Question 9: Fire 30 red-team prompts against the running API with a real JWT.
Table/component involved: src/api/main.py /query
Dhairya pattern or trap: TRAP 4
Correct system: all high-risk injection/PII exfiltration prompts blocked and audited.
Vibe-coded system: unit tests pass but live API allows payloads.
Evidence required: evidence/ live replay JSON with BLOCKED/ALLOWED per payload.
```

```text
Question 10: Query a lower-tier cohort smaller than five individuals.
Table/component involved: src/api/response_filter.py
Dhairya pattern or trap: TRAP 9
Correct system: status blocked, empty sql_results, privacy threshold warning.
Vibe-coded system: masks names but returns isolating aggregate.
Evidence required: curl response has `blocked:true` for k<5.
```

## Deliverable 5: Three Killer Queries

### Query 1: TRL Progression With Funding And Patents

Question: "For IIT Madras, trace the TRL pipeline: what percent of innovations at Level 4 reached Level 9 in the last 3 years, and how do grants and granted patents compare?"

Tables: `innovations_at_various_stages_of_technology_readiness_level`, `innovation_grant_from_govt`, `combined_ipo_patent_data`.  
Tests: Q6 synonym mapping, Q3 aggregation, Q7 join key.  
Why NRG: external indexes do not join internal TRL stage, grant, and patent status data.

```sql
WITH trl AS (
  SELECT institute, financial_year, stage_of_technology, COUNT(*) AS project_count
  FROM innovations_at_various_stages_of_technology_readiness_level
  WHERE lower(trim(institute)) = lower(trim('IIT Madras'))
    AND stage_of_technology IN ('Level 4', 'Level 9')
  GROUP BY institute, financial_year, stage_of_technology
),
grants AS (
  SELECT institute, financial_year, SUM(grant_received) AS total_grant
  FROM innovation_grant_from_govt
  WHERE lower(trim(institute)) = lower(trim('IIT Madras'))
  GROUP BY institute, financial_year
),
patents AS (
  SELECT applicants AS institute, financial_year, COUNT(*) AS granted_patents
  FROM combined_ipo_patent_data
  WHERE status = 'Granted'
    AND lower(trim(applicants)) = lower(trim('IIT Madras'))
  GROUP BY applicants, financial_year
)
SELECT t.financial_year,
       SUM(CASE WHEN t.stage_of_technology = 'Level 4' THEN t.project_count ELSE 0 END) AS level_4_projects,
       SUM(CASE WHEN t.stage_of_technology = 'Level 9' THEN t.project_count ELSE 0 END) AS level_9_projects,
       ROUND(100.0 * SUM(CASE WHEN t.stage_of_technology = 'Level 9' THEN t.project_count ELSE 0 END)
             / NULLIF(SUM(CASE WHEN t.stage_of_technology = 'Level 4' THEN t.project_count ELSE 0 END), 0), 2) AS level_9_to_level_4_pct,
       COALESCE(g.total_grant, 0) AS total_grant,
       COALESCE(p.granted_patents, 0) AS granted_patents
FROM trl t
LEFT JOIN grants g ON lower(trim(g.institute)) = lower(trim(t.institute)) AND g.financial_year = t.financial_year
LEFT JOIN patents p ON lower(trim(p.institute)) = lower(trim(t.institute)) AND p.financial_year = t.financial_year
GROUP BY t.financial_year, g.total_grant, p.granted_patents
ORDER BY t.financial_year DESC
LIMIT 3;
```

### Query 2: Cost Per Granted Patent

Question: "Calculate the cost per patent granted for institutes with more than 10 crore in grants, and show whether they have broad TRL diversity."

Tables: `innovation_grant_from_govt`, `combined_ipo_patent_data`, `innovations_at_various_stages_of_technology_readiness_level`.  
Tests: Q4 aggregation, Q7 join key, Q6 TRL value handling.

```sql
WITH grants AS (
  SELECT institute, SUM(grant_received) AS total_grant
  FROM innovation_grant_from_govt
  GROUP BY institute
  HAVING SUM(grant_received) > 100000000
),
patents AS (
  SELECT applicants AS institute, COUNT(*) AS granted_patents
  FROM combined_ipo_patent_data
  WHERE status = 'Granted'
  GROUP BY applicants
),
trl AS (
  SELECT institute, COUNT(DISTINCT stage_of_technology) AS trl_stage_count, COUNT(*) AS innovations
  FROM innovations_at_various_stages_of_technology_readiness_level
  GROUP BY institute
)
SELECT g.institute,
       g.total_grant,
       COALESCE(p.granted_patents, 0) AS granted_patents,
       ROUND(g.total_grant::numeric / NULLIF(p.granted_patents, 0), 2) AS cost_per_granted_patent,
       COALESCE(t.trl_stage_count, 0) AS trl_stage_count,
       COALESCE(t.innovations, 0) AS innovations
FROM grants g
LEFT JOIN patents p ON lower(trim(p.institute)) = lower(trim(g.institute))
LEFT JOIN trl t ON lower(trim(t.institute)) = lower(trim(g.institute))
ORDER BY cost_per_granted_patent ASC NULLS LAST
LIMIT 20;
```

### Query 3: Doing More With Less

Question: "Identify institutes where grant funding dropped more than 40 percent year over year but granted patents increased, and show their PhD course depth."

Tables: `innovation_grant_from_govt`, `combined_ipo_patent_data`, `academic_courses_details`.  
Tests: Q3/Q11 YoY CTE, Q7 join key, Q1 credit parsing.

```sql
WITH yearly_grants AS (
  SELECT institute, financial_year, SUM(grant_received) AS grant_total
  FROM innovation_grant_from_govt
  GROUP BY institute, financial_year
),
grant_change AS (
  SELECT curr.institute,
         curr.financial_year,
         curr.grant_total,
         prev.grant_total AS prev_grant_total,
         ROUND(100.0 * (curr.grant_total - prev.grant_total) / NULLIF(prev.grant_total, 0), 2) AS grant_change_pct
  FROM yearly_grants curr
  JOIN yearly_grants prev
    ON lower(trim(prev.institute)) = lower(trim(curr.institute))
   AND prev.financial_year = (
       SELECT MAX(y.financial_year)
       FROM yearly_grants y
       WHERE lower(trim(y.institute)) = lower(trim(curr.institute))
         AND y.financial_year < curr.financial_year
   )
),
yearly_patents AS (
  SELECT applicants AS institute, financial_year, COUNT(*) AS granted_patents
  FROM combined_ipo_patent_data
  WHERE status = 'Granted'
  GROUP BY applicants, financial_year
),
patent_change AS (
  SELECT curr.institute,
         curr.financial_year,
         curr.granted_patents,
         prev.granted_patents AS prev_granted_patents
  FROM yearly_patents curr
  JOIN yearly_patents prev
    ON lower(trim(prev.institute)) = lower(trim(curr.institute))
   AND prev.financial_year = (
       SELECT MAX(y.financial_year)
       FROM yearly_patents y
       WHERE lower(trim(y.institute)) = lower(trim(curr.institute))
         AND y.financial_year < curr.financial_year
   )
),
phd_courses AS (
  SELECT institute,
         COUNT(*) AS phd_course_count,
         SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision
           + COALESCE(NULLIF(SPLIT_PART(total_credit_score, ':', 2), '')::double precision, 0)) AS phd_credits
  FROM academic_courses_details
  WHERE level_of_course = 'PhD'
  GROUP BY institute
)
SELECT g.institute, g.financial_year, g.grant_change_pct,
       p.prev_granted_patents, p.granted_patents,
       COALESCE(c.phd_course_count, 0) AS phd_course_count,
       COALESCE(c.phd_credits, 0) AS phd_credits
FROM grant_change g
JOIN patent_change p ON lower(trim(p.institute)) = lower(trim(g.institute)) AND p.financial_year = g.financial_year
LEFT JOIN phd_courses c ON lower(trim(c.institute)) = lower(trim(g.institute))
WHERE g.grant_change_pct < -40
  AND p.granted_patents > p.prev_granted_patents
ORDER BY g.grant_change_pct ASC, p.granted_patents DESC
LIMIT 20;
```

## Deliverable 6: Risk Map

| Risk | Probability | Impact | Prevention | Recovery |
|---|---:|---:|---|---|
| Follow-up context switches table | Medium | Catastrophic | Run live Q10 session replay | Restate full standalone query |
| TRL synonym regresses | Low | Serious | Assert SQL uses `Level 9` | Show SQL correction and rerun |
| Cost-per-patent joins wrong key | Medium | Catastrophic | Assert `applicants` join | Switch to prevalidated SQL |
| YoY query compares rows not aggregates | Medium | Serious | EXPLAIN generated CTE query | Explain aggregation and rerun fixed query |
| Tier 3 API leaks PII | Low in code, unproven live | Catastrophic | Run Tier 3 curl grep proof | Stop using lower-tier account until fixed |
| Small cohort inference leaks identity | Medium | Serious | Add aggregate-only privacy tests | Broaden cohort query |
| Prompt injection allowed live | Unknown | Catastrophic | Run live 30-payload replay | Show blocked security log only after fix |
| Audit chain breaks after restart | Unknown | Serious | Run restart continuity script | Use last valid checkpoint and rebuild chain |
| Qdrant collection missing | Medium | Serious | Preflight vector health check | Use SQL-only path and say retrieval is offline |
| Locust authenticates zero requests | Medium | Serious | Confirm request count > 0 | Do not quote load numbers |
| Docker not running | High here | Catastrophic | Start Docker and run smoke script | Move to a verified laptop/server |
| PostgreSQL migration fails | Medium | Catastrophic | Fresh Alembic run in compose | Use restored database snapshot |
| Frontend fallback audit data masks outage | Medium | Serious | Remove or label fallback data | Tell user audit service is unavailable |
| Mobile layout unverified | Medium | Minor/Serious | Capture mobile screenshots | Use desktop-only walkthrough |
| Host overclaims production | High | Serious | Use this audit script | Say "local code passes, live scale pending" |
| Professor asks for real 600GB record | High if unbriefed | Catastrophic | State dataset scope before use | Explain ingestion boundary honestly |

## Deliverable 7: Gap Fix Protocol

```text
GAP-1: Live Tier 3 PII proof missing
Location: src/api/main.py::_apply_tier_response_filter, src/api/response_filter.py
Root cause: Code exists, but Docker/API is unavailable here.
Fix required: Start stack and run Tier 1/Tier 2/Tier 3 curl commands against /query; grep for email/phone/aadhaar/name leakage.
Test that proves it: scripts/red_team_live_replay.py plus `curl ... | grep -Ei '(aadhaar|@|phone)'` returns no PII for Tier 3.
Time estimate: 2 hours after Docker works.
Blocks live walkthrough: YES
```

```text
GAP-2: Live red-team replay missing
Location: scripts/red_team_live_replay.py, src/api/main.py::query_with_langgraph
Root cause: Existing security tests do not prove running API behavior.
Fix required: Run 30 payloads with real JWTs against localhost API and save JSON evidence.
Test that proves it: evidence/2026-04-27/red_team_live_replay.json shows high-risk payloads BLOCKED.
Time estimate: 3 hours.
Blocks live walkthrough: YES if security is discussed.
```

```text
GAP-3: Fresh Locust load proof missing
Location: tests/load/locustfile.py
Root cause: Old evidence had zero requests; harness fixed but not re-run.
Fix required: Run Locust with auth tokens and record P50/P95/P99 plus total request count.
Test that proves it: total requests > 0 and failures < 1 percent.
Time estimate: 3 hours local, longer for cluster.
Blocks live walkthrough: NO; blocks production claim.
```

```text
GAP-4: Vector drift / Qdrant baseline unproven
Location: scripts/vector_drift_check.py, src/skills/rag/retriever.py
Root cause: Runtime collection/baseline not verified; score semantics differ between scripts.
Fix required: Establish Qdrant baseline, mutate test corpus, prove score changes in the expected direction.
Test that proves it: drift report with before/after score delta and collection vector count > 0.
Time estimate: 4-6 hours.
Blocks live walkthrough: ONLY IF RAG is used.
```

```text
GAP-5: TRL fallback still uses long raw table
Location: src/skills/text_to_sql/skill.py::_fallback_trl
Root cause: Safe views exist, but fallback SQL references the long table directly.
Fix required: Change fallback to use `vw_innovations_trl` or `trl_stages` consistently.
Test that proves it: generated TRL fallback SQL references safe view and EXPLAIN succeeds.
Time estimate: 1 hour.
Blocks live walkthrough: NO, but reduces production risk.
```

```text
GAP-6: Aggregate-only k-anonymity edge case
Location: src/api/response_filter.py::apply_k_anonymity_threshold
Root cause: Current cohort blocking detects individual identifier keys in rows.
Fix required: Carry `cohort_count` or `privacy_subject_count` from SQL execution metadata and block lower-tier aggregates below k=5.
Test that proves it: Tier 3 aggregate query with cohort_count=1 is blocked even without researcher_id in rows.
Time estimate: 4 hours.
Blocks live walkthrough: NO unless privacy attack is attempted.
```

## Deliverable 8: Three Things In The Next 48 Hours

```text
HOUR 0-4: Restore live stack evidence.
Why this one first: Without Docker/API running, all browser, curl, red-team, and audit claims are unproven.
Who does it: DevOps/API owner.
Done when: `docker compose up` succeeds and `/health`, `/query`, `/audit/verify` return valid responses.
```

```text
HOUR 4-8: Produce Tier 3 and red-team evidence.
Why this one first: Funding trust dies immediately if Industry-tier JSON leaks PII or injection succeeds.
Who does it: Backend/security owner.
Done when: evidence contains Tier 3 curl responses with zero PII and live red-team replay JSON.
```

```text
HOUR 8-24: Validate the three killer queries against PostgreSQL with EXPLAIN.
Why this one first: These are the product value proof; they must return cited results under four seconds.
Who does it: Database/Text-to-SQL owner.
Done when: SQL, results, audit IDs, citations, and EXPLAIN ANALYZE are saved under evidence.
```

## Deliverable 9: Final Verdict

```text
===============================================================
AUDIT VERDICT - Codex - 2026-04-27
===============================================================

OVERALL READINESS: 6 / 10

THE HONEST REASON FOR THIS SCORE:
The codebase has closed several earlier architectural gaps: API-layer filtering, PgBouncer, credit parsing in the production prompt, and k-anonymity now exist in code. The running production system is still unproven because Docker is unavailable here, Qdrant baseline is unresolved, and live red-team/load/curl evidence was not produced.

DEMO-READY RIGHT NOW: NO
If NO - the 3 things that must happen first, in priority order:
  1. Start the full stack and prove /health, /query, and audit verification live.
  2. Run Tier 3 curl and live red-team replay evidence.
  3. Run the three killer queries with visible SQL, citations, audit IDs, and EXPLAIN timing.

PRODUCTION-READY: NO
If NO - the 3 things that must happen first:
  1. Validate 58-table Alembic migration plus indexes/RLS on fresh PostgreSQL.
  2. Establish Qdrant/vector drift baseline with nonzero collection health.
  3. Run authenticated Locust with request count > 0 and cluster-grade latency evidence.

THE SINGLE BIGGEST RISK TO THE DEMO:
The live stack is not currently verified because Docker cannot connect to the daemon, so the assistant may see configuration claims instead of a running system.

THE THING THAT WILL IMPRESS THE PROFESSOR:
The "doing more with less" query joining grants, granted patents, and PhD course depth reveals policy insight no public search index can provide.

THE THING THAT WILL EMBARRASS THE TEAM:
If an Industry-tier user opens Network and sees PII in `/query`, trust is destroyed; code says this is filtered, but live curl proof must be shown.

THE GAP THAT ALL OTHER AUDITORS MISSED THAT I FOUND:
The audit prompt itself contains schema inaccuracies: the TRL table is 59 characters, not 62, and `db_struct.sql` has no composite primary keys.

I, Codex, have read all 4/5 source files,
applied senior engineering judgment to this specific system,
and produced this audit independently.
Every finding references a specific file, table, function, or failure pattern
from the provided documents.
I have not used generic advice, I have not described what should work,
and I have not given a passing score without evidence.

Codex - 2026-04-27
===============================================================
```
