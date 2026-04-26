---
name: Storage Location Rule
description: NEVER store memory/workflow files in local ~/.claude/ path — ALWAYS store inside the repo at .claude/memory/ so they're committed, pushed, and accessible remotely
type: feedback
---

ALWAYS store memory files inside the repo at `.claude/memory/`, NEVER in the local `~/.claude/projects/` path.

**Why:** The local `~/.claude/` path is machine-specific. It doesn't get committed to git, doesn't get pushed to remote, and can't be accessed from other machines. The Founder needs all workflow and memory files visible in the project structure and accessible anywhere via git.

**How to apply:** When writing or updating any memory file, write to `.claude/memory/` inside the repo (e.g., `/Users/srujansai/Desktop/NRG/.claude/memory/filename.md`). After writing, also sync to the local `~/.claude/projects/.../memory/` path so Claude Code's auto-memory system can still read it. But the repo copy is the source of truth.
