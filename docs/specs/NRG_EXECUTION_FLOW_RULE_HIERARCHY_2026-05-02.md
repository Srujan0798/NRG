# NRG Execution Flow And Rule Hierarchy

Date: 2026-05-02  
Status: Operating map. This is not a readiness certificate.

This document centralizes how NRG work should flow after the May 2 Guru/Shishya
validation campaign. It reconciles the repo-contained `.claude` and `.agents`
instructions, current evidence, source-truth hierarchy, and C4 status into one
track.

## What C4 Means

In this repo, **C4** means **Quality Bar Constraint 4: Production SLOs**.
It is not the C4 architecture-diagram method.

C4 asks one focused question:

> Can the running NRG query path handle at least 1000 concurrent users with
> zero request failures and P99 latency below 500 ms?

Current local quota-neutral answer: **PASS**.

Fresh May 2 evidence fixed the runner/auth measurement defects, made HTTP 429 a
load failure, exposed per-workload `/query` metrics, and moved request-path
audit appends onto a bounded dedicated executor while preserving the synchronous
audit-chain contract. The latest strict 1000-user local quota-neutral run
reports:

| Metric | Current Local Quota-Neutral Evidence | Required |
| --- | ---: | ---: |
| Total samples | 82,365 | measured, non-zero |
| Failures | 0 | 0 |
| Aggregate P99 | 79 ms | < 500 ms |
| Researcher P99 | 64 ms | < 500 ms |
| Government P99 | 80 ms | < 500 ms |
| Adversarial P99 | 170 ms | < 500 ms |

Evidence:
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/165_quality_bar_scorecard_60s_4workers_bounded_audit_executor.json`
and
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/167_bounded_audit_executor_c4_pass_summary.md`.

Boundary: this run used `NRG_QUOTA_DISABLED=1`, 4 uvicorn workers, 4 Locust
processes, 1000 users, 100/s spawn rate, and 60s runtime. It proves local
capacity for the current checkout. It does **not** prove quota-policy behavior
or deployed/cluster C4 until those modes are replayed with the same strict
scorecard.

Superseded diagnostics remain useful for root-cause history, but they are not
the current status. The key historical files are
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/86_combined_query_envelope_profile_summary.md`
and
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/93_declared_prewarm_no_profile_summary.md`.

## Current Track Verdict

| Surface | Status | Meaning |
| --- | --- | --- |
| Rule hierarchy | PASS | The repo has a clear canonical order; this document makes it explicit. |
| Repo-contained skills | PASS | NRG uses `.claude/skills` and `.agents/skills`, not user-home skill caches. |
| Local product proof | PASS local / external pending | Backend, frontend, tier, audit, accessibility, local Qdrant/Redis, managed full-suite, dependency audit, and local quota-neutral C4 evidence pass locally. |
| C4 SLO | PASS local quota-neutral / cluster pending | Latest strict local scorecard: 1000 users, 82,365 samples, 0 failures, aggregate P99 79 ms; quota-policy and deployed/cluster proof remain pending. |
| Full Python suite | PASS managed live orchestration | `scripts/run_test_suite.sh --live-api` separates non-live and live API phases; latest evidence has 1,830 non-live tests with 0 failures/errors and 36 live API tests with 0 failures/errors. |
| Dependency audit | PARTIAL local image OS scan / deployed scans pending | Frontend `npm audit` reports 0 total vulnerabilities. Frontend and reverse-proxy local runtime images now have 0 Trivy OS findings after nginx base hardening. API runtime Python `pip-audit` reports 0 vulnerabilities and fixable-only Trivy reports 0 findings after true multi-stage hardening, but strict Trivy still reports 112 Debian findings including 7 high no-fix findings. Deployed image scans remain pending. |
| External production gates | BLOCKED | Need deployed URLs, production service context, cluster C4, production Qdrant target, production image dependency checks, and founder signing. |

## Rule Hierarchy

Use this order when instructions conflict.

1. **Founder request in the current conversation**
   - Newest correction overrides older operating assumptions.
   - If the Founder asks for proof across every surface, answer with a
     `PASS` / `FAIL` / `BLOCKED` / `UNKNOWN` matrix.

2. **Repo operating manuals**
   - `AGENTS.md`
   - `.claude/protocol.md`
   - `.claude/constitution.md`
   - `.claude/agent-warfare.md`
   - `.agents/AGENTS.md`
   - `.agents/prompts/shishya_universal.md`

3. **Production-only framing**
   - `.claude/rules/production_only.md`
   - No forbidden production-language leaks in specs, protocols, commit
     messages, or release artifacts.

