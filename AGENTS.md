# NRG Agent Entry Point

NRG is a sovereign research answer engine. Agents must preserve the product
truth in `Core_Idea_Clean.md`, the canonical schema in `db_struct.sql`, the
Dhairya SQL audit evidence, and the verified corpus mirror under `CORPUS/`.

## Start Here

1. Read `.agents/AGENTS.md` for execution-agent rules.
2. Read `.claude/CURRENT_STATE.md` for current status, blockers, and quality bar.
3. Read `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` before touching source-of-truth files.
4. Check `git status --short` and explain any existing changes before editing.

## Work Mode

- If assigned implementation work, make focused production code changes and verify them.
- If assigned strategy or delegation work, use `.claude/CLAUDE.md` as the Guru protocol.
- Do not import external v1.0 app, prompt, or skill content blindly. Distill useful rules into the canonical docs, then discard duplicates.
- Do not claim NRG is "100% better", "final", or "perfect" without fresh evidence. Use `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN` per surface.

## Required Proof

Before reporting completion, include:

- Files changed.
- Tests or checks run.
- Evidence paths created or updated.
- Remaining blockers and known gaps.
