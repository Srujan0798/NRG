# C4 Follow-Up: Multi-Process Locust and Deployment Topology

Date: 2026-05-02

## What Was Checked

- The scorecard can now pass `NRG_C4_LOCUST_PROCESSES>1` through to Locust as `--processes`.
- The subprocess is started in a new session when multi-process Locust is enabled so worker shutdown does not leak signals back into the parent process group.
- The local Docker/Colima topology was checked before attempting a compose run.

## Evidence

| Evidence | Result |
| --- | --- |
| `136_quality_bar_scorecard_60s_4workers_uvloop_httptools_locust4.json` | Negative diagnostic: C4 failed with `locust_processes=4`, `failure_rate=0.9953`, and `HTTP 0` errors. Do not use as pass evidence. |
| `137_locust_report_60s_4workers_uvloop_httptools_locust4.html` | HTML report for the failed multi-process Locust run. |

## Local Topology Status

The local Docker/Colima probe did not expose a usable Docker daemon in this session. A production-compose C4 run is therefore **BLOCKED LOCALLY**, not skipped as a pass.

## Decision

- Keep multi-process Locust support in the scorecard because it is needed for realistic load generation on larger hosts.
- Do not claim C4 closed. Multi-process Locust currently exposes an HTTP 0 failure mode under local conditions.
- Next C4 attempt should run on a machine/topology where Docker or the sovereign deployment stack is actually available, or should use a controlled external load generator against the API host.
