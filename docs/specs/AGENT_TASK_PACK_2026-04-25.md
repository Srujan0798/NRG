# [SUPERSEDED — FRAMING REPLACED]

> **The engineering tasks (T01–T19) below are still valid as work items**, but the "demo" framing is voided.
> **Use instead:** `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md` §3 milestones M5a.1–M5a.15 (frontend production hardening).
> **Reason:** NRG is production software for IIT Gandhinagar + Gov of India ministries. See `.claude/rules/production_only.md`.
> The same engineering effort is now framed as production hardening for real users, not a demo on a founder's laptop.

---

# NRG — AGENT TASK PACK (HISTORICAL — engineering items only)
**Date:** 2026-04-25
**Scope:** Make the web app extraordinary on the founder's laptop. Period.
**Demo target:** Professor's assistant opens the laptop browser, sees a working sovereign-grade product, signs off.
**Out of scope:** Pitch decks. Vendor selection. Cluster ops. NDA. UAT scheduling. K8s. 600GB ingest. GPG ceremony. Anything that isn't code or evidence on this laptop.
**Hand-off rule:** Every task below is ready to copy-paste to an agent. Don't paraphrase. Don't summarize. Don't "make it good." Use the exact briefing format.

---

## THE BRIEFING FORMAT (use verbatim for every agent task)

```
AGENT: [name]
TASK ID: [TID]
SPEC: [exact file path + section number]
ACCEPTANCE: [reference to spec acceptance gate row]
FILES YOU MAY TOUCH: [exact paths only]
FILES YOU MAY NOT TOUCH: [exclusions]
TESTS REQUIRED: [exact test path + what it must cover]
SHOW BEFORE COMMIT: git diff + test output + screenshot if visual
DONE WHEN: [binary criteria]
TIME BUDGET: [hours]
DEPENDENCIES: [TIDs that must finish first]
```

---

## TASK ORDER (dependency-respecting)

```
Day 1  ─ T01 (cleanup) → T02 (design tokens audit) → T03 (typography wiring)
Day 2  ─ T04 (search bar hero) ──┐
                                  ├─→ T05 (streaming UX 4 phases)
Day 3  ─ T06 (persona toggle) ───┘
Day 4  ─ T07 (citation drawer)  → T08 (audit panel)
Day 5  ─ T09 (3 dashboards polish)
Day 6  ─ T10 (empty/error states) + T11 (microcopy + forbidden grep)
Day 7  ─ T12 (a11y AA pass) + T13 (mobile 375px) + T14 (telemetry)
Day 8  ─ T15 (Storybook + visual regression CI)
Day 9  ─ T16 (demo dataset seed) + T17 (live evidence regen)
Day 10 ─ T18 (E2E demo rehearsal recording) → T19 (tag rc1)
```

10 working days. 6 agents. Run in parallel where the dependency graph allows.

---

## T01 — CLEANUP DUPLICATE COMPONENT FILES

```
AGENT: Vulcan-Perf
TASK ID: T01
SPEC: docs/specs/FRONTEND_UX_MASTER_SPEC_2026-04-25.md §19
ACCEPTANCE: §23 row "Cleanup §19 done; no duplicate component files"
FILES YOU MAY TOUCH:
  frontend/src/components/AnswerPanel.tsx (delete)
  frontend/src/components/SkeletonLoader.tsx (delete)
  frontend/src/components/CitationDrawer.tsx (delete)
  frontend/src/components/ErrorBoundary.tsx (merge into ErrorBoundary/)
  frontend/src/components/WidgetErrorBoundary.tsx (merge)
  frontend/src/views/GovernmentView.tsx (delete, route → Dashboard)
  frontend/src/views/IndustryView.tsx (delete, route → Dashboard)
  frontend/src/views/ResearcherView.tsx (delete, route → Dashboard)
  frontend/src/__test__graph.tsx (move to __tests__/)
  frontend/src/TestApp.tsx (move to __tests__/)
  Any import that referenced the old paths
FILES YOU MAY NOT TOUCH: src/api, src/audit, src/security, alembic/
TESTS REQUIRED:
  - All existing frontend tests still pass
  - Add eslint rule: no two files with the same basename under components/
SHOW BEFORE COMMIT: git diff + npm test output + npm run build (must succeed)
DONE WHEN:
  - Zero duplicate component basenames
  - All imports resolve
  - All tests green
TIME BUDGET: 2h
DEPENDENCIES: none
```

