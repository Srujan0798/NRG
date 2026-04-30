# Prompts Hybrid Freshness Pass - 2026-04-30

## Scope

Refreshed the `prompts_hybrid/` stones so future agents start from current NRG
truth instead of stale pre-C4 assumptions.

## Files Updated

- `prompts_hybrid/00_INDEX.md`
- `prompts_hybrid/01_master_execution_stone.md`
- `prompts_hybrid/02_main_flow_stone.md`
- `prompts_hybrid/03_frontend_zero_flaw_stone.md`
- `prompts_hybrid/04_backend_security_data_stone.md`
- `prompts_hybrid/05_audit_red_team_stone.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `prompts_hybrid/07_show_readiness_handover_stone.md`
- `prompts_hybrid/ARCHIVE_NOTES.md`

## Changes

- Added required reads for `.claude/CURRENT_STATE.md`,
  `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`, and latest
  `evidence/2026-04-30/` reports.
- Replaced stale SQL audit path references with
  `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`.
- Updated C4 language: local 100-user C4 smoke passed in
  `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`; production
  readiness still needs 1000-user sovereign-cluster/deployed proof.
- Added C4 read-model/cache safety rules for tier-safe keys, filtered payloads,
  public JSON markers, and audit traceability on cache hits.
- Updated show-readiness prompts to use the verified demo query
  `best quantum researchers` and blocked PII request before advanced queries.
- Added minimum final-report fields: files changed, commands/tests run,
  evidence paths, blockers, and commit SHA or `not committed`.
- Added a minimum acceptance gate to the evidence stone so agents cannot bury
  required proof inside the longer checklist.

## Verification

```text
git diff --check -- prompts_hybrid
```

Result: passed with no whitespace errors.

```text
rg -n "SQL_AUDIT_REPORT_DHAIRYA\.md if present|C4 remains open|strict C4 latency still fails|not strict-C4-ready|local gate improved|3602 requests|2700ms|live_c4_local_smoke/README|worker_pool|cached_filter|launch ready" prompts_hybrid
```

Result: no stale prompt-control references found. Historical phrases remain only
where they are explicitly part of audit templates or current blocked-gate
language.

## Remaining Blocker

No prompt blocker remains from this pass. The product blocker is unchanged:
1000-user sovereign-cluster/deployed C4 proof is still required before any
production-readiness claim.
