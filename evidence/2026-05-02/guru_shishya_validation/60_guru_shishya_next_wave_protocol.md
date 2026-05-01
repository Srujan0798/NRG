# Guru/Shishya Next-Wave Protocol

Date: 2026-05-02

This protocol continues the project-local `.claude/skills`, `.agents/skills`,
and `prompts_hybrid/` workflow. The inventory is complete; execution now follows
evidence priority, not theatrical use of unrelated skills.

## Guru Assignment Note

NRG has strong local proof for backend/API contracts, Dhairya SQL regression,
frontend build/Jest/a11y, live browser query flow, tier safety, and audit chain
after repair. It is not eligible for a whole-product claim while dependency
audit, C4 load, live Qdrant/Redis health, broad single-command test orchestration,
and external gates remain unresolved.

Skill accounting:

- `.claude/skills`: 86 files inventoried.
- `.agents/skills`: 50 files inventoried.
- Total local skills: 136 files inventoried and classified.
- Evidence: `55_skill_inventory.tsv`, `56_skill_usage_ledger.md`,
  `57_hybrid_prompts_headers.log`.

## Phase 1: Fortify

Objective: remove local false failures and close the highest-risk local blockers.

### ACTION F1: C4 Report-Path Hardening

Skills:

- `.claude/skills/performance`
- `.agents/skills/systematic-debugging`
- `.agents/skills/test-driven-development`
- `.agents/skills/verification-before-completion`

Agent Instructions:

1. Preserve the root-cause record: `quality_bar_scorecard.py` wrote Locust HTML
   into `ROOT/.cache/locust_report.html` without creating the parent directory.
2. Keep the regression test in `tests/scripts/test_quality_bar_scorecard.py`.
3. Verify with `.venv/bin/python -m pytest tests/scripts/test_quality_bar_scorecard.py -q`.
4. Do not mark C4 as passing from this fix. This only removes one local runner
   defect; latency and failure-rate evidence still governs C4.

Evidence:

- `58_c4_scorecard_cache_regression.log`

### ACTION F2: Dependency Audit Closure Plan

Skills:

- `.claude/skills/security-audit`
- `.claude/skills/frontend-react-best-practices`
- `.agents/skills/systematic-debugging`
- `.agents/skills/deploy-checklist`

Agent Instructions:

1. Use `59_frontend_npm_audit_high_json.json` as the machine-readable source.
2. Split fixes into two lanes:
   - Lane A: non-breaking direct updates that preserve React 18, Vite build,
     Jest, Playwright, Storybook build, and lint.
   - Lane B: major toolchain upgrades requiring a separate branch and full
     frontend verification.
3. Do not run `npm audit fix --force` on the main worktree without an explicit
   upgrade protocol, because the audit itself reports major version changes for
   Storybook, Vite, Jest/jsdom, and Loki-related paths.
4. Acceptance requires `npm audit --audit-level=high` exit 0 plus frontend
   build, Jest, contrast, lint, and Playwright a11y reruns.

Evidence target:

- `61_dependency_audit_closure.log`
- updated `frontend/package.json`
- updated `frontend/package-lock.json`

## Phase 2: Elevate

Objective: restore live-service health and prove performance with real services.

### ACTION E1: Qdrant/Redis Health Restoration

Status: PASS locally after Colima/Compose startup. Production/deployed proof
remains external-gate work.

Skills:

- `.claude/skills/nrg-embedding-models`
- `.claude/skills/nrg-redis-caching`
- `.claude/skills/nrg-grafana-monitoring`
- `.agents/skills/vector-index-tuning`
- `.agents/skills/prometheus-configuration`

Agent Instructions:

1. Start the intended local stack or point the app to verified Qdrant and Redis
   endpoints.
2. Prove `/health`, `/health/all`, `/health/qdrant`, `/api/vectors/health`, and
   Redis-backed cache behavior.
3. Run vector drift baseline checks only after Qdrant has vectors and payload
   metadata.
4. Keep local and external health evidence separate.

Evidence targets:

- `62_colima_start.log`
- `63_compose_qdrant_redis_up.log`
- `64_live_health_all_after_services.json`
- `65_live_health_qdrant_after_services.json`
- `66_live_vectors_health_after_services.json`
- `67_redis_keyspace_after_services.log`
- `68_qdrant_redis_local_health_report.md`
- `69_post_service_verification.log`
- `72_colima_docker_ps.log`
- `74_colima_stack_health_all.json`

### ACTION E2: C4 Load Closure

Skills:

- `.claude/skills/performance`
- `.claude/skills/capacity-plan`
- `.agents/skills/deployment-pipeline-design`
- `.agents/skills/statistical-analysis`

Agent Instructions:

1. Rerun the C4 scorecard after F1 and E1.
2. If local 1000-user run still fails, profile `/query`, `/login`, and
   `/health/all` separately so the next fix targets the slowest path.
3. A laptop run may support local claims only. Production-speed claims require
   the external/cluster gate.
4. C4 PASS requires current evidence for P99 target, failure target, and 1000
   users.

Evidence targets:

- `65_c4_scorecard_after_services.log`
- `66_c4_hot_path_profile.json`

## Phase 3: Immortalize

Objective: convert proof into durable state, docs, backlog, and handover gates.

### ACTION I1: Broad Test Orchestration

Skills:

- `.claude/skills/test-suite`
- `.claude/skills/pre-commit`
- `.agents/skills/verification-before-completion`
- `.agents/skills/debug`

Agent Instructions:

1. Separate tests requiring a live API from offline unit/contract tests.
2. Update the test runner so the broad command is green or explicitly stages
   API startup before live tests.
3. Acceptance is one reproducible command or a documented two-stage command set
   with evidence and exit codes.

Evidence targets:

- `67_full_pytest_orchestrated.log`
- updated runner or runbook if required

### ACTION I2: External Gate Closure

Skills:

- `.claude/skills/release-readiness`
- `.claude/skills/external-audit`
- `.claude/skills/signature-request`
- `.agents/skills/deploy-checklist`
- `.agents/skills/secure-linux-web-hosting`

Agent Instructions:

1. Run only on the machine with deployed frontend/API URLs, production Qdrant
   target, cluster context, and founder signing key.
2. Use `scripts/run_final_external_gates.py` and the external-gate runbook.
3. Founder-only signing must not be simulated or bypassed.
4. Update the final matrix with PASS, FAIL, BLOCKED, or UNKNOWN only.

Evidence targets:

- `evidence/YYYY-MM-DD/final_external_gates/EXTERNAL_GATE_SUMMARY.md`
- signed tag and signature manifest when founder completes signing.

## Stop Conditions

- Any failed security, audit, tier, or PII gate stops release claims.
- Any dependency-audit high finding keeps dependency audit at FAIL unless risk
  is formally accepted in writing.
- Any missing deployed target keeps external proof at BLOCKED.
- Any missing evidence path keeps a row UNKNOWN or BLOCKED.
