---
name: sprint-plan
description: Plan the next sprint — read backlog, memory, current state, produce prioritized task assignments for agents. Use /sprint-plan to create next sprint.
allowed-tools: Bash(git *) Bash(.venv/bin/python *) Bash(pytest *) Read Grep Glob
---

# Sprint Planning

You are planning the next 2-week sprint for the NRG agent team.

## Planning Protocol

### Step 1: Assess Current State
```bash
# What's the test status?
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -3

# What's been done recently?
git log --since="2 weeks ago" --oneline | head -20

# Any uncommitted work?
git status -s
```

### Step 2: Read the Backlog & Data Sources
Read these files for remaining work:
- `BACKLOG.md` — active task backlog with priorities (P0/P1/P2), scale flags, and protocol status
- `Core_Idea_Clean.md` — vision (Data Source 1 — are we aligned?)
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — SQL benchmark (Data Source 2 — 41% accuracy, target 85%)
- `db_struct.sql` — official PostgreSQL schema (Data Source 3 — 58 tables, 40 missing from dev)
- Memory files — sprint retrospectives, bug patterns, what failed

**Schema Gap Awareness**: Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables. Any task touching SQL/schema must account for this. See `.claude/CLAUDE.md` "THE 3 DATA SOURCES" for full details.

### Step 3: Prioritize

Priority matrix:
```
                    HIGH IMPACT
                        │
           P1           │          P2
     (Do first)         │    (Do second)
                        │
   ─────────────────────┼──────────────────
                        │
           P3           │          P4
     (Do if time)       │     (Backlog)
                        │
                    LOW IMPACT

   LOW EFFORT ──────────┼────────── HIGH EFFORT
```

### Step 4: Assign to Agent Roles

Output format:
```
## Sprint [N] Plan — [Date Range]

### Sprint Goal
[One sentence: what does success look like?]

### P1 — Must Complete
| Task | Agent | Files | Acceptance Criteria |
|------|-------|-------|-------------------|
| ... | Backend | ... | ... |

### P2 — Should Complete
| Task | Agent | Files | Acceptance Criteria |
|------|-------|-------|-------------------|

### P3 — Stretch
| Task | Agent | Files | Acceptance Criteria |

### Dependencies
[Which tasks block which]

### Risks
[What could go wrong]
```

### Step 5: Produce Task Protocols
For each P1 task, produce a copy-paste-ready task protocol using the FULL ═══ format from `.claude/GURU_PROTOCOL.md` Section 3. This includes:
- GURU ASSIGNMENT NOTE (the WHY)
- Phased ACTION (Fortify → Elevate → Immortalize)
- 3+ SKILLS with reasons
- AGENT INSTRUCTIONS block (verbatim from GURU_PROTOCOL.md Section 3)
- ACCEPTANCE CRITERIA that verify ELEVATION, not just "it works"

**NEVER produce flat step lists or simple fix-tasks.** Every task is an elevation protocol.
