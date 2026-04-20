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

### Step 2: Read the Backlog
Read these files for remaining work:
- `AUDIT_V3_FINAL.md` — master task list (40 tasks, check which are done)
- `Core_Idea_Clean.md` — vision (are we aligned?)
- Memory files — sprint retrospectives, bug patterns, what failed

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
For each P1 task, produce a copy-paste-ready task block:
```
TASK: [name]
AGENT: [backend/frontend/ml/devops/security]
FILES: [exact file paths]
PROBLEM: [what's wrong]
ACTION: [what to do]
ACCEPTANCE: [how to verify it's done]
DEPENDS ON: [other tasks, or "none"]
```
