# OPTION A — DEMO SPRINT: Master Task Assignment

**Date:** 2026-04-25  
**Sprint:** Single-day execution  
**Goal:** Make the professor demo bulletproof. Every screen, every click, every query must work flawlessly.  
**Guru Protocol:** Fortify → Elevate → Immortalize

---

## Execution Order

```
WAVE 1 (Parallel — Start Immediately)
├── TP-A1  Demo Script Walkthrough + Recording    [TESTER]    2–3h
├── TP-A2  Dashboard Data Binding Verification    [FRONTEND]  2–3h
├── TP-A3  Synthesizer Fix (Typo + Prose)         [BACKEND]   2–3h
└── TP-A5  UI Polish (Warnings + Mobile + States) [FRONTEND]  2–3h

WAVE 2 (After Wave 1)
└── TP-A4  Killer Demo Queries Preparation        [CODER]     1–2h
```

---

## Task Matrix

| ID | Protocol | Owner | Est. Duration | Blockers | Evidence |
|----|----------|-------|---------------|----------|----------|
| TP-A1 | Demo Script Walkthrough | TESTER | 2–3h | None | Screen recording |
| TP-A2 | Dashboard Data Binding | FRONTEND | 2–3h | None | Screenshots |
| TP-A3 | Synthesizer Fix | BACKEND | 2–3h | None | Before/after responses |
| TP-A4 | Killer Demo Queries | CODER | 1–2h | TP-A1, TP-A2, TP-A3 | Verified query results |
| TP-A5 | UI Polish | FRONTEND | 2–3h | None | Lighthouse report |

---

## Evidence Folder

All evidence must be written to:
```
evidence/2026-04-25/demo_sprint/
```

---

## Sign-off Gate

Before any task is marked complete:
- Frontend tasks: `npm run build` succeeds, 0 ESLint errors
- Backend tasks: `pytest tests/ -x --tb=short` passes
- All tasks: Evidence file exists and is non-empty

---

## Reference Files

- Demo script: `.claude/rules/ux_audit_protocol.md` Section 10
- Demo risk map: `.claude/rules/ux_audit_protocol.md` Section 13
- Killer queries template: `.claude/rules/ux_audit_protocol.md` Section 14
- Demo-readiness skill: `.claude/skills/demo-readiness/SKILL.md`
