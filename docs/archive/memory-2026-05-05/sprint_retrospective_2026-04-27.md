# Sprint Retrospective — NRG Closure Wave 2026-04-27
**Tag**: v1.0.0-launch-ready  
**Commits**: 13 ahead of nrg/main  
**Duration**: ~8 hours (Guru + agents parallel)

---

## What Worked

1. **Parallel execution**. Guru (Claude) handled Phase 0-2 while agents executed LB-1..LB-8 in parallel. No blocking serial dependencies until Phase 3.
2. **Live evidence first**. Once Colima fixed itself (or agent fixed it), we ran live evidence (LB-1/3/5) immediately rather than mock-based verification.
3. **Test suite speed**. `--no-cov` for fast runs, coverage only on final verification. 1,535 tests in 2:09.
4. **Agent autonomy**. Agents committed directly (8 commits) without Guru micromanagement: health endpoint fix, tier isolation tests, killer query evidence, production audit.
5. **Gates at commit time**. Both `forbidden_vocab_check.sh` and `check_workflow_links.sh` run clean on every commit.

## What Did Not Work

1. **Colima/Docker instability**. P0 was the critical blocker for 2+ hours. Docker daemon intermittent, port 5432 forwarding broken. Eventually resolved (unclear if by agent or by Colima self-healing).
2. **Git lock contention**. Multiple processes (agents + Guru) competing for `.git/index.lock` caused failed commits.
3. **pytest-xdist hangs**. `-n auto` with coverage caused indefinite hangs. Required `--no-cov` workaround.
4. **Root file discipline violations**. New files kept appearing in repo root (audit reports, evidence). Required repeated moves.
5. **Schema truth divergence**. `db_struct.sql` (58 tables) vs actual PG (73 tables). Caused confusion in LB-6 acceptance criteria.

## What to Preserve

1. **Guru ≠ Agent separation**. Guru should not write production code unless no agents available. This held.
2. **Evidence-bound closure**. Every LB item has evidence in `evidence/YYYY-MM-DD/`. This is the permanent audit trail.
3. **Assignment protocol format**. Fortify→Elevate→Immortalize with skills + acceptance criteria works for agent delegation.
4. **Fast-path vs full-path separation**. 60/30/10 traffic mix for load testing is a good model.

## What to Change

1. **Pre-warm Colima before sessions**. Add `colima status` check to Guru startup ritual.
2. **Single committer policy**. Either Guru OR agents commit, not both simultaneously. Reduces lock contention.
3. **pytest.ini default to --no-cov**. Coverage should be opt-in (`pytest --cov`) not default. Speeds up all test runs.
4. **Schema source of truth**. `db_struct.sql` must be the canonical schema, auto-generated from PG via `pg_dump --schema-only`. Never hand-edited.
5. **Agent evidence folder naming**. Standardize: `evidence/YYYY-MM-DD/{lbN}_{description}.{json|md|log}`

## Metrics

| Metric | Value |
|--------|-------|
| LB items closed | 8/8 |
| Tests passing | 1,535 |
| Test time | 2:09 |
| Red team blocked | 121/121 |
| Commits | 13 |
| Files changed | ~100 |
| Lines added | ~3,000 |
| Lines removed | ~2,000 |

## Next Sprint Focus

1. **Sovereign cluster activation** (Phase 7) — 2 weeks
2. **600 GB ingest** — data team
3. **C4 1000-user Locust** — performance team
4. **Commercial sprint** (C1-C8) — founder

