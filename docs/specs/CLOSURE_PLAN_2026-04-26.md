# NRG - Closure Plan 2026-04-26

**Status:** Production closure wave
**Authority:** `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`, `.claude/rules/production_only.md`, and active LB protocols `46..53`
**Scope:** Convert unsealed local work and cluster-bound acceptance into verifiable production state.
**External-audit merge:** Principal Auditor review 2026-04-26 is mapped in `.claude/memory/references/principal-auditor-2026-04-26.md`; same-day Principal Engineer reviews from 2026-04-25 are mapped in `.claude/memory/references/grok-principal-engineer-2026-04-25.md`. They reinforce #56 through #60 and do not create a parallel source of truth.
**2026-04-27 synthesis merge:** The "final ultimate synthesis" paste is reconciled into the same closure plan and reference memory. It is not a new source of truth. Claims that are already closed remain closed; claims contradicted by `db_struct.sql` are corrected here.

## Current State

The repository has production-facing acceptance artifacts in place:

- `docs/operations/PRODUCTION_ACCEPTANCE_RUN.md`
- `scripts/seed_release_data.py`
- `evidence/2026-04-26/acceptance_run_recording.mp4`

The next gate is not more planning. The next gate is sealed evidence: committed slices, running-stack re-verification, full-suite proof, schema/RLS proof, anomaly-defense proof, and cluster activation.

## 2026-04-27 Reconciliation Snapshot

The latest synthesis prompt repeats useful launch discipline, but it also contains stale and inaccurate claims. This is the current repo-truth snapshot:

| Item | Current Repo Truth | Evidence |
|---|---|---|
| API tier-shape boundary | Code is present and committed; live curl proof is still blocked by Docker daemon availability on this machine | `src/api/main.py`, `src/api/response_filter.py`, `tests/api/test_tier_isolation_live.py`, `0c8c65f` ancestry |
| Credit parsing in production prompt | Closed in production prompt, fallback path, schema-aware prompt, and validator | `src/skills/text_to_sql/skill.py`, `schema_aware_prompt.py`, `validator.py`, `tests/benchmarks/test_text_to_sql_prompt_hardening.py` |
| PgBouncer | Present in default compose path; API defaults to `pgbouncer:6432` | `docker-compose.yml`, `tests/config/test_docker_compose_pgbouncer.py`, `673d987` |
| Full Python suite | Locally green under 15 minutes | `evidence/2026-04-27/final_validation/full_python_suite.log` (`1579 passed, 63 skipped, 219 deselected in 99.71s`) |
| Frontend suite/build/lint | Locally green | `evidence/2026-04-27/final_validation/frontend_full_suite.log`, `frontend_lint.log`, `frontend_build.log` |
| Docker one-command contract | Compose config and default service graph are fixed; live startup is not verified because Docker daemon is unavailable here | `evidence/2026-04-27/final_validation/docker_compose_config_quiet.txt`, `docker_daemon_status.txt` |
| TRL identifier claim | Corrected: table name length is 59, not 62. The schema has 63-character constraint/sequence identifiers, so safe-view discipline still remains valid | `db_struct.sql`, `docs/audits/NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md` |
| Composite primary key claim | Corrected: `db_struct.sql` has no composite primary keys; it has composite unique constraints on Django bridge tables | `db_struct.sql`, `docs/audits/NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md` |
| Live red-team replay | Still open as live evidence | `scripts/red_team_live_replay.py`; requires running API |
| Qdrant/vector baseline | Still open as runtime evidence | `evidence/2026-04-27/local_release_gates_2026-04-27.md` reports local Qdrant vectors = 0 |
| Product acceptance cache prewarm | Closed locally with a production-named utility and tests | `scripts/prewarm_release_cache.py`, `tests/scripts/test_prewarm_release_cache.py` |
| Production-path Hall of Shame | Closed locally with all seven Dhairya patterns in the validator ledger | `src/data/schema/failed_queries/HALL_OF_SHAME.md`, `tests/data/test_failed_queries_hall_of_shame.py` |
| Real-user UX acceptance protocol | Merged into a production UX acceptance report; live browser recording and device evidence remain required before handover | `docs/audits/ui_ux_2026-04-27/PRODUCTION_UX_ACCEPTANCE_REPORT.md`, `evidence/2026-04-27/final_validation/ux_acceptance_protocol_merge.md` |
| Principal v4.1 forced-completion protocol | Local GAP-A/B/C verification rerun and recorded; live-stack and cluster-bound gates remain explicit | `evidence/2026-04-27/final_validation/principal_v41_forced_completion_status.md`, `principal_v41_gap_abc_tests.log`, `principal_v41_dhairya_benchmark.log` |

