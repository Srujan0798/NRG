# TP-002 — GAP-B: 60s Vector Drift Scheduler

**Owner:** CODER  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**v4.1 Reference:** Part B — Mandatory Local Fix B  

---

## Objective

Create and deploy a 60-second vector drift detection scheduler. It must run continuously, execute drift checks every 60s, and log results. Produce evidence file A20.

---

## Current State

- `scripts/vector_drift_scheduler.py` **does not exist**.
- Drift detection logic exists in `tests/observability/test_vector_drift.py` and likely `src/observability/drift.py`.
- No automated/scheduled drift checks are running.

---

## Fortify Phase (Read & Audit)

1. Read the drift detection source:
   ```bash
   find src -name "*drift*" -type f
   ```
   Likely candidates: `src/observability/drift.py`, `src/skills/rag/drift.py`
2. Read `tests/observability/test_vector_drift.py` to understand the API.
3. Check if any cron or scheduler infrastructure exists:
   ```bash
   ls infrastructure/cron/ 2>/dev/null || echo "No cron dir"
   ```
4. Run drift tests to confirm they still pass:
   ```bash
   python -m pytest tests/observability/test_vector_drift.py -v
   ```

---

## Elevate Phase (Implement & Fix)

1. **Create `scripts/vector_drift_scheduler.py`** with the following behavior:
   - Imports the drift detection function from the correct module.
   - Runs in an infinite loop.
   - Executes drift detection every **60 seconds**.
   - Logs each run with timestamp + result to `logs/drift_scheduler.log`.
   - Handles `SIGTERM` / `SIGINT` gracefully (clean shutdown).
   - Supports a `--once` CLI flag for manual/single execution.
   - Supports a `--interval N` CLI flag to override 60s (for testing).
   - On drift detected, logs WARNING level with drift score.

2. **Create systemd service template** (optional but recommended):
   ```
   infrastructure/systemd/nrg-drift-scheduler.service
   ```

3. **Write test** `tests/scripts/test_vector_drift_scheduler.py`:
   - `test_scheduler_runs_with_once_flag` — `--once` executes one cycle and exits 0
   - `test_scheduler_logs_to_file` — log file is created and non-empty
   - `test_scheduler_respects_interval` — mock time to verify interval

4. Make the script executable:
   ```bash
   chmod +x scripts/vector_drift_scheduler.py
   ```

---

## Immortalize Phase (Evidence & Commit)

1. Run the scheduler for **5 minutes** to generate logs:
   ```bash
   python scripts/vector_drift_scheduler.py --interval 60 &
   sleep 300
   kill %1
   ```

2. Create evidence file:
   ```
   evidence/2026-04-25/A20_drift_scheduler_fix.log
   ```
   Contents must include:
   - First 20 lines of `logs/drift_scheduler.log`
   - `wc -l logs/drift_scheduler.log` (should show ≥5 entries for 5min run)
   - Test output: `pytest tests/scripts/test_vector_drift_scheduler.py -v`
   - One-line summary: "GAP-B RESOLVED — 60s drift scheduler running, N checks logged"

3. Commit with message:
   ```
   feat(observability): GAP-B 60s vector drift scheduler
   ```

---

## Acceptance Criteria

- [ ] `scripts/vector_drift_scheduler.py` exists and is executable
- [ ] `--once` flag runs one check and exits with code 0
- [ ] Running for 5 minutes produces ≥4 log entries at 60s intervals
- [ ] `pytest tests/scripts/test_vector_drift_scheduler.py -v` passes
- [ ] Evidence file A20 exists and contains log samples
- [ ] No regressions in `pytest tests/observability/ -v`

---

## Rollback Plan

Stop the scheduler process. The scheduler is a standalone script — no persistent state changes.
