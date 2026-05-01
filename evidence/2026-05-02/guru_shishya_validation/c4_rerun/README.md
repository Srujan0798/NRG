# C4 Rerun Closure Note

Date: 2026-05-02

This folder records the C4 follow-up after the Guru/Shishya validation matrix. It is not a C4 pass certificate.

## What Changed

- `scripts/quality_bar_scorecard.py` now runs the maintained C4 Locust workload in `tests/load/locustfile_c4.py` instead of the older generic load file.
- The scorecard creates the `.cache/locust_report.html` parent directory before invoking Locust.
- The scorecard pre-issues persona tokens before Locust starts so C4 measures `/query` load instead of login/replay churn.
- The C4 parser now requires measured numeric evidence: requested users, Locust exit code, P99, failure rate, and sample count.
- The C4 parser now reports per-workload `/query` metrics from Locust HTML: researcher, government, and adversarial.
- The C4 parser now reads the real Locust `window.templateArgs` HTML payload, not only small synthetic report fragments.
- `src/api/main.py` now has opt-in query-stage profiling via `NRG_QUERY_STAGE_PROFILE=1`, `NRG_QUERY_STAGE_PROFILE_FILE`, and `NRG_QUERY_STAGE_PROFILE_SAMPLE_RATE`.
- `tests/load/locustfile_c4.py` now fails HTTP 429 responses instead of counting rate limiting as success.
- `tests/load/locustfile_c4.py` no longer sends synthetic `X-Forwarded-For` headers when using a preissued token. This fixed the JWT replay failure storm.
- `src/services/consent.py` now caches repeated `has_consent()` checks for a short TTL and invalidates on grant, revoke, and erase, reducing repeated consent-ledger reads on the query hot path.
- `src/audit/__init__.py` now avoids repeated same-process JSONL tail rereads after the process has established the current tail, and precomputes immutable event serialization before entering the audit file-lock critical section.

## Evidence

