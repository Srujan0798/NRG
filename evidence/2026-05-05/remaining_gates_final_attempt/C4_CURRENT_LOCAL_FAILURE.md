# C4 Current Local Failure

Date: 2026-05-05
Status: FAIL

## Latest Result

The latest current-stack Quality Bar scorecard is `5/6`; C4 is the failing
constraint.

- Scorecard source: `scripts/quality_bar_scorecard.json`
- Run log: `evidence/2026-05-05/remaining_gates_final_attempt/quality_bar_scorecard_rerun_60s_4workers.log`
- Requested load: 1000 users, spawn rate 100, runtime 60s, 4 Locust workers
- C4 outcome: p99 10000ms, threshold 500ms
- Failure rate: 100% locust-reported failures, with HTTP 0 errors
- Total samples: 13888

The strict local SLO regression command also failed:

- Command: `.venv/bin/python -m pytest tests/performance/test_slo_compliance.py -m 'slow or not slow' -q --tb=short --no-cov`
- Result: 7 passed, 2 failed, 3 skipped
- Failing checks: P95 343ms >300ms, P99 2007ms >500ms

## Runtime State After Failure

Colima needed restarts after the C4 attempt and Docker build verification.
Recovery evidence is in:

- `evidence/2026-05-05/remaining_gates_final_attempt/colima_recovery_after_c4_failure.log`
- `evidence/2026-05-05/remaining_gates_final_attempt/colima_recovery_after_docker_build_hang.log`

Observed post-recovery checks:

- First recovery: Docker containers came back and `/health/db` plus
  `/health/qdrant` were healthy; `/health/all` remained degraded because the
  aggregate route reported Redis `No connection`.
- After Docker build verification hung: `docker ps` timed out and
  `localhost:8000` was unreachable.
- Second recovery log contains a Colima startup fatal
  (`did not receive an event with the "running" status`) before the final
  `colima status` reported the VM running again.
- Frontend Docker build verification was not completed because Buildx/context
  transfer stalled repeatedly.

## Closure Boundary

C4 is not complete on the current stack. The historical May 2 local pass is
preserved as historical evidence only; it does not override this May 5 failure.
Cluster proof still requires a usable `KUBECONFIG` and
`scripts/run_final_external_gates.py --run-cluster-load`.
