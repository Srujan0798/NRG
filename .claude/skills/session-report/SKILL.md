---
name: session-report
description: Generate a structured session summary — tokens used, tasks completed, open items, learnings captured. Use at session end before signing off.
model-agnostic: true
---

# Session Report

## When to Use

At the end of every working session to:
- Communicate what was accomplished to the founder
- Capture learnings before context resets
- Hand off open items to next session cleanly
- Track token/cost efficiency over time (if tooling available)

## Process

### Step 1 — Task Inventory

```bash
# Review what changed this session
git diff --stat HEAD~5..HEAD 2>/dev/null || git status
git log --oneline -10
```

List:
- Tasks completed (K-* protocols closed, files changed)
- Tasks started but not finished
- New issues discovered during work

### Step 2 — Evidence Audit

For each completed task, verify evidence exists:
```bash
ls evidence/$(date +%Y-%m-%d)/
```

If a task was claimed DONE but no evidence file exists → downgrade to IN PROGRESS.

### Step 3 — Memory Update

For each new learning this session that should survive context reset:
1. Check `memory/MEMORY.md` — is there an existing entry to update?
2. If new: write `memory/<type>_<topic>.md` with frontmatter
3. Add pointer to `MEMORY.md` index (one line, under 150 chars)

Types: `user_`, `feedback_`, `project_`, `reference_`, `bugs_`, `patterns/`

### Step 4 — CURRENT_STATE.md Update

Update `.claude/CURRENT_STATE.md`:
- Close any K-* items completed
- Add any new blockers discovered
- Update quality bar if constraints changed status
- Update "Last updated" timestamp

### Step 5 — Report Output

```
SESSION REPORT — [date]
Model: [model name]

COMPLETED:
  - [task] → evidence: [file or "none — follow up"]
  - [task] → evidence: [file or "none — follow up"]

IN PROGRESS (hand off to next session):
  - [task] — current state: [what's done, what's left]

DISCOVERED:
  - [bug/issue found] → added to BACKLOG.md? [yes/no]

MEMORIES WRITTEN:
  - [memory file] — [what it captures]

QUALITY BAR:
  C1 DPDP: [PASS/PENDING]  C2 Audit: [PASS/PENDING]
  C3 DAG:  [PASS/PENDING]  C4 SLO:   [PASS/PENDING]
  C5 Drift:[PASS/PENDING]  C6 Egress:[PASS/PENDING]

OPEN BLOCKERS:
  - [blocker] — owner: [who/what unblocks it]
```

## Output

- Updated `CURRENT_STATE.md`
- Updated `memory/MEMORY.md` + any new memory files
- Session report printed to conversation

## For NRG

At session end, always check:
- `forbidden_vocab_check.sh` — did any session output introduce forbidden words into `.md` files?
- K-* protocols — are the open ones reflected accurately in CURRENT_STATE.md?
- Evidence freshness — any evidence older than 7 days used to claim DONE? Flag it.

BACKLOG.md is the long-term backlog. CURRENT_STATE.md is the sprint snapshot. Keep both current.

## Anti-Patterns

- Skipping session report when "nothing much happened" — context decay is the failure, not the size of the session
- Writing session report without updating CURRENT_STATE.md — next session starts cold
- Marking tasks DONE in the report without evidence — creates false quality bar claims
- Writing session data as memory (e.g., "today we fixed X") — memory should be timeless rules, not journals