| Evidence | Result |
| --- | --- |
| `12_c4_runner_contract_tests_after_token_fix.log` | Scorecard contract tests passed after token replay fix. |
| `16_c4_runner_contract_tests_after_report_parse.log` | 12 scorecard/parser tests passed after Locust HTML report parsing. |
| `42_scorecard_contract_tests_after_token_report_fix.log` | Final targeted scorecard/Locust contract tests passed: 12 passed. |
| `18_quality_bar_scorecard_60s_after_report_parse.json` | 1000 users, 0 failures, but P99 9900 ms in 60-second local run. |
| `26_quality_bar_scorecard_5m_quiet_api_heartbeat.json` | 1000 users, 0 failures, 73,133 samples, P99 4600 ms in 5-minute local run. |
| `27_locust_report_5m_quiet_api.html` | Locust HTML report for the 5-minute quiet API run. |
| `33_quality_bar_scorecard_60s_4workers.json` | 1000 users, 0 failures, 27,765 samples, P99 4500 ms with 4 local API workers. |
| `34_locust_report_60s_4workers.html` | Locust HTML report for the 4-worker diagnostic run. |
| `29_sequential_query_latency_probe.log` | Warm sequential queries are fast, mostly 5-45 ms with citations and audit IDs. |
| `29_consent_cache_tests.log` | Consent service cache regression tests passed: 18 passed. |
| `43_final_local_verification.md` | Final focused verification passed: 30 targeted tests, compileall, diff check, corpus sync, forbidden vocabulary, and no leftover load/API processes. |
| `44_c4_truth_contract_after_429_endpoint_metrics.md` | C4 truth contract passed: 429 fails, query metrics split by workload, scorecard exposes per-workload failure/P99 metrics. Follow-up 4-worker diagnostic reparse shows 37,174 samples, 0 failures, aggregate P99 3100 ms, and adversarial query P99 6400 ms. |
| `44b_scorecard_locust_contract_tests_after_real_report_parser.log` | Scorecard/Locust contract tests passed after fixing real Locust report parsing: 15 passed. |
| `45_query_stage_profile_4workers.jsonl` | Opt-in sampled query-stage profile from a 60-second 4-worker C4 run: 7,179 sampled requests. |
| `48b_quality_bar_scorecard_60s_profile_4workers_locust_metrics.json` | Reparsed real Locust report metrics: 37,174 samples, 0 failures, aggregate P99 3100 ms, researcher P99 2700 ms, government P99 3000 ms, adversarial P99 6400 ms. |
| `50_query_stage_profile_summary.md` | Hot-path summary: cache-hit requests are sub-millisecond; cold/cache-miss path is dominated by audit append and singleflight wait. |
| `51_py_compile_after_profile.log` | `src/api/main.py`, `scripts/quality_bar_scorecard.py`, and `tests/load/locustfile_c4.py` compile. |
| `52_scorecard_locust_contract_tests_final_profile.log` | Final targeted scorecard/Locust contract tests passed: 16 passed. |
| `54_corpus_sync_after_profile.log` | Corpus/source-truth sync passed. |
| `55_forbidden_vocab_after_profile.log` | Forbidden vocabulary guard passed. |
| `56_no_leftover_port_8000_after_profile.log` | No leftover host listener on port 8000 after the profiled run. |
| `57_git_diff_check_after_restore.log` | Final `git diff --check` passed after restoring generated scorecard JSON. |
| `58_request_envelope_profiler.md` | Added opt-in request-envelope JSONL profiler to compare middleware/serialization/request timing against query-stage timing in the next C4 run. |
| `58_audit_tail_cache_test_red.log` | Red test proving the old append path reread the chain tail on every same-process append: failed with 5 tail reads. |
| `59_audit_tail_cache_targeted_green.log` | Tail-cache targeted tests passed after the fix: cached tail reuse, stale writer refresh, and concurrent appends. |
| `60_audit_chain_security_after_tail_cache.log` | Audit/per-user/cosign safety suite passed after tail-cache change: 87 passed. |
| `68_audit_chain_security_after_critical_section.log` | Audit/per-user/cosign safety suite passed after critical-section reduction: 87 passed. |
| `72_quality_bar_scorecard_60s_after_critical_section.json` | Final post-change scorecard still fails C4: 5/6 overall, C4 failed. |
| `73_locust_report_60s_after_critical_section.html` | Final post-change Locust report. |
| `74_query_stage_profile_summary_after_critical_section.md` | Final post-change profile: 29,168 samples, 0 failures, aggregate P99 3000 ms; cache hits remain fast, cold audit/singleflight still dominate app-stage tail. |
| `75_py_compile_final_after_audit_hotpath.log` | Final compile check passed for audit, API, scorecard, and C4 Locust files. |
| `76_final_targeted_tests_after_audit_hotpath.log` | Final targeted audit/scorecard/Locust tests passed: 103 passed. |
| `77_git_diff_check_final_after_audit_hotpath.log` | Final `git diff --check` passed. |
| `78_corpus_sync_final_after_audit_hotpath.log` | Final corpus/source-truth sync passed. |
| `79_forbidden_vocab_final_after_audit_hotpath.log` | Final forbidden vocabulary guard passed. |
| `80_no_leftover_port_8000_final_after_audit_hotpath.log` | No leftover host listener on port 8000. |
| `75_rate_limit_and_quota_mode_boundary.md` | Clarifies that quota-on C4 needs distinct load identities, while `NRG_QUOTA_DISABLED=1` is capacity-only evidence. |
| `86_combined_query_envelope_profile_summary.md` | Combined query-stage plus request-envelope profile: Locust aggregate P99 1000 ms, server `/query` envelope P99 538.303 ms, sampled route-handler P99 1.589 ms, 0 failures. |
| `89_c4_declared_prewarm_no_profile.json` | Declared C4 workload prewarm: 312 requests across researcher, government, and adversarial personas, 0 failures, audit IDs present. |
| `91_quality_bar_scorecard_60s_declared_prewarm_no_profile.json` | Warmed no-profile 60-second scorecard: 1000 users, 45,559 samples, 0 failures, aggregate P99 2100 ms, C4 failed. |
| `92_locust_report_60s_declared_prewarm_no_profile.html` | Locust HTML report for the warmed no-profile diagnostic. |
| `93_declared_prewarm_no_profile_summary.md` | Summary of the warmed no-profile diagnostic: researcher P99 2100 ms, government P99 2100 ms, adversarial P99 2400 ms. |
| `94_no_leftover_port_8000_after_prewarm_no_profile.log` | No leftover host listener on port 8000 after the warmed no-profile diagnostic. |
| `95_py_compile_final_after_prewarm_diag.log` | Final compile check passed for audit, API, scorecard, and C4 Locust files. |
| `96_git_diff_check_final_after_prewarm_diag.log` | Final `git diff --check` passed. |
| `97_corpus_sync_final_after_prewarm_diag.log` | Final corpus/source-truth sync passed. |
| `98_forbidden_vocab_final_after_prewarm_diag.log` | Final forbidden vocabulary guard passed. |
| `99_final_targeted_tests_after_prewarm_diag.log` | Final targeted audit/scorecard/Locust/API profiler tests passed: 106 passed. |
| `100_no_leftover_port_8000_final_after_prewarm_diag.log` | No leftover host listener on port 8000. |
| `113_c4_prewarm_after_query_middleware_skip.json` | Duplicate `/query` middleware-sanitiser work removed; declared prewarm passed 312/312, median 3.135 ms. |
| `115_quality_bar_scorecard_60s_after_query_middleware_skip.json` | 1000 users, 35,428 samples, 0 failures, aggregate P99 2700 ms, C4 failed. |
| `133_quality_bar_scorecard_60s_asgi_middleware_4workers.json` | Pure ASGI middleware diagnostic: 1000 users, 47,233 samples, 0 failures, aggregate P99 970 ms, C4 failed but best stable local result so far. |
| `127_quality_bar_scorecard_60s_asgi_middleware_8workers.json` | 8-worker/backlog diagnostic rejected as improvement: 22.09% failure rate, aggregate P99 7800 ms. |
| `139_quality_bar_scorecard_60s_asgi_authcache_4workers.json` | Auth-cache diagnostic: 1000 users, 45,249 samples, 0 failures, aggregate P99 1200 ms; not a C4 closure. |
| `142_asgi_middleware_authcache_summary.md` | Summary of duplicate middleware removal, ASGI middleware conversion, verified-token cache, and current C4 status. |
| `136_quality_bar_scorecard_60s_4workers_uvloop_httptools_locust4.json` | Negative multi-process Locust diagnostic: `locust_processes=4`, failure rate 99.53%, mostly HTTP 0. Not pass evidence. |
| `144_multilocust_and_topology_followup.md` | Documents multi-process Locust tooling, failed local multi-process evidence, and local Docker/Colima topology blocker. |

