---
name: self-evolve
description: GUARDIAN evolution — analyzes what happened in the last sprint/cycle, updates rules, memory, CLAUDE.md, and skills to prevent repeat failures. Use /self-evolve after each sprint.
allowed-tools: Bash(git *) Bash(.venv/bin/python *) Bash(pytest *) Read Grep Glob Edit Write
---

# Self-Evolution — Guardian Agent

You are the system's immune system. After every sprint, you analyze what happened and make the system smarter.

## Evolution Protocol

### Step 1: Gather Evidence
```bash
# What changed this sprint?
git log --since="2 weeks ago" --oneline --stat

# What tests failed recently?
git log --since="2 weeks ago" --all --grep="fix:" --oneline

# What was the test pass rate?
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -3
```

**Also check the 3 Data Sources** (see `.claude/CLAUDE.md` "THE 3 DATA SOURCES"):
- Has `Core_Idea_Clean.md` been updated since last sprint?
- Has `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` accuracy improved from 41% baseline?
- Has `db_struct.sql` schema gap (18 dev vs 58 prod tables) been addressed?
- Ask the Founder: any NEW external inputs received since last session?

### Step 2: Pattern Analysis

Look for:
1. **Recurring bugs**: Same type of fix appearing multiple times → need a NEW RULE
2. **Test gaps**: Features that shipped without tests → need coverage enforcement
3. **Security near-misses**: Anything that almost leaked PII or broke auth → need stronger gates
4. **Performance regressions**: Things getting slower → need benchmarks
5. **Architecture drift**: Code not following established patterns → need updated CLAUDE.md

### Step 2.5: Deep Audit — Three Power Questions

After pattern analysis, ALWAYS answer these three questions. They force thinking our normal workflow misses.

**POWER GAP — Are we behind the state-of-the-art?**
Compare NRG's current architecture against what's possible TODAY in agentic AI:
- Routing: Are we using LLM-augmented routing or still regex-only?
- Memory: Are we using vector + graph memory or just flat files?
- Agent communication: Can agents share mid-task discoveries, or do they work in isolation?
- Self-healing: Does the system auto-detect and recover from failures, or wait for humans?
- Observability: Do we have real-time tracing (Langfuse/LangSmith), or are we flying blind?

For each gap found: estimate impact (high/medium/low) and effort (days). Add high-impact, low-effort items to BACKLOG.md immediately.

**CROSS-POLLINATION — What did agents learn that ALL agents should know?**
Review completed tasks from this sprint. For each:
- Did the agent discover a new pattern? → Add to `.claude/CLAUDE.md` or relevant skill
- Did the agent work around a limitation? → File it as a system improvement
- Did the agent produce reusable code/logic? → Extract to a shared module or skill
- Did the Founder correct anything? → Update `.claude/` or `.agents/` files PERMANENTLY so it never repeats

The goal: every agent session makes the NEXT agent session smarter. Knowledge must flow from completed tasks into system files, not die in conversation history.

**HORIZON CHECK — Will this survive 10× scale?**
NRG today: 5,615 researchers, 19,322 vectors, 3 personas, 1 LLM provider active. Dev SQLite = 18 tables, Prod PostgreSQL = 58 tables (40 missing — `[SCHEMA]` blocker).
Ask for each architectural decision made this sprint:

**QUALITY BAR CHECK — Are we compliant with the 6 Hard Constraints?**
Read `.claude/QUALITY_BAR.md`. Score each of the 6 constraints on a 1–10 scale:
1. DPDP Indian PII detection
2. Per-user audit binding (non-repudiation)
3. Multi-hop intent decomposition
4. P99 <500ms / ≥1000 concurrent SLOs
5. Vector drift monitoring + auto-retrain trigger
6. Schema allowlist before cloud LLM exposure

For any constraint scoring below 7, add/verify a BACKLOG protocol that addresses it. Report compliance as `X/6 fully compliant` in the Evolution Report.