## Real-User UX Acceptance Addendum - 2026-04-27

The latest real-user UX protocol is now merged as a production acceptance artifact, not as another parallel checklist.

| UX concern | Durable home | Current repo truth |
|---|---|---|
| First impression, login, role selection, dashboard, query, result, navigation, loading, errors, mobile, performance, and copy checks | `docs/audits/ui_ux_2026-04-27/PRODUCTION_UX_ACCEPTANCE_REPORT.md` | Consolidated into one evidence-backed report |
| Source-data trust controls | `frontend/src/i18n/en-IN.ts`, `AnswerPanel`, frontend hardening report | Copy Answer and View Source Data controls exist; browser proof should be refreshed |
| Browser noise and failed requests | `docs/audits/frontend_hardening_2026-04-27/console-summary.txt` | Previous captured run shows zero console errors, page errors, request failures, and HTTP 4xx/5xx |
| Placeholder and native-alert hygiene | Static source scan recorded in `ux_acceptance_protocol_merge.md` | No production frontend source matches for the checked placeholder or native-alert patterns |
| Full live walkthrough, mobile, Lighthouse, and Tier 3 API proof | Closure protocols #56 and #61 | Still requires a running stack on a machine with Docker daemon access |

## Principal v4.1 Forced-Completion Addendum - 2026-04-27

The latest Principal v4.1 protocol is merged as a verification pass over existing launch blockers, not as a new task track. Local GAP-A/B/C have current-head proof; remaining live-evidence items stay bound to #56 and #61/#62.

| Protocol demand | Durable home | Current repo truth |
|---|---|---|
| Fix GAP-A DB co-sign | `src/audit/db_cosign.py`; audit trigger migrations; `tests/audit/test_db_cosign.py`; `tests/security/test_per_user_audit_binding.py` | Current-head focused run passed as part of 62-test GAP-A/B/C suite |
| Fix GAP-B 60-second vector drift scheduler | `scripts/vector_drift_scheduler.py`; scheduler tests | Current-head focused run passed; dry-run reports 60-second interval and `/api/reindex` |
| Fix GAP-C Text-to-SQL failure ledger | `src/data/schema/failed_queries/HALL_OF_SHAME.md`; ledger tests | Current-head focused run passed; seven patterns counted |
| Preserve Dhairya regression | `tests/benchmarks/test_dhairya_regression.py` | Current-head run: 43 passed |
| Produce live API, red-team, load, and SQL plan evidence | #56, #58, #61, #62 | Still requires a running API, PostgreSQL, and intended load environment |

## Gap Matrix