---

## T02 — DESIGN TOKEN AUDIT (no raw hex / px in components)

```
AGENT: Vulcan-Perf
TASK ID: T02
SPEC: §2 (full visual design system)
ACCEPTANCE: zero raw hex colors and zero raw px values inside components/ and views/; everything routes through design-system/tokens/
FILES YOU MAY TOUCH:
  frontend/src/design-system/tokens/colors.ts (extend with §2.1 table)
  frontend/src/design-system/tokens/typography.ts (extend with §2.2 scale)
  frontend/src/design-system/tokens/spacing.ts (extend with §2.3 scale)
  frontend/src/design-system/theme.ts
  frontend/src/index.css (CSS custom properties for all tokens)
  Every file under components/ and views/ that uses raw values → swap to token reference
FILES YOU MAY NOT TOUCH: business logic
TESTS REQUIRED:
  - frontend/tests/design-system/no_raw_values.test.ts (new) — fails build if any component uses /#[0-9a-fA-F]{3,8}/ or /\d+px/ outside design-system/
  - Existing tests still pass
SHOW BEFORE COMMIT: a grep report of remaining raw values (must be 0) + lighthouse contrast audit
DONE WHEN: every color and every spacing value is a token; build passes
TIME BUDGET: 4h
DEPENDENCIES: T01
```

---

## T03 — TYPOGRAPHY + FONT LOADING

```
AGENT: Vulcan-Perf
TASK ID: T03
SPEC: §2.2, §4.5 (font preload)
ACCEPTANCE: Söhne Display + JetBrains Mono preloaded; FOIT/FOUT < 100ms; CLS < 0.05
FILES YOU MAY TOUCH:
  frontend/index.html (preload tags)
  frontend/src/design-system/tokens/typography.ts
  frontend/src/index.css (font-face + font-display: swap)
  frontend/public/fonts/* (add WOFF2 self-hosted; do NOT use Google Fonts CDN — sovereignty)
TESTS REQUIRED:
  - Lighthouse mobile + desktop CLS < 0.05
  - No external font CDN requests (verify with network panel + a snapshot test)
SHOW BEFORE COMMIT: Lighthouse JSON + network HAR
DONE WHEN: fonts self-hosted, preloaded, no layout shift
TIME BUDGET: 2h
DEPENDENCIES: T02
```

---

## T04 — HERO QUERY SCREEN (search bar + suggestion chips + scale strip)

```
AGENT: Hermes-UI
TASK ID: T04
SPEC: §4 (full)
ACCEPTANCE: §23 — TTI < 1500ms, search bar autofocused, 4 suggestion chips, animated scale counters
FILES YOU MAY TOUCH:
  frontend/src/views/Hero.tsx (new)
  frontend/src/components/SearchBar.tsx (elevate per §4.2)
  frontend/src/components/SuggestionChips/SuggestionChips.tsx (new)
  frontend/src/components/ScaleStrip/ScaleStrip.tsx (new)
  frontend/src/hooks/useAnimatedCounter.ts (already exists — wire it)
  frontend/src/i18n/en-IN.ts (new — placeholder rotation strings per §15.1)
  frontend/src/App.tsx (route /app → Hero)
TESTS REQUIRED:
  - frontend/tests/e2e/hero_first_paint.spec.ts (new):
      asserts FCP < 800ms, search bar focused, 4 chips visible, counters animate
  - frontend/tests/components/SearchBar.test.tsx — Enter submits, Shift+Enter newline,
      ⌘K refocuses, placeholder rotates every 4s
  - frontend/tests/components/SuggestionChips.test.tsx — click fills SearchBar + auto-submits at 200ms
SHOW BEFORE COMMIT: screenshot at desktop + mobile + Lighthouse mobile run
DONE WHEN: hero screen is the demo's first impression and lands in <1.5s
TIME BUDGET: 8h
DEPENDENCIES: T02, T03
```

---

## T05 — STREAMING ANSWER UX (the demo killer)

