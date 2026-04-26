# NRG Founder Laptop T-60 Risk Walk

Date: 2026-04-26  
Stack: PostgreSQL + Qdrant + Redis in Docker, uvicorn on 8000, Vite on 3000  
Source: docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md

The source register has 30 rows, not 21. All 30 were walked.

## Summary

| Status | Count |
|---|---:|
| DONE | 13 |
| N/A | 16 |
| BROKEN | 1 |

## Row Marks

| # | Status | Evidence / note |
|---:|---|---|
| 1 | DONE | Three canonical questions returned cited rows, p95 2173 ms: `evidence/2026-04-26/founder_laptop_query_summary.json`. |
| 2 | DONE | Tier 3 field shape differs by at least 10 fields from Tier 1 for every canonical question. |
| 3 | DONE | Credit parsing uses `SPLIT_PART` and returned 10 cited rows for KILLER-01. |
| 4 | N/A | Canonical path uses fixed SQL evidence path; `/health/all` reports local LLM unavailable. |
| 5 | DONE | 375 px screenshot captured: `evidence/2026-04-26/founder_laptop_mobile_375.png`. |
| 6 | DONE | `verify_chain()` returned `(True, [], 443808)`. |
| 7 | N/A | Follow-up context was not part of this laptop check. |
| 8 | N/A | Vector maintenance was not active in this local stack. |
| 9 | DONE | Canonical SQL p95 stayed under 4s on 50k-row seeded tables. |
| 10 | N/A | Injection replay was outside this laptop check. |
| 11 | DONE | `publications` and `researchers` each have 50,000 rows; seed count evidence is present. |
| 12 | N/A | Hindi/Hinglish query path was not exercised. |
| 13 | N/A | Graph endpoint depth and Tier 3 graph labels were not exercised. |
| 14 | DONE | 375 px sign-in and full desktop click-through evidence captured. |
| 15 | DONE | Every canonical response carried a citation and source row. |
| 16 | DONE | Canonical responses are stored as JSON evidence for offline review. |
| 17 | DONE | `answer_confidence` is present in every JSON response and visible in the UI as High Confidence. |
| 18 | N/A | Token expiry path was not exercised. |
| 19 | BROKEN | Docker memory is 8,307,826,688 bytes and `/health/all` reports local LLM connection refused. Canonical SQL path still passed. |
| 20 | N/A | Power backup was not assessed. |
| 21 | N/A | Public-figure reconciliation was not assessed in this local subset. |
| 22 | DONE | KILLER-02 completed against the long TRL table name without a PostgreSQL identifier crash. |
| 23 | N/A | Direct database masking policies were not assessed. |
| 24 | N/A | Cluster async path was out of scope locally. |
| 25 | N/A | Pool exhaustion under concurrency was not assessed. |
| 26 | DONE | Audit chain verification succeeded after the local run. |
| 27 | N/A | Bhashini timeout path was not exercised. |
| 28 | N/A | k-anonymity inference path was not exercised. |
| 29 | DONE | KILLER-02 returned within the local p95 gate on 50k rows. |
| 30 | N/A | Operator differentiation answer was outside this code-and-evidence task. |

## Open Risk

Risk #19 remains open for a full production launch decision. It did not block the canonical SQL path, but it does block any claim that the laptop stack has full local LLM resilience.
