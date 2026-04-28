---
name: claudemd-management
description: Audit and maintain CLAUDE.md quality — capture session learnings, prune stale rules, keep project memory current. Use at session end or when CLAUDE.md feels out of sync.
model-agnostic: true
---

# CLAUDE.md Management

## When to Use

- At session end when new patterns or rules were discovered
- When CLAUDE.md instructions contradict actual observed behavior
- When a rule in CLAUDE.md was never triggered this sprint
- After an external audit that changes project constraints

## Process

### Audit Pass (read before writing anything)

1. Read `CLAUDE.md` top to bottom
2. For each rule, ask: "Was this followed this sprint? Would an agent know when to trigger it?"
3. Flag:
   - **Stale** — references files/commands that no longer exist
   - **Redundant** — covered by a more specific skill already in `.claude/skills/`
   - **Ambiguous** — could be interpreted two different ways
   - **Missing** — behavior observed this session that isn't captured anywhere

### Capture Learnings

For each new pattern or correction from this session:
1. Check if it belongs in `CLAUDE.md` (project-wide rule) or in `memory/` (factual context)
2. CLAUDE.md gets: rules, constraints, session start procedures, skill directory
3. `memory/` gets: bugs found, project status, external audit findings, founder directives

Rule of thumb:
```
"Do X when Y happens"  → CLAUDE.md
"X happened on date Z" → memory/
```

### Update Rules

```bash
# Before editing, check current rule count
grep -c "^###\|^##\|^-" .claude/CLAUDE.md

# After editing, verify no forbidden vocab crept in
bash scripts/forbidden_vocab_check.sh
```

### Prune Stale Rules

A rule is stale if:
- It references a file path that no longer exists
- It references a command that fails when run
- It was added for a one-time event and has no future relevance

Mark stale rules with `<!-- STALE: reason -->` before deleting — gives one sprint grace period.

### Skills Directory Section

After adding new skills to `.claude/skills/` or `.agents/skills/`, update the Skills Directory table in CLAUDE.md:
- Correct category (NRG Core / Strategy / Engineering / Sovereign / Operations / Legal / Design)
- Correct count in section headers

## Output

- Updated `CLAUDE.md` with new rules, removed stale entries
- Updated skills directory table with new skill links
- One-line entry in `memory/MEMORY.md` if a new memory file was created

## For NRG

Priority rules to keep current in CLAUDE.md:
- Quality Bar constraints (C1–C6) and which are PASSING/PENDING
- K-* active protocols (update when closed)
- Session start steps (should stay under 6 steps)
- Skills directory counts (28 in .agents/skills/, check current count in .claude/skills/)

Do NOT put in CLAUDE.md:
- Specific SQL queries or schema details (db_struct.sql is authoritative)
- Evidence file lists (evidence/ directory is self-documenting)
- Agent conversation history (use memory/ for that)

## Anti-Patterns

- Adding rules in CLAUDE.md that duplicate a SKILL.md — link to the skill instead
- Writing rules that only apply to one task — use task comments, not global rules
- Leaving contradictory rules — if two rules conflict, resolve before committing
- CLAUDE.md over 300 lines — if growing beyond this, extract sections into skills
