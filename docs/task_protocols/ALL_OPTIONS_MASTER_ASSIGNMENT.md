# ALL OPTIONS — Master Task Assignment

**Date:** 2026-04-25  
**Decision:** Pick ONE option (or parallel combinations)  
**Goal:** Get to demo-ready state for the professor/ministry presentation

---

## THE THREE OPTIONS

### OPTION A: DEMO SPRINT (1 Day)
**Goal:** Make the professor demo bulletproof.

**Files:** `docs/task_protocols/demo_sprint/`

| ID | Protocol | Owner | Duration | Evidence |
|----|----------|-------|----------|----------|
| TP-A1 | Demo Script Walkthrough + Recording | TESTER | 2–3h | Screen recording |
| TP-A2 | Dashboard Data Binding Verification | FRONTEND | 2–3h | Screenshots |
| TP-A3 | Synthesizer Fix (Typo + Prose) | BACKEND | 2–3h | Before/after responses |
| TP-A4 | Killer Demo Queries Preparation | CODER | 1–2h | Verified query results |
| TP-A5 | UI Polish (Warnings + Mobile + States) | FRONTEND | 2–3h | Lighthouse report |

**Execution:**
```
WAVE 1 (Parallel): TP-A1, TP-A2, TP-A3, TP-A5
WAVE 2 (After): TP-A4
```

**Best for:** When the demo is imminent and the professor sees UI first.

---

### OPTION B: GAP CLOSURE SPRINT (2 Days)
**Goal:** Close GAP-A/B/C + produce evidence files A1-A20 + self-audit report v2.

**Files:** `docs/task_protocols/v4.1_execution/`

| ID | Protocol | Owner | Duration | Evidence |
|----|----------|-------|----------|----------|
| TP-001 | GAP-A — DB Co-sign Verification | CODER | 2–3h | A19 |
| TP-002 | GAP-B — 60s Drift Scheduler | CODER | 2–3h | A20 |
| TP-003 | GAP-C — HALL_OF_SHAME.md | SECURITY | 1–2h | File itself |
| TP-004 | Red Team 30× Attack Suite | SECURITY | 4–6h | A10 |
| TP-005 | Evidence Verification A1-A20 | CODER | 2–3h | INDEX.md |
| TP-006 | Self-Audit Report v2 | CODER | 3–4h | J report |

**Execution:**
```
WAVE 1 (Parallel): TP-001, TP-002, TP-003, TP-004
WAVE 2 (Sequential): TP-005 → TP-006
```

**Best for:** When you need court-defensible sovereign sign-off and ministry compliance.

---

### OPTION C: EXTERNAL AI AUDIT (1 Day Setup + Wait)
**Goal:** Find what you missed before the professor does.

**Files:** `docs/task_protocols/external_audit/`

| ID | Protocol | Owner | Duration | Evidence |
|----|----------|-------|----------|----------|
| TP-C1 | External AI Audit Execution | GURU/You | 1d + wait | 3+ AI responses |

**Execution:**
```
1. Gather 4 files
2. Copy prompt from audit_protocol.md Sec 13.6
3. Run on 3+ AIs
4. Collect Deliverable 7 from each
5. Merge, deduplicate, sort
6. The merged gap list = next sprint backlog
```

**Best for:** When you want independent eyes before a high-stakes demo.

---

## RECOMMENDED COMBINATIONS

**Fastest to Demo (2 Days):**
- Day 1: OPTION A (Demo Sprint) — fix what the professor sees
- Day 2: OPTION B Wave 1 (GAP-A/B/C only) — close the 3 local gaps
- Skip: TP-004 (Red Team 30×), TP-005, TP-006, TP-C1

**Most Bulletproof (3–4 Days):**
- Day 1: OPTION A (Demo Sprint)
- Day 2: OPTION B Wave 1 (GAP-A/B/C + Red Team)
- Day 3: OPTION B Wave 2 (Evidence + Self-Audit Report)
- Day 4: OPTION C (External Audit) — run in parallel with Day 2–3

**Minimum Viable (1 Day):**
- OPTION A only (TP-A1, TP-A2, TP-A3, TP-A5 in parallel)
- Skip everything else
- Risk: no audit trail, no gap closure, no independent verification

---

## HOW TO ASSIGN

Tell any agent:
> "Execute protocol `docs/task_protocols/<folder>/TP-XXX_*.md`. Fortify → Elevate → Immortalize. Report back PASS/FAIL + evidence paths."

Before any task is marked complete:
```bash
python -m pytest tests/ -x --tb=short   # backend
cd frontend && npm run build            # frontend
```

---

## EVIDENCE FOLDERS

```
evidence/2026-04-25/
├── demo_sprint/           ← Option A evidence
│   ├── A1_demo_walkthrough.mp4
│   ├── A1_demo_failures.md
│   ├── A2_tier1_dashboard.png
│   ├── A2_tier3_dashboard.png
│   ├── A3_synthesizer_before_after.md
│   ├── A4_killer_queries.md
│   ├── A5_lighthouse_report.json
│   └── ...
├── v4.1_execution/        ← Option B evidence
│   ├── A19_db_cosign_fix.log
│   ├── A20_drift_scheduler_fix.log
│   ├── A10_red_team_attacks_v41.log
│   ├── INDEX.md
│   └── J_self_audit_report_v2.md
└── external_audit/        ← Option C evidence
    ├── ai_claude_response.md
    ├── ai_gpt4_response.md
    ├── ai_gemini_response.md
    └── C1_master_gap_list.md
```

---

**Which option do you want? Or do you want the recommended 2-day combination?**
