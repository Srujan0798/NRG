---
name: hybrid-mvp-fusion
description: Use when building or improving an NRG v1.0 release from internal specs, external product ideas, screenshots, or agent-generated concepts; merges only useful patterns into NRG while preserving Core_Idea, Dhairya SQL audit, schema truth, tiers, audit proof, and evidence gates.
---

# Hybrid v1.0 Fusion

Use this skill when an agent is asked to make a v1.0 release, merge external
ideas, or turn production-module material into the NRG product path.

## Required Reading

Read these first, in order:

1. `.claude/CURRENT_STATE.md`
2. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
3. `Core_Idea_Clean.md`
4. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
5. `db_struct.sql`
6. `prompts_hybrid/00_INDEX.md`
7. the task-specific prompt stone

Run this before using `CORPUS/` as a handoff pack:

```bash
python3 scripts/verify_corpus_sync.py
```

## Fusion Rule

Take only what improves NRG's real product path:

- clearer login/persona/query/answer/proof flow
- stronger answer layout, citations, source rows, SQL/proof drawer, audit ID
- better loading, error, blocked, empty, mobile, and follow-up states
- better API adapter or response contract clarity
- better query-corpus, validation, or evidence structure

Reject or isolate anything that weakens NRG:

- landing-page-only MVPs
- fake dashboards without query truth
- UI polish that hides bad SQL/RAG answers
- release-only hardcoded answers
- schema guesses that ignore `db_struct.sql`
- query tests that ignore the Dhairya audit
- claims without evidence

## Non-Negotiable Gates

A v1.0 change is acceptable only when it preserves:

- `Core_Idea_Clean.md` product direction
- Dhairya SQL audit failure patterns
- `db_struct.sql` schema truth
- tier-safe responses for Researcher, Government, and Industry
- citations/source rows/audit event ID on answer paths
- no PII leak to Tier 3
- fresh evidence for build, tests, screenshots, or API JSON

## Output Required

Report:

- what external or production-module idea was accepted
- what was rejected and why
- files changed
- commands/tests run
- evidence paths
- blockers
- commit SHA if committed, otherwise `not committed`