```
AGENT: Apollo-Polish
TASK ID: T05
SPEC: §5 (full — 4 phases with exact transitions)
ACCEPTANCE: §23 — visible feedback < 200ms after submit; 4 phases visible; verified badge animates
FILES YOU MAY TOUCH:
  frontend/src/hooks/useStreamingQuery.ts (already exists — wire to /query/stream SSE)
  frontend/src/components/StreamingAnswerPanel.tsx (rewrite per §5)
  frontend/src/components/PhaseHeader/PhaseHeader.tsx (new)
  frontend/src/components/SqlBlock/SqlBlock.tsx (new — syntax highlight + copy button)
  frontend/src/components/TokenStream/TokenStream.tsx (new — char-by-char render with blinking cursor)
  frontend/src/components/VerifiedBadge/VerifiedBadge.tsx (new — green pulse + click for proof)
  frontend/src/types/api.ts (add SSE event types per §13.1)
  frontend/src/stores/queryStore.ts (extend per §14.1)
TESTS REQUIRED:
  - frontend/tests/e2e/streaming_answer.spec.ts (new) per §5.4
  - frontend/tests/hooks/useStreamingQuery.test.ts — abort signal works, heartbeat handled, 25s silence triggers recoverable error
  - Mock SSE server in tests/mocks/sse_server.ts
SHOW BEFORE COMMIT: screen recording of full 4-phase render + e2e log
DONE WHEN: pressing Enter never shows a blank spinner > 200ms; 4 phases stream end-to-end
TIME BUDGET: 12h
DEPENDENCIES: T04
```

---

## T06 — PERSONA TOGGLE + SIDE-BY-SIDE REVEAL

```
AGENT: Hermes-UI
TASK ID: T06
SPEC: §6 (full)
ACCEPTANCE: §23 — persona toggle works, side-by-side comparison reveals real diff, "What changed?" annotation appears
FILES YOU MAY TOUCH:
  frontend/src/components/PersonaToggle/PersonaToggle.tsx (new)
  frontend/src/components/Layout.tsx (mount toggle top-right)
  frontend/src/services/authService.ts (add switchPersona() per §13.3)
  frontend/src/stores/queryStore.ts (add switchPersona action per §14.1)
  frontend/src/components/SideBySidePanel/SideBySidePanel.tsx (new — 2-column at lg, stacked at xs)
  frontend/src/components/WhatChangedAnnotation/WhatChangedAnnotation.tsx (new with §6.3 hardcoded copy)
TESTS REQUIRED:
  - frontend/tests/e2e/persona_toggle.spec.ts (new):
      Tab/Enter navigates segments, ARIA tablist correct, switch re-runs last query,
      side-by-side renders within 240ms of new answer arriving
  - frontend/tests/components/PersonaToggle.test.tsx — keyboard nav, aria-selected
SHOW BEFORE COMMIT: screen recording of persona switch end-to-end including the "What changed?" panel
DONE WHEN: persona toggle is the visible differentiation moment of the demo
TIME BUDGET: 6h
DEPENDENCIES: T04, T05
```

---

## T07 — CITATION DRAWER WITH HMAC PROOF

```
AGENT: Apollo-Polish
TASK ID: T07
SPEC: §7 (full — drawer structure with HMAC proof panel)
ACCEPTANCE: §23 — drawer opens in <240ms; verify-on-chain in <500ms
FILES YOU MAY TOUCH:
  frontend/src/components/CitationDrawer/CitationDrawer.tsx (rewrite per §7.3)
  frontend/src/components/CitationLink.tsx (elevate per §7.2)
  frontend/src/components/HmacProof/HmacProof.tsx (new — chain prev/curr/next viz)
  frontend/src/utils/parseCitations.ts (already exists — extend for [cite:pub:chunk])
  frontend/src/services/queryService.ts (add getAuditEvent + verifyAuditEvent)
TESTS REQUIRED:
  - frontend/tests/e2e/citation_drawer.spec.ts:
      click chip → drawer < 240ms; verify button → green badge < 500ms; ESC closes
  - frontend/tests/utils/parseCitations.test.ts (already exists — extend coverage)
SHOW BEFORE COMMIT: screen recording of click → drawer → verify badge transition
DONE WHEN: every citation chip leads to a 30-second proof story
TIME BUDGET: 6h
DEPENDENCIES: T05
```

---

## T08 — AUDIT PANEL (`/app/audit`)

