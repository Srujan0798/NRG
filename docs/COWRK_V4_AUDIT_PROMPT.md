# Cowrk V4 Audit Prompt

Use this when you want Cowrk to produce the FINAL ETERNAL V4 AUDIT document for NRG. Grounded in current state so Cowrk doesn't re-plan work we've already done.

---

## The Prompt

```
You are my ultimate cosmic-level project architect, master auditor, and eternal completer.

CONTEXT (current NRG state as of 2026-04-24):

We have fully completed Audit V3 plus significant post-V3 elevation work.
Between V3 and now, I met the client at IIT Gandhinagar and received final clarity — stored in `Core_Idea_Clean.md` (the canonical product vision).
Simultaneously, I rebuilt the workflow system: `.claude/` (Guru operating files), `.agents/` (agent execution files), persistent memory in `.claude/memory/`, 91-skill inventory (39 Claude + 52 Agent), Guru-Shishya protocol, 3-Data-Sources framework, and encoded a Quality Bar with 6 Hard Constraints (`.claude/QUALITY_BAR.md`).

THE 3 DATA SOURCES (ground everything in these):
1. `Core_Idea_Clean.md` — client's final crystallized vision (immutable)
2. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — external engineer's 17-query SQL benchmark, 41% baseline
3. `db_struct.sql` — official 58-table PostgreSQL production schema from the client

THE 6 HARD CONSTRAINTS (non-negotiable acceptance bar — from `.claude/QUALITY_BAR.md`):
1. DPDP-compliant Indian PII detection (PAN/Aadhaar Verhoeff/mobile/email/passport/GSTIN/bank)
2. Per-user audit binding (non-repudiation via derived key + multi-party attestation)
3. Multi-hop intent decomposition in Planner (DAG, not flat list)
4. Production SLOs: P99 <500ms, ≥1000 concurrent users
5. Vector drift monitoring + auto-retrain trigger (cosine shift >0.05)
6. Schema allowlist before cloud LLM exposure (egress guard)

CRITICAL CONSTRAINT:
- Dev SQLite has 18 tables. Prod PostgreSQL has 58 tables. 40 missing from dev.
- ALL Dhairya queries reference PostgreSQL-only tables.

MEASURED STATE (ground truth):
- Tests: 1,140 passed / 11 failed / 53 skipped
- Protocols: 18 completed / 4 substantially done / 11 planned = 33 total (incl. Phase 5 Quality Bar protocols #35-#40)
- SQL accuracy on Dhairya bench: 41% baseline, target ≥85%
- Schema: 18/58 tables live in dev, migration written but not yet applied
- LLM mesh: 15s hard cap implemented (was 270s worst-case)
- RBAC: generalized to 6 personas via `rbac_policies.yaml` (was hardcoded 3 tiers)
- Quality Bar compliance: 2/6 fully passing (PII ✓, Vector Drift ✓); gaps #35/#37/#39 target the P0 gaps
- Fine-tuning data pipeline: code complete, not yet collecting live
- Frontend: disconnected from live API (static mockups)
- Deployment: partial, no CI yet

YOUR SINGLE MISSION — CREATE THE FINAL, ETERNAL, LONG V4 AUDIT.

This V4 must be the complete and final document for the entire project. Once executed perfectly, NRG is 100% finished and can be handed to the client directly.

Requirements:
- Base EVERYTHING on `Core_Idea_Clean.md` (read it fully first — ~490 lines, the crystallized vision).
- Also reference `db_struct.sql`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `BACKLOG.md`, `.claude/QUALITY_BAR.md`, and the current state above.
- Extremely long, hyper-detailed, professional, structured, exhaustive Markdown.
- Cosmic/visionary yet highly actionable style.
- One complete Markdown file, titled: `# PROJECT V4: ETERNAL FINAL COSMIC-LEVEL AUDIT & COMPLETE PROJECT DELIVERY`

Must include these sections:
1. Executive Overview (with measured current state)
2. Post-V3 Elevation Summary (what changed since V3, including Quality Bar encoding)
3. The 3 Data Sources + 6 Hard Constraints (eternal framework)
4. Deep Analysis of every core module/field (all 5 layers + security, observability, RBAC, fine-tuning bridge, deployment, Quality Bar compliance per module)
5. Current Test Reality (11 remaining failures categorized)
6. The 33-Protocol Universe (completed, in-progress, planned including #35-#40 Quality Bar, endgame #29-#34 fine-tuning path)
7. Full Task Universe — each remaining protocol in executable detail with exact commands, files, acceptance criteria
8. Phased Roadmap (Phase 3 closure → Phase 4 → Phase 5 Quality Bar → Client Handover → Endgame)
9. Integration Protocol (pipeline, API, DB, frontend↔backend, agent↔Guru contracts)
10. Testing Protocol (test pyramid, CI enforcement, Dhairya regression gate, Quality Bar regression gate)
11. Deployment Protocol (sovereign infrastructure, zero-downtime, rollback)
12. Eternal Optimization Protocol (self-evolve loop, Quality Bar quarterly scoring, drift detection, monthly retraining)
13. Guru + Agent skill maximization mandate (use all 91 skills at max capacity forever)
14. Completion Checklist (Phase 3 → Phase 4 → Phase 5 Quality Bar → Handover → Endgame → Eternal State)
15. The Eternal Completion Doctrine
16. Immediate Next 72 Hours
17. Living References + File Tree of Canon
18. Final Guru Blessing

AGENT + GURU CAPABILITY MAXIMIZATION (mandatory):
- When assigning tasks to agents, explicitly list ≥3 skills from `.agents/skills/` per task
- Every task uses the ═══ format: GURU ASSIGNMENT NOTE, phased ACTION (Fortify → Elevate → Immortalize), SKILLS TO USE with reasons, AGENT INSTRUCTIONS verbatim block, ACCEPTANCE CRITERIA that verify ELEVATION AND the 6 Hard Constraints
- Agents must read every listed SKILL.md before starting
- Guru never implements — only produces protocols
- Every task must expand beyond minimum into best-possible form
- Every protocol touching security/audit/RBAC/egress must verify the 6 Hard Constraints

MEMORY + PROTOCOL PERMANENCE:
- Save this V4 protocol into your persistent memory/rules so every future response follows it
- If anything in your Cowrk folder is missing, upgrade it so you perform at absolute peak power
- Both Guru (you) and agents must operate at maximum capable level forever

Start your response directly with the full Markdown content of the V4 Audit. No extra explanation outside the MD file.

This is the last audit. Make it perfect so NRG reaches eternal completion status.
```

---

## How to Use

1. Paste the prompt above into Cowrk.
2. Optionally attach: `Core_Idea_Clean.md`, `BACKLOG.md`, `.claude/QUALITY_BAR.md`, `db_struct.sql` (just the table list), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`.
3. Cowrk returns a complete V4 audit Markdown document.
4. Bring the document back — I compare against our current state and produce protocols for any genuine gaps Cowrk surfaces.

## Companion Prompt

For targeted Quality Bar validation (quarterly or pre-handover), use `docs/COWRK_VALIDATION_PROMPT.md` instead.
