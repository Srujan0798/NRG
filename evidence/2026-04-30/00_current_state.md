# NRG Current State Lock

Generated: 2026-04-30

## Repository State

- Current branch: `main`.
- Last commits observed:
  - `6d0ac3a chore: drop tracked test run metadata`
  - `516991a chore: prune verified dead artifacts`
  - `d207b54 fix: answer messy researcher queries on live schema`
- Previously untracked file `evidence/2026-04-29/p0_backend_security_and_query_closure.md` is useful evidence and should be committed, not deleted.
- Broad cleanup is complete enough for the next phase. Future agents should not continue deleting files unless import/reference search proves a file is dead.

## Working Product Status

- The repo is structurally cleaner: stale tracked docs, dead frontend components, one-off scripts, and tracked test-run metadata were removed in recent commits.
- The next highest-value work is answer-engine hardening, not more cleanup.
- Current known product risk: messy natural-language queries can still route to weak/generic behavior unless the backend classification/retrieval path is hardened and covered by tests.
- Current known release risk: C4/load readiness is not fresh. Prior evidence showed the 100-user load bar failed; Wave 5 must rerun and report current numbers.

## Agent Wave Order

1. Wave 1 backend answer-engine hardening.
2. Wave 4 SQL/RAG retrieval truth, only if file ownership does not conflict with Wave 1.
3. Wave 2 frontend main flow after backend response contract is stable.
4. Wave 3 security/tier/audit proof after query responses expose audit IDs.
5. Wave 5 performance profiling after backend query behavior is stable.
6. Wave 6 handover package after evidence gates are collected.

## Non-Negotiable Agent Rules

- Read `.claude/CLAUDE.md`, `.claude/CURRENT_STATE.md`, and the assigned `prompts_hybrid/*_stone.md` before editing.
- Do not modify overlapping file ownership in parallel.
- Do not claim completion without fresh command output.
- Do not make broad cleanup changes during feature hardening.
- Every response must include files changed, tests run, evidence paths, blockers, and commit SHA if committed.

## Immediate Next Step

Start Wave 1: harden `/query` and any stream path so messy user text goes through a stable flow:

`sanitize -> intent classify -> clarify if needed -> SQL/RAG/hybrid retrieval -> deterministic verification -> synthesis -> audit`.

Minimum Wave 1 evidence:

- Targeted backend tests for messy/noisy questions.
- At least 10 test-client JSON responses showing distinct relevant behavior.
- Each successful answer includes citations and `audit_event_id`.
