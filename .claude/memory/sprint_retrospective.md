# Sprint Retrospective — 2026-04-25

## New Rules Added

- Zero-request load tests are failures, even when the process exits successfully.
- Static production routes must not mount global auth or backend health checks.
- Evidence dashboards must show blocker state directly instead of hiding failures behind green aggregate scores.

## Memory Updated

- `.claude/memory/bugs_patterns.md`: added Pattern 7 for invalid Locust proof and Pattern 8 for static route backend probes.

## Skills Applied

- `startup-metrics-framework`: translated audit output into operating metrics: readiness, quality bar, security attacks, training-pair mix, and cost per 1,000 queries.
- `build-dashboard`: shaped a founder go/no-go dashboard around decision support instead of raw metric dumping.
- `frontend-design`: implemented `/founder` as a restrained operations board with stable responsive cards, status bars, and a go/no-go matrix.
- `webapp-testing`: built, served, and verified the route with Playwright at desktop and 375px mobile sizes.
- `self-evolve`: recorded recurring failure patterns in project memory.

## 3 Data Sources Status

- Core Idea: current for product direction and sovereign constraints.
- Dhairya SQL Audit: focused regression is strong; latest evidence reports `43/43` passing.
- PostgreSQL Schema: still partial; schema parity evidence reported `7 passed, 4 skipped`, not a full live Postgres proof.

## Quality Bar Compliance

| Constraint | Score | Status |
|---|---:|---|
| DPDP PII | 9 | focused tests pass |
| Per-user audit | 5 | unit binding passes, operational chain verify currently false |
| Multi-hop planner | 9 | focused DAG tests pass |
| P99 + concurrent SLOs | 2 | local Locust run made 0 requests |
| Vector drift + retrain | 7 | scheduler and focused drift path pass locally |
| Schema allowlist | 9 | egress allowlist tests pass |

Fully compliant: `4/6` in practice. The scorecard script prints `5/5` because C4 is skipped, but that is not a release-grade `6/6`.

## Lethal Assumptions Review

1. **Assumption:** C4 can wait for a sovereign cluster. **If wrong:** UAT will expose slow or unmeasured query paths. **Mitigation:** fix local Locust harness before cluster access.
2. **Assumption:** audit chain can be repaired after the fact. **If wrong:** non-repudiation evidence becomes legally weak. **Mitigation:** verify last-N chain segments after every append and alert immediately.
3. **Assumption:** tier labels are enough. **If wrong:** T1/T2/T3 responses look identical and fail ministry/industry trust review. **Mitigation:** enforce distinct API payload contracts and render them in `/founder`.

## Power Gap Assessment

- Real-time proof board: medium impact, low effort. `/founder` now exists as a static evidence board.
- Load proof parser: high impact, low effort. Add a CI check that rejects Locust CSVs with zero requests.
- Audit-chain last-N monitor: high impact, medium effort. Add append-time verification and alerting.

## Recommendation For Next Sprint

Do not add new product surface until these proof gaps close:

1. Repair/root-cause audit chain mismatch.
2. Fix Locust task implementation and produce nonzero p95/p99 evidence.
3. Make full `pytest tests/` green or split slow/nightly tests explicitly.
4. Make T1/T2/T3 response structures materially different and test via curl + frontend.

---

# Sprint Retrospective — 2026-04-27 Phase 7-10 Prep

## What Worked

- Local launch-ready push completed against the configured `nrg` remote.
- Phase 7 commands were converted from prose into an operator runbook.
- C4 load-test path now matches the requested `tests/performance/locustfile_c4.py` command and declares a 60/30/10 fast/full/adversarial mix.
- C5 now has an explicit `--establish-baseline` command, Helm cronjobs, a persistent drift status file, and `/health.vector_drift`.
- The 600GB intake path now has a manifest, GPG, and per-row HMAC verifier.

## What Failed Or Remains External

- No Kubernetes current context is configured locally, so P7-A through P7-G cannot be truthfully executed here.
- Helm and GPG binaries are not available on this machine outside the repo environment.
- Official 600GB data, stakeholder UAT sessions, and external auditor work are not present.
- `v1.0.0-eternal` already exists as an unsigned lightweight tag on an older commit; final sealing must not reuse it casually.

## Rules To Preserve

- Live-only evidence must stay marked blocked until the sovereign URL, data, or signer exists.
- A final handover zip is not created until every required signature and UAT transcript is present.
- Load-test evidence with zero requests is invalid.