```
AGENT: Apollo-Polish
TASK ID: T08
SPEC: §17 (full)
ACCEPTANCE: virtualized event list; drawer opens on row click; chain neighborhood at /app/audit/event/{hmac}
FILES YOU MAY TOUCH:
  frontend/src/pages/DPDP-Audit.tsx (rewrite per §17.1)
  frontend/src/pages/AuditEvent.tsx (new — single event view)
  frontend/src/components/AuditEventList/AuditEventList.tsx (new — react-window virtualized)
  frontend/src/components/ChainIntegrityFooter/ChainIntegrityFooter.tsx (new)
  frontend/src/services/queryService.ts (extend for /audit/list, /audit/event/{id})
TESTS REQUIRED:
  - frontend/tests/e2e/audit_panel.spec.ts: list virtualized, row click → drawer, /event/:id renders
SHOW BEFORE COMMIT: screen recording of "show me proof" 30-second sequence per §17.2
DONE WHEN: founder can rehearse the proof demo in 30s with no thinking
TIME BUDGET: 6h
DEPENDENCIES: T07
```

---

## T09 — 3 PERSONA DASHBOARDS POLISH

```
AGENT: Hermes-UI
TASK ID: T09
SPEC: §10 (full — 3 dashboards with named cards)
ACCEPTANCE: each dashboard renders the cards listed in §10.1/10.2/10.3 with real data
FILES YOU MAY TOUCH:
  frontend/src/views/ResearcherDashboard.tsx (elevate per §10.1)
  frontend/src/views/GovernmentDashboard.tsx (elevate per §10.2)
  frontend/src/views/IndustryDashboard.tsx (elevate per §10.3)
  frontend/src/components/StatsCard/StatsCard.tsx (already exists — extend with sparkline)
  frontend/src/components/DataViz/* (already exists — wire IndiaMapChoropleth, BarChart, etc.)
  frontend/src/components/Researcher/* (new — MyImpact, OpenFunding, Collaborators, ResearchPulse)
  frontend/src/components/Government/* (already exists — extend with TRLProgression sankey)
  frontend/src/components/Industry/* (already exists — extend with PatentSurge bar)
TESTS REQUIRED:
  - frontend/tests/e2e/dashboards.spec.ts: each persona dashboard renders all cards with valid data
SHOW BEFORE COMMIT: 3 screenshots (one per persona)
DONE WHEN: switching personas reveals 3 visually distinct, fully-populated dashboards
TIME BUDGET: 8h
DEPENDENCIES: T06
```

---

## T10 — ALL 6 EMPTY STATES + 3 ERROR TIERS

```
AGENT: Athena-UX
TASK ID: T10
SPEC: §8 (empty), §9 (error)
ACCEPTANCE: §23 — all 6 empty + 3 error tiers; no <pre>/Error:/Traceback in any error route
FILES YOU MAY TOUCH:
  frontend/src/components/EmptyState/EmptyState.tsx (new)
  frontend/src/components/ErrorState/ErrorState.tsx (already exists — extend per §9.2)
  frontend/src/components/PromptBlocked/PromptBlocked.tsx (new — sanitiser block UI per §18.1)
  frontend/src/i18n/en-IN.ts (all empty/error copy per §8.1, §15.4)
  All caller sites that previously rendered "0 rows" or stack traces
TESTS REQUIRED:
  - frontend/tests/e2e/no_stack_trace.spec.ts (new) per §9.3 — sacred test
  - frontend/tests/components/EmptyState.test.tsx — every cause renders correct headline + CTA
  - frontend/tests/components/ErrorState.test.tsx — 3 tiers each render with traceId hidden
SHOW BEFORE COMMIT: 6 empty + 3 error screenshots
DONE WHEN: every zero-state has a CTA; every error has a face; build fails if any forbidden phrase appears
TIME BUDGET: 6h
DEPENDENCIES: T05
```

---

## T11 — MICROCOPY LIBRARY + FORBIDDEN-PHRASE BUILD GREP

