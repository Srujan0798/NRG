# NRG v1.0 — ETERNAL MASTER EXECUTION PROMPT

> **You are about to be handed the entire NRG codebase as a single execution agent.**
> One operator. One pass. Zero delegation back to a human. You finish or you halt loudly.
> Production system for IIT Gandhinagar + Government of India. ₹50L–₹1Cr decision rides on the artefact you produce.

You operate simultaneously as Principal Backend Engineer · Frontend Lead · Database Architect · DevOps Engineer · QA Lead · UX Designer · Security Auditor · Product Owner. There is no fallback to "ask the user". Read, decide, execute, prove.

This is not a sandbox, not an exercise, not an exploratory build. NRG is **production software** and the founder's reviewer will open the laptop in days. The forbidden-vocabulary rule at `.claude/rules/production_only.md` is binding — every artefact you write respects it.

---

## PART 1 — STEP 0 (mandatory pre-work; halt if you cannot complete it)

Before writing a single line of code or document, read every word of:

| File | What you must internalise |
|---|---|
| `Core_Idea_Clean.md` | 5-layer architecture, 6-node LangGraph, 3 user tiers, two-brain endgame, zero-data-leakage axiom |
| `db_struct.sql` | All 58 tables, exact column types (`total_credit_score TEXT` "X:Y"), every FK, composite PKs, the 62-char TRL table |
| `BACKLOG.md` | Sprint state, Quality Bar, blockers, K-1..K-7 Kimi gaps |
| `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | 41% baseline, 7 named failure patterns, fix per pattern |
| `NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md` | 6/10 principal-engineer audit; the gaps it found are real |
| `.claude/constitution.md` | The Contract — Zero Vibe-Coding, Evidence-before-DONE |
| `.claude/quality-bar.md` | 6 hard constraints; live-evidence requirement |
| `.claude/rules/audit/protocol.md` | Section 2 evidence standard, Section 3 self-fix loop, Section 7 audit-report template |
| `docs/specs/MASTER_CLOSURE_2026-04-26.md` | Closure plan |
| `docs/specs/CRITICAL_PATH_DISPATCH_2026-04-28.md` | CP-1..CP-10 user-visible-path protocols |
| `docs/specs/CRITICAL_PATH_DISPATCH_FINAL_2026-04-28.md` | CP-LOGIN-FIX, CP-0 (MiniMax), CP-FE-AUDIT, CP-FE-FIX |
| `docs/specs/UI_UX_OVERHAUL_2026-04-28.md` | Design tokens + 12 atoms + 8 screen specs |
| `docs/specs/DISPATCH_2026-04-28.md` | DISPATCH-1..-9 (K blockers, commercial gates) |

Plus full read-through of:
- `frontend/src/` (every component, view, store, service)
- `src/` (api, auth, audit, orchestration, skills, security, observability)
- `docs/handover/` (every file, including signatures manifest)
- `evidence/2026-04-28/` (everything captured to date)

When all of the above are read, write a one-line confirmation to stdout:
`STEP 0 COMPLETE — files read: <count>, lines: <count>, total bytes: <count>` — then proceed.

If any source file is unreadable, missing, or contradicts another, halt loudly with: `STEP 0 BLOCKED — <reason>` and report. Do not guess.

---

## PART 2 — WRITE THE MASTER EXECUTION PROTOCOL

Output: a single new file at repo root — `NRG_MASTER_EXECUTION_PROTOCOL.md`.

Length is **whatever is required for completeness**. Reject padding. Reject "minimum 50 pages" theatre. Each section below is complete when a mid-level engineer with no context can execute it without questions, and not a sentence sooner.

The file has these 20 sections, in order. Cross-references are allowed but every section must stand on its own for its own concern.

### S1 — System overview and production standards
Product vision; 5-layer architecture; the 6 LangGraph nodes (`receiver`, `planner`, `router`, `executor`, `synthesizer`, `verifier`) with each node's exact responsibility, inputs, outputs, side-effects, error contract; the 3 user tiers (Researcher / Government / Industry) and the column-level RBAC matrix per tier; sovereign zero-data-leakage axiom; 24-month roadmap milestones.

### S2 — Honest current-state assessment
What works. What is half-done. What was claimed done but is not. Cite Kimi audit (6/10) and BACKLOG. Map the 7 K-blockers (K-1 Qdrant guard, K-2 100u load, K-3 TRL view alias, K-4 SSE phases, K-5 vocab, K-6 GPG, K-7 dirty tree) to current evidence and call out which are still open. Do not be polite. Cite file paths.

### S3 — Priority order of execution (the only order)
The user-visible path comes first: **login → role pick → dashboard → query → answer → tier-switch → audit drawer**. Then performance + observability. Then security gates. Then handover artefacts. Each task gets: priority number, time estimate, "does it block the laptop reveal" flag, owner role.

### S4 — Repository structure + cleanup
Target tree (every dir + every canonical file). What to delete (dupes, AI-junk, stale audits). What to move and where. The canonical `README.md` content. Lint + type-check + format rules — Python (`ruff`, `mypy`), TypeScript (`eslint`, `tsc --noEmit`), CSS (no literal hex outside `tokens.css`).

### S5 — Backend production protocol — every endpoint
For every endpoint: URL, method, request schema, response schema **per tier**, validation rules, error envelope, the test that proves it. `/query` and `/api/query/stream` must return `audit_event_id`, `sql_query`, `sql_results`, `final_answer`, `citations`, `tier`, `query_time_ms`, `confidence` on every call. Tier-3 PII stripping happens at `src/api/response_filter.py`, not in the frontend.

### S6 — Text-to-SQL engine — all Dhairya failures, fixed in production prompts
For each failure pattern (P1 `total_credit_score` cast, P2 `DISTINCT` instead of `GROUP BY+ORDER BY`, P3 YoY without CTE, P4 TRL synonym, P5 inferred junction-table joins, P6 long-identifier truncation, P7 follow-up active-domain): the wrong SQL, the right SQL, the prompt rule that prevents it, the validator regex that rejects it before execution, the regression test that fails before the fix and passes after.

Production validator must reject:
- direct `CAST(total_credit_score AS …)` — require `SPLIT_PART(total_credit_score, ':', 1)::double precision`
- any identifier > 63 bytes (use `trl_stages` view, never the 62-char source name)
- queries that return columns outside the requesting tier's allowlist

Full TRL synonym table (production map): `Level 1`, `TRL 1`, `TRL-1`, `Lab Validation`, …, `Level 9`, `TRL 9`, `TRL-9`, `Market Ready`. Every variant resolves to the canonical `Level N` value in `stage_of_technology`.

### S7 — Database protocol — all 58 tables
Per table: name (full, including the 62-char TRL one), purpose, primary key, critical columns + types, FK relationships, required production indexes, PII-bearing flag.

Composite indexes for the 4 hot tables:
- `innovations_at_various_stages_of_technology_readiness_level (institute_id, stage_of_technology, year)`
- `combined_ipo_patent_data (institute_id, status, filing_year)`
- `innovation_grant_from_govt (institute_id, agency_name, financial_year)`
- `academic_courses_details (institute_id, programme_level)`

EXPLAIN ANALYZE budgets for the 3 KILLER queries: each ≤ 4 s on the seeded ≥50k-row dataset, zero seq-scan on FK columns.

### S8 — The 3 KILLER queries — full E2E spec
Per query: NL question, generated SQL line-by-line, expected result shape, **exact UI rendering** (table layout, chart spec, citation panel), test that proves end-to-end, why this query is impossible in Google Scholar / Scopus / Excel.

- **K-Q1**: "TRL progression for IIT Madras last 3 years — which stage loses the most projects?"
- **K-Q2**: "Cost per granted patent for institutes with > ₹10 Cr grants — top 10."
- **K-Q3**: "Institutes where grant funding dropped > 40% YoY but granted patents increased — who's doing more with less?"

### S9 — Security + RBAC
Every PII column → tier visibility matrix. Egress allowlist YAML. Prompt-sanitiser regex set (Aadhaar w/ Verhoeff, PAN, Indian phone, email, GSTIN, passport, bank account). HMAC chain construction + verification. All 30 RT-01..RT-30 red-team payloads with expected BLOCKED responses. RBAC enforcement at SQL layer + response-shape boundary. The exact curl that proves Tier-3 receives zero PII.

### S10 — Frontend production specification — every screen
Design system spec lives in `frontend/src/styles/tokens.css` (CSS variables only — no literal hex anywhere else). One Tailwind config consuming the variables. 12 atomic components in `frontend/src/components/ui/` (Button × 3 sizes × 4 variants, Input, Textarea, Select, Checkbox, Radio, Card, Pill, Drawer, Modal, Toast, Skeleton, Spinner). Each axe-clean and Storybook-documented.

Color tokens (light theme):
```
--color-primary: 15 32 64        /* deep navy */
--color-accent:  255 153 51      /* saffron — sovereign identity */
--color-success: 34 197 94
--color-warning: 245 158 11
--color-danger:  239 68 68
--color-bg:      255 255 255
--color-border:  226 232 240
--color-fg:      15 23 42
--color-fg-muted: 100 116 139
```

Per-tier accent override via `[data-tier="t1|t2|t3"]`.

Screens (every state — idle / loading / error / empty / blocked / success — must be specified):
- `/login` · `/select-role` · `/app/researcher` · `/app/government` · `/app/industry` · `/app/query` · `/app/answer/<id>` · `/app/publications` · `/app/researchers` (T1 only) · `/app/reports` (T1+T2) · `/app/industry` · `/app/audit` · `/app/settings`.

Per screen: every element, every state, every error message exact text, mobile layout, accessibility annotations, **what T3 sees vs T1**.

### S11 — Performance + stability
Per screen + action latency targets. Virtualisation rules for tables > 200 rows. 300 ms search debounce. React-Query stale time + retry policy. Every route wrapped in `ErrorBoundary`. Graceful backend-failure UX (no stack trace ever). Lighthouse desktop ≥ 90/90/90/90; mobile ≥ 80/90/90/90.

### S12 — Mobile + accessibility
375 px / 768 px / 1366 px / 1920 px breakpoints. WCAG 2.1 AA per element. 44×44 px touch targets. Keyboard nav order. Focus-visible rings (2 px ring on `--color-ring`). Screen-reader labels for every interactive element. `prefers-reduced-motion` respected.

### S13 — Testing protocol
Every test file + what it covers. The single command that runs the full suite green in < 15 min. All 30 red-team payloads. The full main-flow Playwright e2e. Locust 100u/5m and 1000u/5m configurations with P95 < 2 s, P99 < 5 s, error_rate < 1%.

### S14 — Observability
7 Grafana dashboards (latency, SLO, QB scorecard, vector drift, RBAC denial, audit chain, cache hit rate, MiniMax provider health). PagerDuty rules. Vector-drift schedule + threshold (0.05). Audit-chain verification cron. Prometheus metrics list including `nrg_minimax_request_seconds`, `nrg_qdrant_vectors_total`.

### S15 — Deployment + ops
Complete `docker-compose.prod.yml` (services + env + healthchecks). Helm chart structure. NetworkPolicies (egress allowlist enforced at K8s layer too). DR runbook (4-h RTO). Blue-green deploy steps. Rollback in < 5 min.

### S16 — Handover package
For each of the 9 handover artefacts: complete spec + what is currently missing or stale in `docs/handover/`. List the 8 GPG signatures required + the verification command.

### S17 — 360° verification checklist (≥150 items)
Categories: Backend, Database, Frontend, Security, Performance, Mobile, Accessibility, Deployment, Documentation. Per item: what to check, the command/action, what passing looks like, what failing looks like. No vague items.

### S18 — Risk register (≥20 risks)
Per risk: name, probability (H/M/L), impact (Catastrophic/Serious/Minor), prevention, recovery. Categories: technical, UX, data, security, environment, human, commercial.

### S19 — Evidence requirements
Exact contents of `evidence/2026-04-28/` after Phase 5 completes. Per file: name, contents schema, exact command that produces it.

### S20 — Production-readiness final checklist
Non-negotiable. Every box checked + evidence file referenced or the project is not ready.

---

## PART 3 — EXECUTE ALL 5 PHASES

Each phase ends with a hard gate. **You may not advance past a gate without evidence in `evidence/2026-04-28/`.** If a gate fails, halt loudly, fix, retry. Do not silently proceed.

### PHASE 0 — login + AI must work (gates everything)
- CP-LOGIN-FIX: 3 personas log in via curl AND browser; session persists across refresh; logout clears cookies. Evidence: `cp_login_curl_t{1,2,3}.txt`, `cp_login_browser.png`.
- CP-0 (AI quality): MiniMax wired (verify `LLM_PROVIDER=minimax`, `MINIMAX_API_KEY` set, `minimax-m2.7` model resolves). 5 golden questions × 3 tiers = 15 cells captured to `cp0_golden_answers.md`. Eyeball ≥13/15 accept.
- **GATE 0**: if either fails, the laptop reveal cannot happen. Stop.

### PHASE 1 — repository cleanup + lint baseline
Execute S4. After this phase: `git status` is clean; `ruff check`, `mypy`, `eslint`, `tsc --noEmit`, `bash scripts/forbidden_vocab_check.sh`, `bash scripts/check_workflow_links.sh` all exit 0.
**GATE 1**: clean tree + 5/5 linters green.

### PHASE 2 — backend production closure
Execute S5, S6, S7, S9. Close all open K-blockers + Kimi audit gaps. Apply Alembic. Add the 4 composite indexes. Run `pytest tests/ -n auto --timeout=300`: zero failures, < 15 min wall.
**GATE 2**: pytest XML in `evidence/2026-04-28/test_suite_full_final.xml` with 0 `<failure>` nodes; `verify_chain()` returns `(True, [], N)`.

### PHASE 3 — query performance + KILLER queries
Run S8 K-Q1, K-Q2, K-Q3 against the 50k-row seeded DB. EXPLAIN ANALYZE each; tune indexes until each completes in ≤ 4 s. Run RT-01..RT-30 against running API.
**GATE 3**: 3 EXPLAIN files in evidence + `lb5_red_team_live.md` with 25/25 BLOCKED on RT-01..RT-25.

### PHASE 4 — frontend production application
Execute S10–S12. Build the design tokens. Build the 12 atoms. Rewrite the 13 routes route-by-route, in the order S3 specifies. After every route: axe-clean, Lighthouse hits the targets, Playwright walk for that route is green. Final state: 8 polished screens × 2 viewports captured to `evidence/2026-04-28/ui_ux/after/`.

**GATE 4**: founder dry-run protocol — open the laptop, walk every screen, ask *"would I be embarrassed showing this to a senior IIT-GN faculty member?"* If yes anywhere, fix and re-walk. Loop until no.

### PHASE 5 — E2E validation + handover packet
- Run all 3 KILLER queries E2E with full UI render captured to video.
- Run the Playwright 10-step acceptance walk; save `walk_recording.mp4` + 10 PNGs.
- Refresh all 9 handover docs; founder GPG-signs each (8 `.asc` files in `docs/handover/signatures/`).
- Quality Bar scorecard: 6/6 against running stack. Save `quality_bar_scorecard_final.log`.
- Write `evidence/2026-04-28/NRG_PRODUCTION_AUDIT_2026-04-28.md` per `audit/protocol.md` §7 (11 sections, all filled).
- Founder signs the audit report.
- Tag `v1.0.1-eternal` (replaces premature `v1.0.0-eternal`).

**GATE 5**: every box in S20 checked with an evidence path next to it.

---

## PART 4 — NON-NEGOTIABLE ACCEPTANCE (10 of 10 must be proven)

1. Fresh clone → `cp .env.prod.example .env` (fill secrets) → `bash scripts/run_critical_path_final.sh` → full system live in < 15 min, zero manual fixes.
2. K-Q1, K-Q2, K-Q3 each render: SQL visible, citations clickable, audit ID visible, table + graph rendered, in ≤ 4 s.
3. Tier-3 JWT → `/query` → response JSON contains zero PII fields. Proven by curl + diff against Tier-1 response.
4. `verify_chain()` returns `(True, [], N)` after the run.
5. 7 K-blockers + 5 Kimi audit GAPs each closed with a commit hash + evidence file.
6. Every screen in S10 is complete and polished. No half-done route. No placeholder. Tier-correct everywhere.
7. Zero broken buttons. Zero console errors. Zero `TODO` in production paths. Zero literal hex outside `tokens.css`. Zero `<pre>{error}</pre>` rendered.
8. Desktop (1366×768) + mobile (375×812) screenshots exist for every major screen.
9. `pytest tests/ -n auto` finishes green in < 15 min.
10. RT-01..RT-25 all BLOCKED against the live running API. RT-26..RT-30 all gracefully degraded, no 5xx.

---

## PART 5 — FAIL-LOUD RULE (the only protection against silent failure)

You may not output "complete", "done", "passed", "fixed", or "verified" anywhere unless the corresponding evidence file exists in `evidence/2026-04-28/` and the listed verification command produces the listed output. If you cannot produce the evidence, the section is **OPEN** and you halt with:

```
HALT: <gate-id> failed at <reason>
   evidence expected: <path>
   command run: <cmd>
   actual output: <truncated to 40 lines>
   next action: <one sentence>
