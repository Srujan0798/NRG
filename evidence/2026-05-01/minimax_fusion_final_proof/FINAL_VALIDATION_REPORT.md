# Minimax Hybrid Fusion Final Proof Matrix

Date: 2026-05-01
Starting commit: `d73fb0e fix: harden fused error recovery surface`

## Scope

This pass re-used `.claude/skills/hybrid-mvp-fusion/SKILL.md` and
`.claude/skills/nrg-validation-campaign/SKILL.md` for the repeated founder
request to prove the Minimax Desktop source has been fully handled without
false "100%" claims.

External source:

- `/Users/srujansai/Desktop/Minimax_mvp`

Status separation:

- `inventory-accounted`: PASS. The 84-file Desktop source was already fully
  classified in `evidence/2026-05-01/minimax_fusion_final_inventory_review.md`.
- `value-integrated`: PASS for the useful values accepted so far. NRG-native
  changes from the external source include role-aware starter questions, answer
  context, validation matrix rows, and safe error recovery.
- `product-proven`: PASS for the local validation slice below. BLOCKED for
  deployed production gates.

The external Desktop folder was not deleted. It remains source material outside
the repo. Direct tree replacement remains rejected because the external backend,
auth, SQLite schema, CORS defaults, hardcoded data, and raw stack-trace error
boundary conflict with NRG source truth.

## Important Finding During This Pass

The first browser proof failed twice for environment reasons and revealed why
proof must name its target:

1. `PLAYWRIGHT_PORT=3000` reused an existing Vite-only server, so `/login`
   returned `500`.
2. An SSH listener was bound on local port `8000`, so the E2E proxy hit a
   remote/stale backend with AI synthesis enabled. That backend returned a weak
   fast-path answer for `best quantum researchers....`.
3. After starting the current local NRG backend on `127.0.0.1:8017` with
   `NRG_AI_SYNTHESIZE_FAST_PATHS=false` and setting
   `API_TARGET=127.0.0.1:8017`, the live browser proof passed.

This is why future proof runs must set both `PLAYWRIGHT_PORT` and `API_TARGET`
explicitly when another service already owns ports 3000 or 8000.

## Commands Run

Backend contract/security/query/RAG/audit/hot-path slice:

```bash
.venv/bin/pytest tests/contract tests/api/test_health_endpoints.py tests/api/test_query_security_validation.py tests/api/test_live_hybrid_stream.py tests/api/test_tier_response_filtering.py tests/security/test_prompt_injection.py tests/security/test_sql_injection_blocked.py tests/security/test_pii_indian.py tests/security/test_tier_generalization.py tests/security/test_zero_leakage.py tests/audit/test_chain_integrity.py tests/skills/test_text_to_sql.py tests/skills/test_text_to_sql_rewriter.py tests/skills/test_rag.py tests/orchestration/test_query_catalog.py tests/performance/test_query_latency_hot_path.py -q --tb=short
```

Result:

```text
195 passed, 1 skipped, 7 deselected in 26.17s
```

Killer query capture:

```bash
NRG_EVIDENCE_DIR=evidence/2026-05-01/minimax_fusion_final_proof/killer NRG_KILLER_QUERY_RUNS=3 .venv/bin/python scripts/capture_killer_query_evidence.py
```

Result:

```text
status: healthy
KILLER-01 p95 43.57ms, rows 8, citations 1
KILLER-02 p95 29.31ms, rows 1, citations 2
KILLER-03 p95 20.82ms, rows 5, citations 2
```

Frontend Jest:

```bash
npm --prefix frontend test -- --runInBand
```

Result:

```text
27 test suites passed
99 tests passed
```

Frontend production build:

```bash
npm --prefix frontend run build
```

Result:

```text
2637 modules transformed
built in 27.08s
```

Corpus source-truth sync:

```bash
python3 scripts/verify_corpus_sync.py
```

Result:

```text
"ok": true
Core_Idea_Clean.md: match
db_struct.sql: match
SQL_AUDIT_RAW_dhairya.sql: match
killer_queries.yaml: match
```

Live browser proof against current local backend:

```bash
NRG_AI_SYNTHESIZE_FAST_PATHS=false .venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8017
PLAYWRIGHT_PORT=3318 API_TARGET=127.0.0.1:8017 NRG_EVIDENCE_DIR=../evidence/2026-05-01/minimax_fusion_final_proof/browser_local npm --prefix frontend run test:e2e -- -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts
```