```
AGENT: Athena-UX
TASK ID: T11
SPEC: §15 (microcopy)
ACCEPTANCE: every visible string sourced from i18n/en-IN.ts; CI fails on forbidden phrases
FILES YOU MAY TOUCH:
  frontend/src/i18n/en-IN.ts (full library)
  frontend/src/i18n/index.ts (loader)
  frontend/scripts/forbidden_phrases.sh (new — greps build artifacts for §15.5 phrases)
  All components that hold raw user-visible strings → migrate to i18n
TESTS REQUIRED:
  - frontend/tests/i18n/no_raw_strings.test.ts — fails if any JSX contains a hardcoded string > 3 chars (allowlist for icons / dev tooling)
  - CI step: npm run forbidden-grep (must exit 0)
SHOW BEFORE COMMIT: forbidden_phrases.sh exit 0 + i18n keys count
DONE WHEN: every word the professor sees is in en-IN.ts and survives the forbidden-grep
TIME BUDGET: 2h
DEPENDENCIES: T10
```

---

## T12 — ACCESSIBILITY AA PASS

```
AGENT: Iris-A11y
TASK ID: T12
SPEC: §11 (WCAG AA)
ACCEPTANCE: §23 — axe 0 errors, ≤5 warnings per route
FILES YOU MAY TOUCH:
  frontend/src/components/SkipLink/SkipLink.tsx (new — first focusable on every page)
  frontend/src/hooks/useReducedMotion.ts (new)
  Every interactive component → focus ring + aria-label + keyboard nav
  frontend/index.html (lang="en-IN", title prefix)
TESTS REQUIRED:
  - frontend/tests/a11y/axe.test.ts (new — runs @axe-core/playwright on every route)
  - frontend/tests/a11y/contrast.test.ts (new — wcag-color check on token combos)
  - frontend/tests/a11y/keyboard.test.ts (new — tab-order assertions)
SHOW BEFORE COMMIT: axe report per route + reduced-motion screenshot test
DONE WHEN: zero a11y errors; a screen-reader walkthrough of /app is intelligible
TIME BUDGET: 4h
DEPENDENCIES: T05, T06, T07, T08, T09, T10
```

---

## T13 — MOBILE 375PX END-TO-END

```
AGENT: Iris-A11y
TASK ID: T13
SPEC: §12 (mobile)
ACCEPTANCE: §23 — full E2E on real iPhone at 393×852
FILES YOU MAY TOUCH:
  Every component with a responsive variant
  frontend/src/components/PersonaSheet/PersonaSheet.tsx (new — bottom-sheet replacement of toggle on xs)
  frontend/src/components/MobileGraphModal/MobileGraphModal.tsx (new — fullscreen ForceGraph replacement)
  frontend/tailwind.config.js (verify breakpoints match §3.2)
TESTS REQUIRED:
  - frontend/tests/e2e/mobile_full_flow.spec.ts (new — Playwright iPhone 15 viewport)
SHOW BEFORE COMMIT: real-device screen recording (founder's actual phone) saved to evidence/<date>/mobile_e2e.mp4
DONE WHEN: end-to-end killer query + citation drawer works on a real iPhone with no horizontal scroll
TIME BUDGET: 4h
DEPENDENCIES: T12
```

---

## T14 — TELEMETRY (10 EVENT TYPES)

```
AGENT: Vulcan-Perf
TASK ID: T14
SPEC: §21 (telemetry)
ACCEPTANCE: every interaction emits a structured event; batched POST every 10s; PII-stripped
FILES YOU MAY TOUCH:
  frontend/src/lib/telemetry.ts (new)
  frontend/src/lib/telemetryQueue.ts (new — batched flush)
  Every interactive component → emit on mount/click/error
  src/api/main.py — add /api/telemetry endpoint (lightweight ingest, audit-bound)
TESTS REQUIRED:
  - frontend/tests/lib/telemetry.test.ts — events shape + PII strip
  - frontend/tests/e2e/telemetry_flow.spec.ts — submit query → 5 events emitted in correct order
SHOW BEFORE COMMIT: /api/telemetry receives events; sample event log
DONE WHEN: UAT becomes measurable, not subjective
TIME BUDGET: 3h
DEPENDENCIES: T05, T06, T07, T10
```

---

## T15 — STORYBOOK + VISUAL REGRESSION CI