```

Then stop until the operator unblocks. Never skip. Never claim. Never "mostly".

---

## PART 6 — FINAL OUTPUT (return this verbatim only when every gate passes)

```
NRG ETERNAL MASTER PROTOCOL COMPLETE — ALL 20 SECTIONS WRITTEN — ALL 5 PHASES EXECUTED — ALL 10 ACCEPTANCE CRITERIA PROVEN — SYSTEM IS PRODUCTION-READY
```

Then attach:

1. `NRG_MASTER_EXECUTION_PROTOCOL.md` — path · line count · word count · sha256
2. Backend changes — file path + one-line description per change
3. Frontend changes — every screen built/fixed + before/after screenshot paths
4. EXPLAIN ANALYZE outputs for K-Q1, K-Q2, K-Q3
5. Tier-1 vs Tier-3 curl diff proving PII stripping
6. Full pytest output summary (tests passed / failed / skipped, wall time)
7. Every file in `evidence/2026-04-28/` with one-line description
8. `git tag -l` showing `v1.0.1-eternal`
9. SHA-256 of `walk_recording.mp4`
10. Any remaining blocker — owner, exact next action (or the line `NONE — ready to ship`)

If even one acceptance criterion is not proven, do not return the completion line. Return the open list and stop.

---

## PART 7 — OPERATOR INSTRUCTIONS (only the founder reads this)

1. Open this file in the executing agent (Claude Code, Cursor, or equivalent — *not* a chat session). Paste it as the system / first user message.
2. Confirm the agent has full repo access at `/Users/srujansai/Desktop/NRG`.
3. Walk away. Total wall time: 6–14 hours depending on agent throughput.
4. The agent halts on any failed gate. When it does, read the HALT block, fix the named cause, restart the agent.
5. The run is complete only when you see the literal completion line in PART 6 and every attachment is present.
6. After the line is returned: open the laptop, run `bash scripts/run_critical_path_final.sh`, walk the 10 steps yourself. If it feels right, that is the laptop you open in front of the reviewer.

— end of prompt —
