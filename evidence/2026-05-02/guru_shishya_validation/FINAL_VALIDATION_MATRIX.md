# Guru/Shishya Validation Matrix

Date: 2026-05-02
Base commit: `0db43517d47e3d69cb6b2720842b9b1edeaa277c`

This report is an evidence matrix for the current local checkout. It is not a
production-readiness certificate.

## Verdict

| Surface | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Repo hygiene and source truth | PASS | `01_git_status_start.log`, `06_corpus_sync.log`, `07_forbidden_vocab.log` | Source-truth mirror is synced; forbidden-vocabulary guard passed. |
| Agent workflow hygiene | PASS | `05_existing_diff_start.patch`, `../00_current_state.md` | Duplicate untracked skill imports were removed; root `AGENTS.md` is now a short execution entry point. |
| Backend/API contracts | PASS | `22_backend_security_query_suite_after_stream_fix.log` | 195 passed, 1 skipped, 7 deselected. |
| Query intelligence and answer contract | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `18_stream_wiring_regression.log`, `killer/` | Messy query, stream payload, citation, audit ID, tier response, and contract slices passed. |
| Dhairya SQL regression | PASS | `10_dhairya_sql_regression.log` | 57 passed, 31 deselected. |
| Database/schema truth | PASS | `06_corpus_sync.log`, `24_live_health.json` | Corpus/schema mirrors match; local DB is healthy with 76 tables, 5,615 researchers, and 100,000 publications. |
| Retrieval/RAG live dependency | BLOCKED | `24_live_health.json`, `27_live_health_all.json` | Qdrant is unavailable on this local run, so live RAG retrieval is degraded even though unit tests pass. |
| Security, PII, injection, tier safety | PASS | `22_backend_security_query_suite_after_stream_fix.log`, `25_quality_bar_scorecard_with_live_api.log` | DPDP, per-user audit binding, prompt/SQL injection, egress, and tier filtering checks passed. |
| Audit/HMAC chain | PASS | `12_audit_investigate.log`, `19_audit_verify_chain_corrected.log` | Corrected chain verification reports valid chain, 0 errors. |
| Frontend unit/UI contract | PASS | `28_frontend_jest_after_install.log`, `29_frontend_build_after_install.log` | 99 frontend tests passed; production build passed. |
| Live browser main query flow | PASS | `live_quantum_recheck/` | Desktop/mobile screenshots, video, citation drawer, source-data drawer, audit-proof drawer, console-error capture, raw Researcher JSON, and Tier 3 blocked JSON were captured for the messy quantum researcher flow. |
| Accessibility contrast | PASS | `30_frontend_contrast_after_install.log` | 20 WCAG token contrast tests passed. |
| Live local health | DEGRADED | `24_live_health.json`, `27_live_health_all.json` | `/health` is healthy overall, but `/health/all` is degraded because Qdrant and Redis are unavailable. |
| C4 performance/load | FAIL | `25_quality_bar_scorecard_with_live_api.log`, `31_c4_scorecard_raw_summary.log` | 1000-user local run attempted, but C4 failed: request failures occurred, P99 target was not met, and Locust report writing failed because `.cache/locust_report.html` parent path was missing. |
| Evidence discipline | PASS | `00_guru_assignment_protocol.md`, this file | All major claims are mapped to evidence files. |
| External production gates | BLOCKED | `../final_external_gates/EXTERNAL_GATE_SUMMARY.md` | Missing deployed frontend/API URLs, production Qdrant target, explicit cluster-load flag, and founder GPG signatures. |

## Fixes Preserved In This Wave

- Extracted query response support helpers from `src/api/main.py` into
  `src/api/query_response_utils.py`.
- Fixed extracted logging to match `StructuredLogger` call shape.
- Fixed query stream router wiring to pass keyword-only arguments correctly.
- Added root `AGENTS.md` as a concise agent entry point and ignored local
  `.codex/` / `.npm-cache/` artifacts.

## Do Not Claim Yet

- Do not claim full production readiness.
- Do not claim C4 compliance.
- Do not claim live RAG is fully operational in this local run.
- Do not claim deployed-browser or production-cluster proof until external
  gates are rerun with the required target URLs, Qdrant, cluster context, and
  founder signing key.

## Next Engineering Target

Close local full-stack health and C4:

1. Start or compose Qdrant and Redis for local validation.
2. Ensure `.cache/` exists before Locust writes HTML reports, or make the
   runner create the parent directory.
3. Re-profile `/query` under load and eliminate the observed failures.
4. Rerun the quality-bar scorecard and update evidence only after C4 passes.
