---
name: SKILL.md mass-deletion accident
description: Guard against unstaged deletions of .agents/skills/ SKILL.md files — agents reference these by path from CLAUDE.md, AGENTS.md, shishya_universal.md, and every protocol; missing files break the agent fleet silently
type: feedback
---

On 2026-04-26, a routine `git status` revealed 26 unstaged deletions under `.agents/skills/*/SKILL.md` — including all the universal skill manuals agents are required to read (`pre-commit`, `code-review-and-quality`, `python-backend`, `security-auditor`, `prompt-engineering-patterns`, etc.). HEAD had 50 SKILL.md files; working tree had 24. The deletions were never staged or committed, but they affected agents reading the working tree (most agent tooling reads files from disk, not from git HEAD).

Recovery: `git restore .agents/skills/` pulled them all back. Took 1 second.

**Why:** Multiple agents/processes operate on the working tree concurrently in this repo (frontend agents, backend agents, security agents). One of them ran a checkout/move/clean that wiped these files. Without verification, agents could silently fail to load their skill manuals and produce lower-quality work — or page back with "file not found" mid-protocol.

**How to apply:**
- Whenever `git status` shows `D .agents/skills/*/SKILL.md` or `D .claude/skills/*/SKILL.md` and the deletion isn't staged, treat as accidental and run `git restore` immediately. Don't commit deletions of skill manuals without explicit founder approval.
- Add a periodic check (could be a pre-commit gate or a `/self-evolve` step): `[ "$(find .agents/skills -name SKILL.md | wc -l)" -ge 50 ]` — block commit if floor drops.
- If a skill is genuinely deprecated, remove the directory and its references in `CLAUDE.md`, `.agents/AGENTS.md`, `.agents/prompts/shishya_universal.md`, and any protocol that names it — same commit, same PR. Never leave dangling references.

**Source:** Founder system-improvement track 2026-04-26 — caught during sprint LB-1..LB-5 mid-flight.
