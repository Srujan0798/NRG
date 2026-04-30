# NRG Validation Campaign Report

Date: 2026-05-01
Starting commit: `3c043d2 docs: enforce external fusion claim boundary`
Scope: local validation-and-fix pass for backend answer contract, blocked-query security envelope, killer query evidence capture, frontend build discipline, and source-truth corpus sync.

## Result

Local validation gates passed after fixes.

This is not a whole-production perfection claim. It proves the local gates listed below. Production claims still require deployed browser replay, deployed Qdrant baseline, 1000-user sovereign-cluster load proof, and founder signing.

## Fixes Made

- Blocked `/query` security responses now return the Answer Engine blocked envelope instead of a raw `detail` body on the main query endpoint.
- Blocked response metadata no longer echoes attacker-controlled query text. `query`, `question`, and `interpreted_question` use `[blocked by security policy]`.
- Citation normalization keeps modern `id/source_id/label` fields and restores compatibility fields `title` and `publication_id`.
- Killer-query evidence capture no longer crashes when a route returns no SQL; it writes explicit no-SQL evidence instead.
- Answer Engine visible copy was centralized in `frontend/src/i18n/answer-engine.ts`.
- Frontend shared UI copy for loading and close actions now uses the i18n copy source.
- Production i18n raw-string guard now skips Storybook-only `.stories.tsx` files.

## Commands And Evidence

### Backend Contract, Security, SQL, RAG, Audit, Query Catalog

```bash
.venv/bin/pytest tests/contract tests/api/test_health_endpoints.py tests/api/test_query_security_validation.py tests/api/test_live_hybrid_stream.py tests/api/test_tier_response_filtering.py tests/security/test_prompt_injection.py tests/security/test_sql_injection_blocked.py tests/security/test_pii_indian.py tests/security/test_tier_generalization.py tests/security/test_zero_leakage.py tests/audit/test_chain_integrity.py tests/skills/test_text_to_sql.py tests/skills/test_text_to_sql_rewriter.py tests/skills/test_rag.py tests/orchestration/test_query_catalog.py tests/performance/test_query_latency_hot_path.py -q --tb=short
```

Result: `195 passed, 1 skipped, 7 deselected in 33.99s`

Evidence: `evidence/2026-05-01/validation_campaign_backend_tests.log`

### Focused Security Regression After Root Cause Fix

```bash
.venv/bin/python -m black src/api/answer_contract.py tests/contract/test_answer_engine_v1_contract.py
.venv/bin/pytest tests/security/test_sql_injection_blocked.py tests/api/test_query_security_validation.py tests/contract/test_answer_engine_v1_contract.py tests/contract/test_query_endpoint.py -q --tb=short
```

Result: `40 passed in 9.94s`

### Killer Queries

```bash
NRG_EVIDENCE_DIR=evidence/2026-05-01/validation_campaign/killer NRG_KILLER_QUERY_RUNS=3 .venv/bin/python scripts/capture_killer_query_evidence.py
```

Result: health `healthy`

- `KILLER-01`: p95 `163.99ms`, `8` rows, `1` citation
- `KILLER-02`: p95 `66.55ms`, `1` row, `2` citations
- `KILLER-03`: p95 `127.39ms`, `5` rows, `2` citations

Evidence:

- `evidence/2026-05-01/validation_campaign/killer/killer_query_health.json`
- `evidence/2026-05-01/validation_campaign/killer/killer_query_health_endpoint.json`
- `evidence/2026-05-01/validation_campaign/killer/killer_query_1_response.json`
- `evidence/2026-05-01/validation_campaign/killer/killer_query_2_response.json`
- `evidence/2026-05-01/validation_campaign/killer/killer_query_3_response.json`
- `evidence/2026-05-01/validation_campaign/killer/explain_killer_1.txt`
- `evidence/2026-05-01/validation_campaign/killer/explain_killer_2.txt`
- `evidence/2026-05-01/validation_campaign/killer/explain_killer_3.txt`
- `evidence/2026-05-01/validation_campaign_killer_output.log`

### Frontend Unit, A11y, Contract, Design-System Tests

```bash
cd frontend
npm test -- --runInBand
```

Result: `26 passed, 26 total; 97 passed, 97 total`

Evidence: `evidence/2026-05-01/validation_campaign_frontend_jest.log`

### Frontend Production Build

```bash
cd frontend
npm run build
```

Result: build passed in `42.90s`

Evidence: `evidence/2026-05-01/validation_campaign_frontend_build.log`

### Source-Truth Corpus Sync

```bash
python3 scripts/verify_corpus_sync.py
```

Result: `ok: true`; Core idea, DB schema, Dhairya audit SQL, killer queries, and schema mirrors match.

### Hygiene

```bash
git diff --check
bash scripts/forbidden_vocab_check.sh
```

Result: both passed with no output.

## Root Cause Closed

The broad suite initially failed because blocked SQL-injection envelopes returned status `200` but still included raw attacker-controlled text inside `query`, `question`, and `interpreted_question`. The security test correctly detected `hacker` echoed back in response metadata.

The fix is central: `blocked_answer_payload()` now uses a fixed placeholder for blocked query metadata. The focused SQL-injection/security/contract set and the broad backend suite both pass after this change.

## Remaining Honest Blockers

- Deployed browser replay is not proven in this campaign.
- Deployed Qdrant corpus baseline is not proven in this campaign.
- Sovereign-cluster 1000-user load is not proven in this campaign.
- Founder GPG signing remains founder-only.

## Claim Boundary

Allowed claim: local backend/security/audit/query/RAG/frontend-build/frontend-unit/killer-query gates passed for this campaign.

Not allowed claim: NRG is globally perfect or production-certified in every environment.
