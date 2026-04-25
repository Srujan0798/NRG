# v4.1 FINAL ETERNAL — Master Task Assignment

**Date:** 2026-04-25  
**Sprint:** Single-sprint execution  
**Goal:** Close all local gaps (GAP-A/B/C), verify evidence files A1–A20, execute Red Team 30×, produce Self-Audit Report v2.  
**Guru Protocol:** Fortify → Elevate → Immortalize

---

## Execution Waves

```
WAVE 1 (Parallel — Start Immediately)
├── TP-001  GAP-A  DB Co-sign Verification        [CODER]     2–3h
├── TP-002  GAP-B  60s Drift Scheduler             [CODER]     2–3h
├── TP-003  GAP-C  HALL_OF_SHAME.md                [SECURITY]  1–2h
└── TP-004  Red Team 30× Attack Suite               [SECURITY]  4–6h

WAVE 2 (Sequential — Start after Wave 1)
├── TP-005  Evidence Verification A1–A20            [CODER]     2–3h
└── TP-006  Self-Audit Report v2                    [CODER]     3–4h
```

---

## Task Matrix

| ID | Protocol | Owner | Est. Duration | Blockers | v4.1 Ref |
|----|----------|-------|---------------|----------|----------|
| TP-001 | GAP-A — DB Co-sign Verification | CODER | 2–3h | None | Part B |
| TP-002 | GAP-B — 60s Drift Scheduler | CODER | 2–3h | None | Part B |
| TP-003 | GAP-C — HALL_OF_SHAME.md | SECURITY | 1–2h | None | Part B |
| TP-004 | Red Team 30× Attack Suite | SECURITY | 4–6h | None | Part G |
| TP-005 | Evidence Verification A1–A20 | CODER | 2–3h | TP-001, TP-002, TP-003 | Part A |
| TP-006 | Self-Audit Report v2 | CODER | 3–4h | TP-005 | Part J |

---

## Evidence Folder

All evidence must be written to:
```
evidence/2026-04-25/
```

Old evidence from `2026-04-24/` may be referenced but **must not be modified**.

---

## Sign-off Gate

Before any task is marked complete, the agent **must** run the local test suite:

```bash
python -m pytest tests/ -x --tb=short
```

If this fails, the task is **not** Immortalized. Fix first, evidence second.

---

## Quick Reference: v4.1 Protocol Sections

| Section | Content | Protocol |
|---------|---------|----------|
| A | Evidence files A1–A20 | TP-005 |
| B | GAP-A/B/C fixes | TP-001, TP-002, TP-003 |
| D | Comprehensive checklist D1–D10 | TP-005 (verify), TP-006 (document) |
| E | Load test | TP-005 |
| G | Red Team 30 attacks | TP-004 |
| H | Benchmark scores 5/6 | TP-005 |
| I | Live proof test | TP-005 |
| J | Self-audit report | TP-006 |

---

## How to Execute

1. **Guru** assigns one or more protocols to an agent.
2. **Agent** reads the protocol file (`TP-00X_*.md`).
3. **Agent** executes Fortify → Elevate → Immortalize.
4. **Agent** produces evidence in `evidence/2026-04-25/`.
5. **Agent** reports back with: PASS / FAIL + evidence paths.
6. **Guru** verifies acceptance criteria before closing.
