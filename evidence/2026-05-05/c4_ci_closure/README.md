# C4 CI Closure Evidence

Date: 2026-05-05
Status: HOSTED QUALITY-BAR PASS; downstream deploy gates still tracked separately

## Hosted Quality-Bar Evidence

- `38_hosted_quality_bar_scorecard_dc3b92e7.json` — GitHub Actions
  scorecard artifact from commit `dc3b92e75510d4372ec027340629d934ddb7df39`.
- `39_hosted_quality_bar_summary_dc3b92e7.md` — summary of the hosted
  `Deploy` run `25395229374`, job `quality-bar` `74480094337`.
- `40_hosted_quality_bar_scorecard_e2bc6fb0.json` — latest GitHub Actions
  scorecard artifact from commit `e2bc6fb01eca138b60a9ec193160d28222a0d0b7`.
- `41_hosted_quality_bar_summary_e2bc6fb0.md` — latest hosted run summary;
  `CI`, `Deploy`, and `Deploy NRG` are all PASS for the same commit.
- Hosted C4 metrics: 1000 requested users, P99 410 ms, failure rate 0.0, and
  292598 total samples.
- Latest hosted C4 metrics: 1000 requested users, P99 370 ms, failure rate
  0.0, and 307721 total samples.

## Passing Local Checks Captured Here

- `21_health_timeout_and_qdrant_after_daemon_probe.log` — focused health
  timeout and Qdrant endpoint checks passed.
- `22_async_append_daemon_queue_tests.log` — async audit append queue tests
  passed.
- `23_tier_response_single_after_audit_queue.log` and
  `32_tier_response_single_final.log` — focused tier response filtering passed.
- `26_slo_health_slice_skip_c4_env.log` — focused SLO health slice passed with
  C4 read-model prewarm skipped for test isolation.
- `27_git_diff_check_final.log`, `28_workflow_verify_final.log`,
  `29_corpus_sync_final.log`, and `30_forbidden_vocab_final.log` — local
  structural checks passed.

## Historical Local Failure Evidence

- `29_slo_full_rerun_after_p99_focus.log` — strict local SLO suite failed:
  P50 114ms exceeded the 100ms target and `/health` timed out once under the
  full SLO ordering.
- `33_slo_full_after_health_dependency_mocks.log` — latest strict local SLO
  rerun failed P95/P99 latency thresholds.

## Blocker Boundary

This directory is evidence for the May 5 C4 closure attempt. Hosted GitHub
Actions quality-bar C4 is now PASS for commit
`dc3b92e75510d4372ec027340629d934ddb7df39`; cluster proof remains BLOCKED until
a usable Kubernetes context and deployment targets are available.