4. **Current state and source truth**
   - `.claude/CURRENT_STATE.md`
   - `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
   - `.claude/memory/INDEX.md`

5. **Product and schema truth**
   - `Core_Idea_Clean.md`
   - `db_struct.sql`
   - `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
   - `docs/reports/SQL_AUDIT_RAW_dhairya.sql`
   - `tests/benchmarks/killer_queries.yaml`

6. **External audit truth**
   - Root `NRG_*_AUDIT_*.md` files.
   - External findings override internal confidence until independently
     verified and closed.

7. **Quality Bar C1-C6**
   - `.claude/quality-bar.md`
   - C1 DPDP PII
   - C2 per-user audit binding
   - C3 multi-hop decomposition
   - C4 production SLO
   - C5 vector drift
   - C6 egress allowlist

8. **Evidence and release acceptance**
   - `.claude/rules/audit/index.md`
   - `.claude/rules/audit/protocol.md`
   - `prompts_hybrid/06_evidence_acceptance_stone.md`
   - Evidence expires by surface; stale evidence cannot support a pass claim.

9. **Work-type rules**
   - Backend: `.claude/rules/backend.md`
   - Frontend: `.claude/rules/frontend.md`
   - Security: `.claude/rules/security.md`
   - UX: `.claude/rules/ux/index.md`
   - Data quality: `.claude/rules/data_quality.md`
   - Contract testing: `.claude/rules/contract_testing.md`

10. **Repo-contained skills**
    - Guru strategy skills: `.claude/skills/*/SKILL.md`
    - Shishya execution skills: `.agents/skills/*/SKILL.md`
    - Current inventory: 86 Guru skills and 51 Shishya skill directories.
    - Inventory evidence:
      `evidence/2026-05-02/guru_shishya_validation/55_skill_inventory.tsv`

11. **Pre-commit and completion gates**
    - `.claude/skills/pre-commit/SKILL.md`
    - `.claude/skills/code-review/SKILL.md`
    - `.claude/skills/security-audit/SKILL.md`
    - `.claude/skills/docs-sync/SKILL.md`
    - No completion claim without current verification output.

## Project Flow

Every NRG work session should follow this order.

1. **Start Lock**
   - Read production-only rule, current state, source-truth map, memory index,
     git status/log, and root external audit files.
   - Run `python3 scripts/verify_corpus_sync.py` when `CORPUS/` is used.

2. **Classify The Task**
   - Identify work type: architecture, backend, frontend, security, database,
     performance, validation, documentation, or release acceptance.
   - Pick only repo-contained skills from `.claude/skills` and `.agents/skills`.

3. **Name The Claim Boundary**
   - Decide whether this work can prove a local claim, deployed claim,
     cluster-load claim, or only a plan.
   - Mark every unprovable surface as `BLOCKED` or `UNKNOWN`.

4. **Plan As Guru**
   - Use the full Guru protocol when assigning agent work.
   - Every protocol includes Fortify, Elevate, Immortalize phases.
   - Every protocol names at least three skills and the exact acceptance gates.

5. **Execute As Shishya**
   - Read `.agents/AGENTS.md` and the selected `SKILL.md` files.
   - Make scoped changes only inside the assigned file ownership.
   - Preserve unrelated user or agent changes.

6. **Verify**
   - Run the smallest relevant tests first.
   - Then run broader gates when the surface is shared or release-facing.
   - Save command output or structured evidence under `evidence/YYYY-MM-DD/`.

7. **Audit The Claim**
   - Convert results into `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`.
   - For UI claims, include browser evidence.
   - For tier/security claims, include raw API JSON and audit IDs.
   - For performance claims, include request count, P50/P95/P99, failures, and
     exact scope.

8. **Update Durable State**
   - Update `.claude/CURRENT_STATE.md`.
   - Update `BACKLOG.md`.
   - Update `.claude/memory/` only for durable rules, bugs, evidence pointers,
     and reusable patterns.

9. **Report To Founder**
   - State what changed, what passed, what failed, what is blocked, and the next
     highest-leverage action.
   - Do not use confidence language where evidence is missing.

## C4-Specific Flow

Use this flow for any new C4 wave. Do not rerun local C4 just to re-prove the
same claim unless code, dependencies, runtime settings, or evidence freshness
requires it.

1. **Choose C4 mode before running**
   - Quota-on C4: use enough distinct load identities so the run measures query
     capacity rather than a three-user quota boundary.
   - Quota-neutral C4: explicitly set and document `NRG_QUOTA_DISABLED=1`.
     This is capacity evidence only, not quota-policy evidence.

