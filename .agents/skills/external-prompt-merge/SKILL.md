---
name: external-prompt-merge
description: Canonical pattern for absorbing an external review or audit prompt into the NRG workflow so the prompt itself becomes disposable. Use when the founder pastes a long external review and asks to merge it into the project.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# External Prompt Merge

Use the canonical workflow at `.claude/skills/external-prompt-merge/SKILL.md`.

This active-agent wrapper exists so Codex sessions can discover the skill from `.agents/skills/` while Claude-oriented workflow files keep the source-of-truth skill in `.claude/skills/`.

Required behavior:

1. Read `.claude/skills/external-prompt-merge/SKILL.md`.
2. Vocabulary-scrub the source prompt before writing artifacts.
3. Classify each durable claim into the correct workflow target.
4. Extend existing workflow files instead of creating duplicates.
5. Sync memory entries to repo memory and auto-memory.
6. Run `bash scripts/forbidden_vocab_check.sh`.
7. Report the artifact paths and explicitly say the prompt is now disposable.
