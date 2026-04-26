---
name: Live Evidence Requirement
description: A unit-test pass alone never satisfies any Quality Bar constraint — every "PASS" claim needs evidence captured against a running stack with production-realistic seed volume
type: feedback
---

Tests on 10-row seed data are **deferred bugs, not passing tests**. Every Quality Bar PASS claim — and every protocol acceptance criterion — must carry at least one of:

1. A captured response from a **running uvicorn API + populated Qdrant + ≥50,000-row staging PostgreSQL**, committed under `evidence/<YYYY-MM-DD>/` as JSON or Markdown.
2. A scorecard run by `scripts/quality_bar_scorecard.py` against that running stack — its JSON output is the source of truth.
3. A signed audit-chain entry in `.audit/chain.jsonl` that references the same artifact.

**Why:** Source #2 (Dhairya) baseline was 41% on a real engine; the 43/43 regression file passes only because the test fixture pins the SQL. Same trap repeats for any constraint scored only on unit tests — they pass in isolation and silently regress when the LLM, the schema parser, the synthesizer, or the response shaper changes. The IIT-GN user acceptance session will never run on 10 rows. Plan accordingly.

**How to apply:**
- Any agent claiming "DONE" on a task touching the 6 Hard Constraints must attach the evidence file path in their report.
- `/code-review-and-quality` and `/pre-commit` reject reports that cite only `pytest` counts without an evidence path.
- Quality Bar scorecard JSON is the single source of truth for release-tag readiness — not green test counts in a transient CI run.
- See `.claude/quality-bar.md` "Live Evidence Requirement" and `.claude/rules/audit/protocol.md` "Real Volume Reality Check".

**Source:** Grok external audit 2026-04-25 — formalized into the workflow 2026-04-26 alongside `feedback_tier_shape_boundary.md`.
