# External AI Audit
**Date:** 2026-04-25
**Skill:** `.claude/skills/external-audit/SKILL.md`

---

## Applying External Audit to NRG

### When to Use

The skill specifies:
- Before any demo where ₹50L+ is on the line
- After completing a major milestone
- Quarterly sanity checks
- When agents go easy on their own work

**NRG Context:** Multiple demos likely with professor, ministry, and industry partners. External audit would provide independent validation.

### The Multi-AI Strategy

The skill recommends running the same prompt + 4 files on **at least 3 different AIs**:

| Agreement | Action |
|-----------|--------|
| All 3 flag as broken | Fix immediately |
| 2 out of 3 flag | Investigate seriously |
| Only 1 flags | Verify with evidence |
| None flag but known broken | Add to own list |

---

## Required Files for NRG External Audit

| File | Path | Status |
|------|------|--------|
| Core Idea | `Core_Idea_Clean.md` | ✓ Available |
| Schema | `db_struct.sql` | ✓ Available (58 tables) |
| Backlog | `BACKLOG.md` | ✓ Available |
| Dhairya Audit | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | ✓ Available |

**Optional 5th:** Latest self-audit report

---

## NRG Known Gaps (Internal Audit)

Based on session data and CLAUDE.md:

| Gap | Severity | Blocks Demo |
|-----|----------|-------------|
| Text-to-SQL accuracy 7/17 (41%) | HIGH | YES |
| 263 failing tests | MEDIUM | NO |
| 40 tables missing from dev schema | HIGH | YES (for Dhairya queries) |
| API response time 7.2s avg | MEDIUM | NO |

### Top Questions to Ask External AI

1. "Is the 3-tier RBAC actually enforced at the data layer, not just API?"
2. "Does the audit chain truly prevent tampering, or just detect it?"
3. "Is the Text-to-SQL pipeline vulnerable to schema poisoning?"
4. "Are there PII leakage vectors in the RAG pipeline?"
5. "Does the LangGraph planner properly decompose complex queries?"

---

## How to Run External Audit (Template)

### Step 1: Gather Files
```bash
# Copy 4 required files to a temp directory for the AI audit
cp Core_Idea_Clean.md /tmp/nrg_audit/
cp db_struct.sql /tmp/nrg_audit/
cp BACKLOG.md /tmp/nrg_audit/
cp docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md /tmp/nrg_audit/
```

### Step 2: Use Audit Prompt
Open `.claude/rules/audit_protocol.md` Section 13.6 for the copy-paste ready prompt template.

### Step 3: Run on 3+ AIs
- Claude (this system)
- Grok
- GPT-4
- Gemini

### Step 4: Collect Deliverable 7 (Gap List)
Each AI produces a gap list. Extract all GAP entries.

### Step 5: Merge and Sort
Sort by "Blocks Demo: YES" items to top.

---

## NRG External Audit Status

**Last External Audit:** Unknown
**Recommendation:** Schedule external audit before next major demo

**Priority gaps to validate externally:**
1. Text-to-SQL accuracy (7/17 → target 17/17)
2. RBAC data-layer enforcement
3. Audit chain integrity guarantees
4. PII leakage vectors

---

## Skill Application Evidence

This document applies the external-audit skill framework to NRG, identifying:
1. The multi-AI audit strategy requirements
2. Required files and their locations
3. Known internal gaps for external validation
4. Template process for conducting the external audit

**Key insight from skill:** "Independent AI audits find what internal agents miss. Not because internal agents are bad — because they built the system and know where the bodies are buried."

**Recommendation:** Schedule external audit with 3+ AI systems before next professor/ministry demo.