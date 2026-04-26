---
name: External-prompt-merge skill
description: Canonical pattern for absorbing an external review/audit prompt (Grok, Cowrk, validator, professor critique) into the NRG workflow so the prompt becomes disposable. Always invoke this skill when the founder pastes a long external review.
type: reference
---

When the founder pastes an external review/audit prompt (Grok, Cowrk, ministry feedback, professor critique, etc.) and asks Claude to "merge it" / "use it for the project" / "no need of this prompt again", invoke the **`external-prompt-merge`** skill at `.claude/skills/external-prompt-merge/SKILL.md`.

**Why:** The founder repeatedly burned cycles on the same loop — Claude produced a new task protocol from the prompt, founder corrected "no, merge it like before". Two prior wraps (Grok 2026-04-25, Cowrk 2026-04-26) followed the same pattern by hand. The skill captures it once.

**How to apply:**
- Vocabulary scrub the prompt FIRST (production-only rule, no launch framing).
- Classify every claim into: permanent rule / Quality Bar addition / runbook / test corpus / sprint blocker / bug pattern / reference / verdict template / already-covered / out-of-scope.
- Write each chunk to its proper file (memory / rule / runbook / corpus / protocol / BACKLOG) — never leave durable content in chat only.
- Sync memory to BOTH `.claude/memory/` (repo) AND `~/.claude/projects/-Users-srujansai-Desktop-NRG/memory/` (auto-memory).
- Verify forbidden-vocab gate exits 0; commit; push; explicitly tell the founder "the prompt is now disposable" with the artifact list.

**Source:** Founder edict, repeated across 2026-04-25 and 2026-04-26 sessions — promoted to canonical skill 2026-04-26.