## Current C4 Status

C4 remains **FAIL**. The runner/auth defects are fixed, but the measured 1000-user P99 target is not met on this local machine.

A 60-second after-cache probe showed lower early latency but is invalid as C4 evidence because the API process shut down during the run and produced HTTP 0 failures. Do not use that probe as a pass claim.

The root-cause boundary moved:

- Previous blocker: C4 run was polluted by JWT replay failures and weak metric parsing.
- Current blocker: `/query` succeeds with zero failures but queues under 1000-user Locust load; local P99 remains above the 500 ms target. The latest warmed no-profile 4-worker 60-second diagnostic reports 45,559 samples, 0 failures, aggregate P99 2100 ms, researcher P99 2100 ms, government P99 2100 ms, and adversarial query P99 2400 ms.
- Latest blocker update: pure ASGI middleware reduced the best stable local aggregate P99 to 970 ms with 47,233 samples and 0 failures, but this still misses the 500 ms C4 gate. The 8-worker topology created HTTP 0 failures and is not an improvement.
- Profile finding: sampled cache-hit route-handler work is low millisecond to sub-millisecond, while the full server request envelope and Locust client-observed timings are much larger under burst load. Combined profile evidence shows route-handler P99 1.589 ms, server `/query` envelope P99 538.303 ms, and client-observed aggregate P99 1000 ms in the same diagnostic window.
- Warmed-read-model finding: declared prewarm removed cold-key setup from the test, but P99 still missed the 500 ms gate. The remaining problem is not only cold cache creation; request lifecycle, queueing, transport scheduling, worker concurrency, and audit-envelope behavior remain the likely boundary.
- New guardrail: future C4 evidence must inspect workload-specific metrics and treat any 429 as request failure.
- Mode boundary: quota-on C4 needs distinct load identities; quota-neutral C4 must explicitly document `NRG_QUOTA_DISABLED=1` and cannot be presented as quota-policy proof.

## Do Not Claim

- Do not claim `6/6` quality-bar compliance.
- Do not claim the C4 1000-user bar is closed.
- Do not lower the C4 threshold or parse target text as a passing P99.

## Next Engineering Options

1. Treat C4 as a queueing/envelope architecture task, not a query-parser task.
2. Add bounded admission/backpressure or a separate worker topology for the 1000-user workload, then rerun the same strict scorecard.
3. If every query must synchronously seal into one JSONL HMAC chain before response, design a larger audit writer architecture; micro-optimizing the current file-lock path is not enough.
4. Repeat C4 on the sovereign cluster, because local same-machine client/server load is still a likely confounder.
5. Keep the current C4 status as FAIL until a fresh measured 1000-user run reports P99 under 500 ms.