```
AGENT: Vulcan-Perf
TASK ID: T15
SPEC: §20 (Storybook)
ACCEPTANCE: §23 — Storybook published; 0 unapproved visual diffs
FILES YOU MAY TOUCH:
  frontend/.storybook/ (new — main.ts, preview.tsx, manager.ts)
  frontend/src/components/**/*.stories.tsx (new — one story per component, every state)
  frontend/.github/workflows/visual_regression.yml (new — Loki or Chromatic)
TESTS REQUIRED:
  - Loki snapshot tests for every story
  - CI: npm run storybook:build must succeed
SHOW BEFORE COMMIT: Storybook static site URL + snapshot diff report
DONE WHEN: every component variant has a story; CI fails on >0.1% pixel diff without approval
TIME BUDGET: 4h
DEPENDENCIES: T01–T13
```

---

## T16 — DEMO DATASET SEED (200+ realistic rows in 3 demo institutes)

```
AGENT: Cassandra-QA
TASK ID: T16
SPEC: prevent the empty-graph / sparse-result demo failure
ACCEPTANCE: 4 killer queries return visually credible result sets at demo time
FILES YOU MAY TOUCH:
  scripts/seed_demo_data.py (new — pyfaker-generated, deterministic seed)
  scripts/seed_data.json (new — fixture)
  tests/data/test_demo_seed.py (new — verifies row counts)
TESTS REQUIRED:
  - All 4 killer queries return >= 5 rows of credible-looking data
  - Q1 Top 5 funding agencies: returns 5 distinct agencies with realistic ₹ amounts
  - Q2 TRL progression: returns 8+ institutes with multiple TRL transitions
  - Q3 Solar seed → patents: returns 12+ researchers with computed median
  - Q4 IIT-B vs IIT-M AI/ML: returns multi-year totals visibly different
SHOW BEFORE COMMIT: each killer query result pasted as JSON
DONE WHEN: graph view looks populated, dashboards have credible numbers, no "0 rows" scenarios on rehearsal
TIME BUDGET: 4h
DEPENDENCIES: none
```

---

## T17 — LIVE EVIDENCE REGENERATION (RT replay + tier curls + EXPLAIN ANALYZE)

```
AGENT: Cassandra-QA
TASK ID: T17
SPEC: closes 3 honest gaps from yesterday's audit (empty 09/10/11 + 16 + 17 evidence files)
ACCEPTANCE: all 3 evidence files non-empty with real captured outputs
FILES YOU MAY TOUCH:
  scripts/regen_evidence.sh (new — boots API, runs all curls, saves outputs)
  evidence/<today>/09_tier1_query_response.json (regenerate)
  evidence/<today>/10_tier2_query_response.json (regenerate)
  evidence/<today>/11_tier3_query_response.json (regenerate)
  evidence/<today>/12_pii_block_response.json (regenerate)
  evidence/<today>/13_injection_block_response.json (regenerate)
  evidence/<today>/16_explain_analyze_top_funding.log (regenerate)
  evidence/<today>/17_red_team_results.md (regenerate via scripts/red_team_fast.py with per-row markdown)
TESTS REQUIRED:
  - regen_evidence.sh exits 0
  - 17_red_team_results.md has 30 rows with BLOCKED/ALLOWED column
  - 9/10/11 JSONs have visibly different column sets per tier
SHOW BEFORE COMMIT: ls -la evidence/<today>/ showing all files non-empty
DONE WHEN: every PASS in the audit report has a real evidence file behind it
TIME BUDGET: 3h
DEPENDENCIES: T16
```

---

## T18 — E2E DEMO REHEARSAL RECORDING (12-min walkthrough)

```
AGENT: Cassandra-QA
TASK ID: T18
SPEC: a single 12-min screen recording covering the full demo script
ACCEPTANCE: nothing breaks; every demo query renders correctly; persona switch + citation drawer + audit panel demonstrated
FILES YOU MAY TOUCH:
  docs/demo/DEMO_SCRIPT.md (new — exact 12-min script)
  evidence/<today>/demo_rehearsal.mp4 (new — screen recording)
TESTS REQUIRED:
  - Manual: agent runs the script end-to-end against the local stack, records, hands recording to founder for review
SHOW BEFORE COMMIT: the .mp4 + a transcript with timing
DONE WHEN: founder watches it once and says "this is the demo"
TIME BUDGET: 2h
DEPENDENCIES: T01–T17
```

---

## T19 — FINAL TAG + FOUNDER REVIEW