**LETHAL ASSUMPTIONS REVIEW — What are we betting on that could break us?**
List the Top 3 lethal assumptions currently live in the system. For each:
- What is the assumption?
- What would break if it's wrong?
- What's the mitigation?
Example: "Assumption: cloud LLM providers will always return within 15s. If wrong: #11 mitigates with local SLM fallback."
- What happens at 50,000 researchers? Does SQLite hold? (No — PostgreSQL migration path must be ready)
- What happens at 200,000 vectors? Does Qdrant HNSW scale? (Check segment config)
- What happens with 10 personas instead of 3? Does RBAC tier filtering generalize?
- What happens with 100 concurrent users? Does the ThreadPool / connection pool hold?
- What happens when DPDP-2023 gets amended? Is consent logic configurable or hardcoded?

For each wall identified: add a BACKLOG.md entry tagged `[SCALE]` with the threshold where it breaks.

### Step 3: Update the System

For each pattern found:

**If it's a code convention** → Update `.claude/rules/backend.md` or `frontend.md`:
```
Read the current rules file, add the new rule with WHY it exists.
```

**If it's a project-wide pattern** → Update `.claude/CLAUDE.md`:
```
Add to the DO NOT section or the Architecture Patterns section.
```

**If it's a recurring mistake** → Update memory:
```
Write to .claude/memory/bugs_patterns.md (IN THE REPO)
Include: what the bug was, why it happened, how to prevent it.
```

**If it's a workflow improvement** → Update the relevant skill:
```
Add a new check to /pre-commit, or a new section to /code-review.
```

**If it's a sprint learning** → Update memory:
```
Write to .claude/memory/sprint_retrospective.md (IN THE REPO)
Include: what worked, what didn't, what to do differently.
```

### Step 4: Produce Evolution Report

```
## Evolution Report — Sprint [N]

### New Rules Added
- [rule]: [why]

### Memory Updated
- [file]: [what changed]

### Skills Updated
- [skill]: [what was added]

### 3 Data Sources Status
- Core Idea (Data Source 1): [current / updated / needs refresh]
- Dhairya SQL Audit (Data Source 2): [accuracy: X% / benchmark status]
- PostgreSQL Schema (Data Source 3): [schema gap: X tables remaining / integration status]

### Quality Bar Compliance (X/6)
| Constraint | Score (1-10) | Protocol if <7 |
|---|---|---|
| 1. DPDP PII | X | — |
| 2. Per-user audit | X | — |
| 3. Multi-hop planner | X | — |
| 4. P99 + concurrent SLOs | X | — |
| 5. Vector drift + retrain | X | — |
| 6. Schema allowlist | X | — |

### Lethal Assumptions Review
1. [Assumption] — [if wrong, X breaks] — [mitigation]
2. [Assumption] — [if wrong, X breaks] — [mitigation]
3. [Assumption] — [if wrong, X breaks] — [mitigation]

### Sprint Classification (DELETE / REWRITE / MERGE / BUILD-NEW)
- DELETE: [modules or code removed this sprint]
- REWRITE: [modules significantly refactored]
- MERGE: [modules consolidated]
- BUILD-NEW: [new modules added]

### Metrics
- Tests: X passed / Y failed (trend: improving/degrading)
- Coverage: X% (trend)
- SQL accuracy: X% (baseline 41%, target 85%)
- Schema gap: X/58 tables integrated
- Security issues found: N (trend)
- Commits this sprint: N
- Bugs fixed: N
- Features shipped: N

### Power Gap Assessment
- [gap]: [impact] / [effort] / [action: BACKLOG or immediate]

### Cross-Pollination
- [agent task] → [learning extracted] → [updated file]

### Horizon Flags
- [decision] breaks at [scale threshold] → [BACKLOG entry tagged SCALE]

### Recommendation for Next Sprint
[What to focus on based on ALL the data — patterns, power gaps, horizon flags, schema gap, SQL accuracy]
```

### Step 5: Verify No Regressions
```bash
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
If the evolution changes broke anything → revert and flag.