Result:

```text
1 passed (10.8s)
```

External production gate runner:

```bash
python3 scripts/run_final_external_gates.py --evidence-dir evidence/2026-05-01/minimax_fusion_final_proof/external_gates
```

Result:

```text
Overall status: BLOCKED
```

## Evidence Paths

- Backend/security/query/RAG/audit log:
  `evidence/2026-05-01/minimax_fusion_final_proof/backend_security_query_audit.log`
- Killer-query evidence:
  `evidence/2026-05-01/minimax_fusion_final_proof/killer/`
- Frontend Jest:
  `evidence/2026-05-01/minimax_fusion_final_proof/frontend_jest.log`
- Frontend build:
  `evidence/2026-05-01/minimax_fusion_final_proof/frontend_build.log`
- Corpus sync:
  `evidence/2026-05-01/minimax_fusion_final_proof/corpus_sync.json`
- Passing browser proof:
  `evidence/2026-05-01/minimax_fusion_final_proof/browser_local/`
- Browser proof command log:
  `evidence/2026-05-01/minimax_fusion_final_proof/live_quantum_browser_local.log`
- Blocked external gates:
  `evidence/2026-05-01/minimax_fusion_final_proof/external_gates/EXTERNAL_GATE_SUMMARY.md`

Browser proof artifacts include:

- `02_login_desktop.png`
- `03_researcher_dashboard_desktop.png`
- `04_streaming_planning_desktop.png`
- `05_quantum_answer_verified_desktop.png`
- `06_citation_drawer_desktop.png`
- `07_source_data_drawer_desktop.png`
- `08_audit_proof_drawer_desktop.png`
- `09_quantum_answer_verified_mobile.png`
- `10_tier3_blocked_quantum_pii_query.json`
- `console_errors.json` with `[]`
- WebM recording of the flow

## Product-Proof Matrix

| Surface | Status | Evidence |
| --- | --- | --- |
| Appearance | PASS for local answer-engine path | Desktop and mobile screenshots in `browser_local/` |
| UI/UX main flow | PASS for local path | Login -> dashboard -> messy query -> streaming -> answer -> citation -> source -> audit -> mobile in `live_quantum_browser_local.log` |
| Query intelligence | PASS for covered local slice | `best quantum researchers....` raw JSON plus KILLER-01/02/03 health |
| Database/schema | PASS for local source-truth sync | `corpus_sync.json`, `db_struct.sql` mirror match |
| Dhairya SQL audit | PASS for covered regression slice | backend suite includes Text-to-SQL, contract, query catalog, and killer query capture |
| Backend/API | PASS for local contract/security slice | `backend_security_query_audit.log`, browser raw JSON with audit ID/citations/source rows |
| Retrieval | PASS for local SQL/RAG test slice | backend suite includes `tests/skills/test_rag.py`; killer query capture healthy |
| Security/tier | PASS for local blocked PII/Tier 3 slice | `10_tier3_blocked_quantum_pii_query.json`; security tests in backend suite |
| Audit | PASS for local tests and browser event IDs | `tests/audit/test_chain_integrity.py` passed; browser JSON has audit IDs |
| Accessibility | PASS for local Jest/contrast slice | frontend Jest includes a11y contrast and component tests |
| Performance | PASS for local hot-path slice; production BLOCKED | `tests/performance/test_query_latency_hot_path.py` passed; external gates block cluster C4 |
| Evidence | PASS | This report plus logs/screenshots/raw JSON under `minimax_fusion_final_proof/` |
| Production | BLOCKED | Missing deployed frontend/API URLs, production Qdrant target, explicit cluster-load run, founder GPG signatures |

## Final Claim Boundary

Allowed claim:

- The Minimax Desktop source has been inventoried and mined for useful value.
- Safe external value has been adapted into NRG-native code/tests/workflow where
  appropriate.
- The current NRG local answer-engine path is stronger than the external bundle
  for the covered local surfaces because it has real tiering, citations, source
  rows, audit IDs, security blocks, and browser proof.

Not allowed claim:

- NRG is 100% perfect in every environment.
- NRG is production-ready across deployed infrastructure.
- Every possible query, viewport, accessibility path, and production load case
  has been proven.

Those claims remain blocked by the external gate report until deployed replay,
production Qdrant baseline, 1000-user sovereign-cluster C4, and founder signing
are completed on the correct environment.