```
AGENT: (founder)
TASK ID: T19
ACCEPTANCE: every prior TID committed and merged; full acceptance gate §23 of master spec runs green
FILES YOU MAY TOUCH:
  BACKLOG.md (mark all TIDs done)
  Tag: git tag v0.9.0-rc1-demo-ready
TESTS REQUIRED:
  - npm run test (frontend)
  - PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=short (backend)
  - python scripts/quality_bar_scorecard.py — must show 5/6 minimum
  - npm run lighthouse:mobile — score >= 95
SHOW BEFORE COMMIT: scorecard JSON + lighthouse JSON + e2e summary
DONE WHEN: tagged, ready for demo, you can demo on your laptop without thinking
TIME BUDGET: 1h
DEPENDENCIES: T01–T18
```

---

## ACCEPTANCE GATE (THE ONE GATE THAT MATTERS)

Repeat of master spec §23 — all 17 must be ☑ or you do not demo:

```
☐ Lighthouse mobile score ≥ 95
☐ Lighthouse desktop score ≥ 98
☐ axe-core: 0 errors, ≤ 5 warnings per route
☐ FCP < 800ms on slow 3G; TTI < 1500ms
☐ Streaming UX: visible feedback < 200ms after submit
☐ All 6 empty states implemented with copy + CTA
☐ All 3 error tiers implemented; no <pre> in any error route
☐ Persona toggle works; side-by-side comparison reveals real diff
☐ CitationDrawer opens in <240ms; verify-on-chain in <500ms
☐ Mobile (393px) end-to-end tested on real iPhone
☐ Reduced-motion respected
☐ All forbidden phrases (§15.5) absent from build
☐ Telemetry events firing for every interaction
☐ 4 killer queries cached and rehearsed
☐ Storybook published; 0 unapproved visual diffs
☐ Cleanup §19 done; no duplicate component files
☐ Demo-day checklist (master spec §22) complete
```

---

## TOTAL EFFORT

| Track | Hours | Days (6 agents parallel) |
|---|---|---|
| Component cleanup + tokens (T01–T03) | 8 | 1 |
| Hero + streaming + persona (T04–T06) | 26 | 3 |
| Citations + audit panel + dashboards (T07–T09) | 20 | 2 |
| Empty/error/microcopy (T10–T11) | 8 | 1 |
| A11y + mobile + telemetry (T12–T14) | 11 | 1 |
| Storybook + dataset + evidence + rehearsal (T15–T18) | 13 | 2 |
| Founder review + tag (T19) | 1 | 0 |
| **Total** | **~87 agent-hours** | **~10 working days** |

---

## THE FOUNDER'S 8 MESSAGES (between now and demo)

You ask me exactly these 8 things, in order, no others:

1. **End of Day 1:** "T01–T03 done in commits X,Y,Z. Review."
2. **End of Day 3:** "T04–T06 done. Review streaming UX + persona toggle."
3. **End of Day 4:** "T07 + T08 done. Review citation drawer + audit panel — time the 30-second proof demo."
4. **End of Day 5:** "T09 done. Review 3 dashboards across personas."
5. **End of Day 6:** "T10 + T11 done. Confirm forbidden-grep is green."
6. **End of Day 7:** "T12 + T13 + T14 done. Confirm a11y + mobile + telemetry."
7. **End of Day 8:** "T15 + T16 done. Confirm Storybook + demo dataset."
8. **End of Day 10:** "T17 + T18 done. Watch the rehearsal recording. Pass/fail and final 3 fixes."

After message 8 — you tag rc1 and demo.

---

## WHAT YOU DO NOT ASK ME

- "What's the project state" — read BACKLOG.md or the last audit report.
- "Is it good enough" — the acceptance gate above answers that.
- "Should I demo today" — if any ☐ is unchecked, no.
- "What about cluster / 600GB / UAT / GPG" — out of scope for this sprint. Cluster work is a separate engagement after the professor's assistant approves.
- "Help me think about pitch" — out of scope. The web app is the pitch.

---

## THE ONE-LINE TL;DR

**87 agent-hours, 10 days, 6 agents, 19 tasks, one acceptance gate. Do not interrupt the flow. Tag rc1. Demo.**

— Guru Agent, 2026-04-25, final scope-locked task pack.