| ID | Gap | Bound To | Cluster-Only | Current State | Owner |
|---|---|---|---:|---|---|
| HYG-1 | Vocabulary purge and acceptance artifact cleanup | Production rule | No | Partially complete; verify grep and references | writer + founder |
| HYG-2 | Working-tree sealing by owner slice | Audit contract | No | Dirty tree; no claim counts until sealed by hash | active agents |
| LB-1 | Tier-shape filter at API response boundary | C2 | No | Code committed; needs running-stack Tier 1/2/3 curl proof against current HEAD | backend + security |
| LB-2 | Text-to-SQL hardening and adversarial suite | C3 | No | Code and local tests committed; needs staging PostgreSQL query evidence | backend + ml |
| LB-3 | Three killer queries on seeded stack | C3 + C4-local | Partial | Needs p95 and cited rows against current HEAD | testing + data |
| LB-4 | Full pytest under 15 minutes | Gate | No | Local evidence green on 2026-04-27; rerun only after code changes | testing + devops |
| LB-5 | Live red-team replay | C6 | No | Needs re-run after LB-1 seal | security |
| LB-6 | 58-table parity, indexes, RLS | C3 + Source #3 | No | Local tests present; live fresh PostgreSQL migration proof still required | backend + database |
| LB-7 | Result anomaly detector and answer confidence UI | C3 + Source #2 | No | Local tests present; running-stack low-confidence path proof still required | backend + ml + frontend |
| LB-8 | Semantic layer and schema-RAG | C3 + Sources #2/#3 | No | Local corpus/tests present; staged schema-retriever recall and token-reduction proof still required | backend + ml + data architecture |
| C4-CL | 1000-user load proof on sovereign cluster | C4 | Yes | Harness exists; cluster run pending | devops |
| C5-CL | Vector-drift baseline on populated Qdrant | C5 | Yes | Daemon exists; baseline pending | devops |
| GAP-D | Acceptance recording on sovereign staging | Handover | Yes | Capture script and acceptance runbook ready | devops |
| GAP-E | 600 GB PostgreSQL ingest | Handover | Yes | Data intake protocol ready | database |
| GAP-F | Three persona user-acceptance sessions | Handover | Yes | Scripts ready; scheduling pending | product |
| GAP-G | GPG signatures on handover docs | Handover | Founder key | Pending founder key/session | founder |
| GAP-H | Chain seal and attestation on live cluster | C1/C2/C6 | Yes | Test pack ready | security |

## Protocol Wave

| Protocol | Name | Done When | Depends On |
|---|---|---|---|
| #54 | Vocabulary Purge | Production vocabulary gate exits 0; CI job present; renamed artifacts have no stale references | None |
| #55 | Working-Tree Sealing | Owner-sliced commits exist for LB-1..LB-8 and BACKLOG rows carry commit hashes | #54 |
| #56 | LB-1..LB-5 Live Evidence | Running stack re-generates tier-shape, adversarial, killer-query, and red-team evidence against HEAD | #55 |
| #57 | LB-4 Full Suite | Canonical suite completes in under 15 minutes with zero failures and JUnit evidence | #55 |
| #58 | LB-6 Schema/RLS | 58/58 schema parity, RLS tier counts, and zero hot-join seq scans are evidenced | #55, #57 |
| #59 | LB-7 Confidence Defense | Anomaly detector covers 12+ signals; low-confidence answers retry or clarify; UI renders confidence | #55, #56, #58 |
| #60 | LB-8 Semantic Layer | Join graph covers 58 tables; schema retriever recall@5 >= 90%; prompt payload reduced >= 60% | #58 |
| #61 | Launch-Ready Seal | Local Quality Bar passes, production audit report is signed, and `v1.0.0-launch-ready` is tagged | #54..#60 |
| #62 | Sovereign Activation | Cluster load, drift baseline, ingest, user-acceptance sessions, chain seal, signatures, and `v1.0.0-eternal` are complete | #61 |

## Execution Order

1. Complete #54 and commit it first.
2. Seal owner slices under #55 without mixing unrelated LB work.
3. Re-run local live evidence under #56 and #57.
4. Verify database parity and semantic layers under #58..#60.
5. Produce the signed production audit and local tag under #61.
6. Move to cluster-bound activation under #62 only after #61 is sealed.

## Non-Negotiables

- No item is `DONE` without a commit hash and evidence path.
- Evidence must be regenerated against the current HEAD after code changes.
- The production vocabulary gate must pass before any sign-off.
- The master execution plan remains the source of truth; this plan is a closure overlay for #54..#62.

## Session-End Checklist

- BACKLOG has #54..#62 plus status and dependency rows.
- `.claude/memory/MEMORY.md` points at this closure plan.
- Three data sources are current: `db_struct.sql`, `tests/benchmarks/killer_queries.yaml`, and BACKLOG.
- Founder dependencies are explicit: DNS, SSO contract, GPG key, Langfuse keys, and cluster availability.