2. **Ensure clean processes**
   - Confirm no stale API, Locust, or scorecard process is still running.
   - Confirm the API binds to the intended port.

3. **Enable profiling for diagnosis**
   - `NRG_QUERY_STAGE_PROFILE=1`
   - `NRG_REQUEST_ENVELOPE_PROFILE=1`
   - Save both JSONL outputs under the dated C4 evidence folder.

4. **Run scorecard**
   - Use `scripts/quality_bar_scorecard.py`.
   - The scorecard must use `tests/load/locustfile_c4.py`.
   - It must parse real Locust report metrics, fail HTTP 429, and expose
     per-workload `/query` P99 and failures.

5. **Pass criteria**
   - Requested users: at least 1000.
   - Failure rate: 0.
   - Aggregate P99: below 500 ms.
   - Per-workload `/query` P99: below 500 ms.
   - Audit-chain verification after load: valid.

6. **Current next proof options**
   - Replay the same strict scorecard on the sovereign cluster before making a
     deployed/cluster C4 claim.
   - Run quota-on C4 with enough distinct load identities before making a
     quota-policy claim.
   - Preserve the `NRG_QUOTA_DISABLED=1` boundary whenever using the latest
     local capacity evidence.
   - Re-run local C4 only after performance-sensitive code, dependency,
     runtime, or evidence-freshness changes.

## Whole-Product Proof Flow

Use this whenever the Founder asks whether NRG is fully better, stronger, or
ready across every surface.

Required rows:

| Surface | Status Rule |
| --- | --- |
| Appearance | Browser screenshots or E2E evidence. |
| UI/UX | Main path plus loading, empty, error, blocked, recovery, and mobile states. |
| Query intelligence | Messy, ambiguous, follow-up, out-of-corpus, and killer-query coverage. |
| Database/schema | `db_struct.sql`, corpus sync, schema route tests, and no stale schema assumptions. |
| Dhairya audit | Dhairya failure patterns covered by regression or live evidence. |
| Backend/API | Raw JSON contract with audit ID, citations, source rows, tier, timing, and verification. |
| Retrieval | SQL/RAG/hybrid route evidence and health status. |
| Security/tier | PII, injection, tier escalation, small-cohort, and Tier 3 raw JSON proof. |
| Audit | HMAC chain proof for allowed and blocked actions. |
| Accessibility | Contrast, keyboard, focus, labels, touch targets, and responsive evidence. |
| Performance | Local profile for local claims; deployed/cluster profile for production claims. |
| Evidence | Current evidence index with commands, outputs, paths, blockers, and commit SHA. |
| Production gates | Deployed browser replay, production service health, 1000-user C4, and founder signing. |

Every row must be `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`. One failed or
unknown row blocks a whole-product pass claim.

## Immediate Next Track

The next execution wave should not scatter across all skills at once. It should
follow this order:

1. **External gate package**
   - Prepare exact operator commands for deployed browser replay, production
     Qdrant/Redis health, cluster C4, and founder signing.

2. **Production image dependency replay**
   - Frontend runtime image build/smoke evidence exists for the local nginx
     image.
   - Frontend and reverse-proxy local runtime OS scans now pass with Trivy.
   - API runtime Python package audit and fixable-only Trivy scan pass, but
     strict Trivy still has no-fix Debian base findings.
   - Re-run `scripts/runtime_image_scan_gate.py` against current scan artifacts
     before updating any dependency/image claim.
   - Resolve the API no-fix base-image boundary when an upstream patched base or
     approved alternate runtime base is available.
   - Scan deployed images, not only local image builds.

3. **Cluster C4 replay**
   - Use the same strict scorecard semantics as the local pass.
   - Record users, spawn rate, runtime, failures, aggregate P99, per-workload
     `/query` P99, and audit-chain verification.

4. **Production data-quality replay**
   - Local PostgreSQL scorecard evidence may close local data-completion gaps,
     but deployed production claims still require a fresh scorecard against the
     target production database.
   - Keep `db_struct.sql`, Dhairya regression expectations, and query evidence
     aligned before external product claims.

## Do Not Claim

- Do not claim deployed/cluster C4 is closed from local quota-neutral evidence.
- Do not claim quota-policy C4 is closed from `NRG_QUOTA_DISABLED=1` evidence.
- Do not claim production readiness from laptop-only evidence.
- Do not treat skill inventory as product proof.
- Do not treat external source accounting as running-product proof.
