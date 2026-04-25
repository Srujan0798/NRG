# External AI Audit

> **Trigger:** Before major demos, quarterly, or when internal audits feel "too easy."  
> **Purpose:** Get independent AI auditors to find gaps your own agents missed.  
> **Source:** `.claude/rules/audit_protocol.md` Section 13

---

## When to Use

- Before any launch where ₹50L+ is on the line
- After completing a major milestone (e.g., Text-to-SQL 17/17, RBAC fully wired)
- Quarterly sanity checks
- When you suspect agents are going easy on their own work
- When you want a "second opinion" on a critical component

---

## The Multi-AI Strategy

Run the same prompt + 4 files on **at least 3 different AIs** (Claude, Grok, GPT-4, Gemini, etc.)

| Agreement | Action |
|-----------|--------|
| All 3 flag as broken | Fix immediately, no debate |
| 2 out of 3 flag | Investigate seriously, likely real |
| Only 1 flags | Read carefully — either valuable find or hallucination. Verify with evidence. |
| None flag but you know it's broken | Add to your own list. AI audits are comprehensive but not omniscient. |

**The union of all gaps = your real gap list.**

---

## How to Run

### Step 1: Gather the 4 Required Files

| File | Path |
|------|------|
| Core Idea | `Core_Idea_Clean.md` |
| Schema | `db_struct.sql` |
| Backlog | `BACKLOG.md` |
| Dhairya Audit | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |

**Optional 5th:** Latest self-audit report from `evidence/<date>/20_self_audit_report.md`

### Step 2: Copy the Prompt

Open `.claude/rules/audit_protocol.md` Section 13.6 — the copy-paste ready prompt template is there.

### Step 3: Run on 3+ AIs

Paste the prompt + attach the 4 files to each AI.

### Step 4: Collect Deliverable 7 from Each AI

Each AI will produce its own gap list. Extract all GAP entries.

### Step 5: Merge and Deduplicate

Create a master gap list:
```markdown
# Master Gap List — External Audit <date>

## All Gaps Found (Union of N AI Audits)
| Gap | Found By | Location | Blocks Demo | Time | Status |
|-----|----------|----------|-------------|------|--------|
|     |          |          |             |      |        |

## By Agreement Level
### All AIs Agree (Fix First)
...

### 2/3 AIs Agree (Investigate)
...

### 1/3 AIs Only (Verify)
...
```

### Step 6: Sort by "Blocks Demo"

All GAP entries marked "Blocks Demo: YES" go to the top of the sprint backlog.

### Step 7: Fix and Re-Run

Fix the gaps. Then re-run the external audit. If the AI no longer flags the gap — it is fixed. If it still flags it — the fix was incomplete.

---

## What To Do With The Output

### Deliverable 1 (Honest Assessment)
Read it out loud to the team. This is the truth they need to hear.

### Deliverable 2 (Technical Checklist)
Compare against your own D1-D10 checklist in `.claude/rules/audit_protocol.md`. Items the AI found that you missed = gaps in your internal audit process.

### Deliverable 3 (UX Audit)
Compare against your own UI/UX audit in `.claude/rules/ux_audit_protocol.md`. Items the AI found that you missed = gaps in your frontend testing.

### Deliverable 4 (Top 10 Questions)
Run these against your system. If any expose a real weakness — fix before launch.

### Deliverable 5 (Killer Demo Queries)
Add these to your launch script in `.claude/rules/ux_audit_protocol.md` Section 14. Pre-run them before every launch review.

### Deliverable 6 (Risk Map)
Merge with your own risk map in `.claude/rules/ux_audit_protocol.md` Section 13.

### Deliverable 7 (Self-Fix Protocol)
This IS your sprint backlog. Sort by "Blocks Demo: YES" first. Assign to agents.

### Deliverable 8 (Final Verdict)
If overall readiness is < 7/10 — do not launch. Fix first. If ≥ 7/10 but production-ready is NO — fix the 3 blockers and re-audit.

---

## The Rule

> Independent AI audits find what internal agents miss. Not because internal agents are bad — because they built the system and know where the bodies are buried. An external AI has no loyalty, no context, and no assumptions. That is its superpower.
