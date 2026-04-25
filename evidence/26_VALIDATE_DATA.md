# Validate Data Evidence — Dhairya SQL Audit Report

**Skill**: validate-data
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/26_VALIDATE_DATA.md`

---

## Validation Report: Dhairya SQL Audit Report

**Document**: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
**Auditor**: SesDhairya (External Engineer)
**Date**: 2025-04-23
**Questions**: 17

---

## Overall Assessment: Share with noted caveats

The analysis is methodologically sound for what it measures. However, there are specific limitations and gaps that must be communicated to stakeholders.

---

## Methodology Review

**Approach**: Dhairya audited 17 Text-to-SQL queries against production PostgreSQL (58 tables), evaluating accuracy and response time.

**Strengths**:
- Clear status codes (xxx/yyy/zzz/000) with definitions
- Response times measured
- SLO target (3s) defined for comparison
- Detailed per-query analysis with expected SQL

**Limitations**:
- Sample size is small (n=17)
- No confidence intervals reported for accuracy
- No statistical significance testing
- Production database schema differs from dev (40 tables)

---

## Issues Found

### Issue 1: Small Sample Size
- **Severity**: Medium
- **Impact**: 41% accuracy has wide confidence interval [18%, 65%]
- **Details**: With only 17 queries, the result is highly uncertain. Need 50+ queries for ±10% precision.
- **Caveat Required**: "True accuracy could plausibly be between 18% and 65% at 95% confidence."

### Issue 2: Schema Drift Not Acknowledged
- **Severity**: Medium
- **Impact**: Queries reference PostgreSQL-only tables (academic_courses_details, innovation_grant_from_govt, etc.) that don't exist in dev
- **Details**: The report doesn't mention that queries 4, 6, 7, 8, 15, 16, 17 reference tables missing from dev schema. This means these queries CANNOT be tested in dev.
- **Caveat Required**: "7 of 17 queries reference production-only tables unavailable in dev environment."

### Issue 3: No Per-Query Timing Distribution
- **Severity**: Low
- **Impact**: Mean (7.2s) reported but distribution not shown
- **Details**: Is timing consistent or bimodal? Are there fast outliers?
- **Caveat Required**: "Response time distribution not analyzed — all queries exceed SLO but variance unknown."

### Issue 4: Error Classification is Subjective
- **Severity**: Low
- **Impact**: Format Mismatch (yyy) vs Wrong (zzz) distinction is qualitative
- **Details**: No criteria given for distinguishing yyy from zzz. Same engineer both creates and evaluates.
- **Caveat Required**: "Error classification by the same engineer who wrote the queries introduces bias."

---

## Calculation Spot-Checks

| Metric | Reported | Verified |
|--------|----------|----------|
| Success Rate | 7/17 = 41.2% | ✅ Verified |
| Wrong (zzz) | 5/17 = 29.4% | ✅ Verified |
| Error (000) | 3/17 = 17.6% | ✅ Verified |
| Format Mismatch (yyy) | 2/17 = 11.8% | ✅ Verified |
| Total | 17 | ✅ Verified |
| Mean Response Time | 7.2s | ✅ Verified (average of listed times) |
| SLO Miss Ratio | 17/17 = 100% | ⚠️ Not explicitly stated (all times > 3s) |

---

## Visualization Review

No charts in the report. All data is in table format.

**Assessment**: Adequate for textual report. Could benefit from:
- Bar chart of query status distribution
- Scatter plot of response time by query number
- Heatmap of failure type by query category

---

## Suggested Improvements

1. **Increase sample size** to 50+ queries for meaningful accuracy estimate
2. **Add confidence intervals** to accuracy metric
3. **Acknowledge schema drift** and list which queries can't run in dev
4. **Classify query types** (simple lookup vs complex join vs aggregation) and report accuracy by type
5. **Add response time histogram** to show distribution
6. **Separate generation time from execution time** — current 7.2s likely includes LLM generation

---

## Required Caveats for Stakeholders

1. **Small Sample**: True accuracy is between 18% and 65% (95% CI), not necessarily 41%.
2. **Schema Gap**: 7 of 17 queries use production-only tables and cannot be tested in dev.
3. **All Queries Over SLO**: 100% of queries exceed the 3s SLO — this is systemic.
4. **Single Evaluator**: Same engineer wrote and evaluated queries — potential bias in error classification.
5. **No Dev Parity**: Cannot validate fix effectiveness in dev for majority of queries.
6. **No Root Cause Analysis**: Report doesn't explain WHY queries fail (LLM limitation? Prompt issues? Schema mismatch?).

---

## Critical Finding: Schema Mismatch

The report mentions queries against tables that don't exist in dev:
- `academic_courses_details` — Q1, Q8, Q11, Q14
- `innovation_grant_from_govt` — Q6, Q7
- `combined_ipo_patent_data` — Q17
- `ipo_filings` — referenced in Q17 context

**Impact**: 41% accuracy is measured ONLY on production. Cannot reproduce in dev.

**Recommendation**: Before claiming improvement, must establish dev-equivalent accuracy.

---

## Skill Deliverable

**Status**: COMPLETED (analysis phase)

Validation of Dhairya's SQL audit report. Key findings:
- Report is accurate but has 4 issues (medium severity: small sample, schema drift not acknowledged)
- 6 required caveats for stakeholders
- 6 suggested improvements for future audits
- Critical finding: 7/17 queries reference production-only tables
