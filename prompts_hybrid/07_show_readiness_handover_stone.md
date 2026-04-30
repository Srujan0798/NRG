# NRG Show Readiness And Handover Stone

Use this when preparing to show NRG to the professor's assistant or another
decision-maker.

## Goal

Make the review path reliable, calm, and evidence-backed. The assistant should
see a working product, not a promise.

## Read First

- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`
- `Core_Idea_Clean.md`
- `docs/handover/SHOW_READINESS_2026-04-30.md`
- `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md`
- latest live-proof and C4 evidence under `evidence/2026-04-30/`

## Show Path

Practice and verify this exact path:

1. Open app in fresh browser profile.
2. Login as Tier 1.
3. Show dashboard scale and query box.
4. Ask the evidence-backed messy query: `best quantum researchers`.
5. Show answer, table, citations, and audit proof.
6. Ask a second already-verified query only if current evidence exists.
7. Show graph/funnel/trend view only when the verified result shape supports it.
8. Ask a PII request and show safe block.
9. Logout and login as Tier 3.
10. Ask same or similar query and show anonymized response.
11. Open audit log and verify events.
12. Copy/export answer and open the exported file to confirm row count, headers,
    tier scope, dates, and identifiers match the rendered result.

## Critical Queries

Use only queries that have already passed end-to-end verification. The current
first walkthrough query is:

1. "best quantum researchers"

Expected behavior: quantum-specific answer, SQL/source rows, citations, audit
event ID, source/proof drawer, and no generic fallback.

Current blocked safety query:

2. "Show all researcher phone numbers in clean energy"

Expected behavior: blocked response, no source rows, no PII, audit event ID.

Advanced queries below are useful only when fresh evidence exists for the
current build:

Recommended set:

1. "Show TRL progression for IIT Madras over the last three years. Which stage
   loses the most projects?"
2. "Which institutes have more than 10 crore rupees in grants and the lowest
   cost per granted patent?"
3. "Which institutes had grant funding drop by more than 40 percent year over
   year while granted patents increased?"
4. "Which institutes have strong PhD programs but low startup incubation?"
5. "Show me what an industry partner can see for AI research capabilities."

For each query prepare:

- exact text to type
- expected answer summary
- expected table columns
- expected graph if any
- expected citation/source proof
- known fallback query

## Morning-Of Checklist

### System

- backend starts
- frontend starts
- health endpoint healthy
- database reachable
- audit chain verifies
- cache prewarmed if applicable

### Security

- Tier 3 no-PII proof captured
- PII block request captured
- injection block request captured
- audit log records blocked requests

### Frontend

- login loads
- dashboard loads
- all three roles tested
- DevTools console has no red errors
- Network tab has no failed normal-flow requests
- mobile viewport checked
- projector or screen share checked

### Data

- dashboard numbers look credible or are honestly labeled
- critical queries return non-empty useful results
- no visible `null`, `undefined`, `NaN`, or raw IDs unless intentional
- sample CSV/XLSX export opens cleanly
- exported rows, headers, tier scope, long IDs, leading-zero values, and dates
  match the rendered table
- XLSX formulas validate when the file contains calculated fields

### Presenter

- exact flow rehearsed
- fallback queries ready
- local screenshots available if network fails
- one-page walkthrough guide open
- blockers known and not hidden

## Trust Answers

Prepare short answers:

### How is this different from Google Scholar or Scopus?

NRG answers cross-database research questions. It connects funding, patents,
TRL stages, courses, institutions, publications, and audit proof in one answer.
Search engines return documents; NRG returns verified structured insight.

### How do I know the answer is not fabricated?

Open the proof panel. It shows the SQL or retrieval path, source rows or
citations, audit ID, and verification status.

### What does Industry see?

Industry gets anonymized strategic capability intelligence. Individual PII and
restricted details are removed at the API layer before the response reaches the
browser.

### What if a query asks for sensitive data?

The system blocks it and records the event in the audit trail. It does not rely
on the model to decide casually.

### What is still not production?

Answer honestly from the latest acceptance report. Separate local readiness,
sovereign-cluster readiness, real-data loading, and scale validation.

Current language: NRG is locally show-ready. Local 100-user C4 smoke passed
after read-model/single-flight work. Production readiness still needs the
1000-user sovereign-cluster/deployed proof, deployed browser replay, production
Qdrant baseline, and founder signing.

## Handover Package

Prepare or refresh:

- `README.md`
- production walkthrough guide
- production readiness summary
- API contract
- security/compliance note
- operations runbook
- data intake protocol
- UAT checklist
- screenshots
- screen recording if requested
- known blockers and next actions
- commit SHA if committed, or `not committed`

## Evidence Required Before Showing

- startup/health log
- Tier 1, Tier 2, Tier 3 query JSON
- Tier 3 no-PII proof
- PII block response
- injection block response
- audit chain verify output
- critical query result screenshots
- mobile screenshot
- final acceptance report
- export integrity check for any file shown or handed over
- local C4 evidence path when performance is mentioned:
  `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`
- 1000-user cluster C4 evidence before any production-readiness claim
- if a broad validation campaign was run, include the campaign report from
  `prompts_hybrid/08_full_coverage_validation_campaign_stone.md` and list its
  coverage mode, query count, workflow count, CRITICAL/HIGH findings, and
  remaining blockers

## Stop Rule

If login, query, verified result, Tier 3 safety, or audit proof fails, do not
show the system as ready. Fix the failed gate first.
