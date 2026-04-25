# TP-A4 — Killer Demo Queries Preparation

**Owner:** CODER  
**Estimated Duration:** 1–2 hours  
**Blockers:** TP-A1, TP-A2, TP-A3 (must verify core features work first)  
**Reference:** `.claude/rules/ux_audit_protocol.md` Section 14

---

## Objective

Prepare 3 killer demo queries that cross ≥3 tables, produce non-obvious insights, and would make the professor lean forward. Pre-run them, verify results, time them, prepare fallback answers.

---

## Fortify Phase (Read & Design)

1. Read `db_struct.sql` — identify tables that can be joined for interesting insights:
   - `innovation_grant_from_govt` + `innovations_at_various_stages_of_technology_readiness_level` + `patents_details`
   - `financial_expenses_operational` + `financial_expenses_capital` + `incubation_details`
   - `phd_students` + `faculty_details` + `research_consultancy_details_*`
   - `nirf_*` tables for rankings

2. Read `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — understand what kinds of queries Dhairya tested. Avoid repeating the same patterns.

3. Think about what the professor actually cares about:
   - Which institutes convert research funding into patents?
   - Which research areas are over-funded vs under-performing?
   - How does faculty strength correlate with research output?
   - Which TRL stages are stuck (lots of funding but no commercialization)?

---

## Elevate Phase (Create & Verify)

### Query 1: Funding-to-Patent Conversion

```
Natural Language:
"Which institutes have the highest gap between their innovation funding
and their actual patent commercialization, and how has that changed
over the last 5 years?"

Tables Crossed:
- innovation_grant_from_govt
- innovations_at_various_stages_of_technology_readiness_level
- patents_details

Why it matters:
Shows policy effectiveness — are we funding research that translates to industry?
```

### Query 2: Faculty-to-Output Ratio

```
Natural Language:
"Which institutes have the highest research output per faculty member
in artificial intelligence and machine learning?"

Tables Crossed:
- faculty_details
- faculty_strength
- research_consultancy_details_*
- patents_details

Why it matters:
Efficiency metric — where is the talent concentrated and productive?
```

### Query 3: TRL Stagnation

```
Natural Language:
"Which research areas have the most innovations stuck at TRL 4-6
(designed/validated but not demonstrated) for more than 3 years?"

Tables Crossed:
- innovations_at_various_stages_of_technology_readiness_level
- innovation_grant_from_govt
- incubation_details

Why it matters:
Identifies the "valley of death" where research dies before commercialization.
```

### For Each Query:

1. **Write the expected SQL** based on `db_struct.sql`
2. **Pre-run via API** — time the response
3. **Verify the answer is correct** — spot-check against known data
4. **If >10 seconds:** prepare cached result, show "from cache" label
5. **If answer is wrong/null:** redesign the query or mark as "coming soon"
6. **Document the "aha" moment** — the one insight that makes the professor lean forward

---

## Immortalize Phase (Evidence)

Create:
```
evidence/2026-04-25/demo_sprint/A4_killer_queries.md
```

Format:
```markdown
# Killer Demo Queries

## Q1: [Title]
- **Question:** [Exact NL text]
- **Expected SQL:** [SQL code]
- **Tables Crossed:** [list]
- **Response Time:** [X seconds]
- **Result Verified:** YES / NO
- **Aha Moment:** [One sentence]
- **Fallback Ready:** YES / NO

## Q2: [Title]
...

## Q3: [Title]
...
```

---

## Acceptance Criteria

- [ ] 3 queries defined, each crossing ≥3 tables from `db_struct.sql`
- [ ] Each query produces a non-obvious insight (not just "list the top 5")
- [ ] Each query has been pre-run via the live API
- [ ] Response time documented for each
- [ ] Fallback answer prepared for any query that fails or is slow
- [ ] At least 1 query makes a non-technical person say "show me that again"

---

## Rollback Plan

If a query fails completely, remove it from the demo script and use a backup query. Do not demo with unverified queries.
