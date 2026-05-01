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

Current answer: **No. C4 is FAIL.**

Fresh May 2 evidence fixed the runner/auth measurement defects. Later C4
diagnostics added combined request-envelope profiling and a declared
prewarm/no-profile run. The latest usable 1000-user local run still reports:

| Metric | Current Evidence | Required |
| --- | ---: | ---: |
| Total samples | 45,559 | measured, non-zero |
| Failures | 0 | 0 |
| Aggregate P99 | 2100 ms | < 500 ms |
| Researcher P99 | 2100 ms | < 500 ms |
| Government P99 | 2100 ms | < 500 ms |
| Adversarial P99 | 2400 ms | < 500 ms |

Evidence:
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/93_declared_prewarm_no_profile_summary.md`

The clearest diagnostic split is:

- sampled route-handler P99: 1.589 ms
- server `/query` envelope P99: 538.303 ms
- Locust client-observed aggregate P99: 1000 ms in the profiled run
- declared prewarm/no-profile aggregate P99: 2100 ms

Evidence:
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/86_combined_query_envelope_profile_summary.md`

So the project is **on track in process** because the measurement is now honest,
strict, and repeatable. The project is **not certified** because C4 still fails.

## Current Track Verdict

| Surface | Status | Meaning |
| --- | --- | --- |
| Rule hierarchy | PASS | The repo has a clear canonical order; this document makes it explicit. |
| Repo-contained skills | PASS | NRG uses `.claude/skills` and `.agents/skills`, not user-home skill caches. |
| Local product proof | PARTIAL | Many backend, frontend, tier, audit, and accessibility gates passed locally. |
| C4 SLO | FAIL | 1000-user P99 is above 500 ms. |
| Full Python suite | FAIL | Latest broad single command is not green. |
| Dependency audit | FAIL | High-severity frontend dependency findings remain open. |
| External production gates | BLOCKED | Need deployed URLs, production service context, cluster C4, and founder signing. |

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

Use this flow for the next C4 wave.

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

6. **Current next engineering options**
   - Use the combined profile to isolate the remaining request-envelope and
     client-observed tail between route handler, middleware, process scheduling,
     socket/backpressure, and Locust client contention.
   - Keep declared warmed read-model traffic explicit in evidence; prewarm alone
     did not close C4.
   - If cold cache misses must synchronously seal into one JSONL HMAC chain
     before response, design a larger audit-writer path; the current file-lock
     micro-optimizations are not enough.
   - Repeat C4 on the sovereign cluster to remove laptop client/server
     contention from the final claim.

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

1. **C4 tail closure**
   - Use the latest combined profile and declared prewarm run as the baseline.
   - Decide whether the next fix is middleware/envelope, process scheduling,
     response serialization, socket/backpressure, or cluster-only validation.
   - Produce one C4 blocker report with the next implementation target.

2. **Dependency audit closure**
   - Triage high-severity frontend findings.
   - Patch only safe dependency paths.
   - Re-run frontend tests and build.

3. **Full-suite orchestration**
   - Separate live-required tests from local-only tests.
   - Make one reproducible command green for the local slice.

4. **External gate package**
   - Prepare exact operator commands for deployed browser replay, production
     Qdrant/Redis health, cluster C4, and founder signing.

## Do Not Claim

- Do not claim C4 is closed.
- Do not claim 6/6 Quality Bar compliance.
- Do not claim production readiness from laptop-only evidence.
- Do not treat skill inventory as product proof.
- Do not treat external source accounting as running-product proof.
