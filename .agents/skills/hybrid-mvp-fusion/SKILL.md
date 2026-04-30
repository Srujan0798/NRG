---
name: hybrid-mvp-fusion
description: "Permanently active skill. Merge EVERYTHING best from external MVPs into NRG — not just frontend, but system workflow, interaction design, UX flows, state management, routing, API patterns, data flows, component architecture, add-ons, combinations. Whatever the MVP does better, take it. Produce one unified hybrid that is the best possible version of NRG."
user-invocable: true
---

# Hybrid MVP Fusion

## The Core Truth

NRG has strong core architecture, security, audit chain, DPDP compliance, and orchestration pipeline. But the overall SYSTEM EXPERIENCE — the workflow from start to finish, the interaction design, the UX flow, the way everything connects, the add-ons, the combinations that make an app feel complete and professional — is where external MVPs built by high-level AI platforms often do better.

**This skill is NOT limited to frontend.** It covers EVERYTHING:

- **System workflow** — how the app flows from login to query to answer to explore to export
- **Interaction design** — how components interact, how state flows, how data moves
- **UX patterns** — loading, error, empty, success, navigation, transitions
- **Frontend components** — layouts, cards, charts, tables, forms, drawers
- **State management** — how the app manages data, caching, optimistic updates
- **Routing & navigation** — page structure, URL patterns, deep linking, breadcrumbs
- **API interaction patterns** — how frontend talks to backend, streaming, polling, caching
- **Add-on features** — onboarding, search suggestions, export, keyboard shortcuts, settings, notifications, help system
- **Data visualization** — charts, graphs, tables, maps, funnels
- **Mobile experience** — responsive design, touch interactions, gesture handling
- **Accessibility** — screen reader support, keyboard navigation, ARIA patterns
- **Performance patterns** — lazy loading, code splitting, prefetching, skeleton states
- **Any combination** that makes the product better

**The rule:** If the MVP does it better — take it. If the MVP has something NRG doesn't — add it. If combining MVP + NRG patterns creates something better than either — do that.

**The only things we protect:** NRG's DPDP compliance, audit chain (HMAC), per-user binding, tier-aware RBAC, PII detection, egress guard, and sovereign data residency. These are non-negotiable production requirements. Everything else is fair game for upgrade.

---

## ZERO SUMMARIZATION RULE (CRITICAL — READ THIS FIRST)

**The Founder's #1 complaint:** AI agents summarize the MVP, cherry-pick 1% of the valuable content, and claim everything was merged. This is FORBIDDEN.

### The Problem
A working MVP has maybe 40% valuable content across its entire codebase. Lazy agents will:
1. Skim the files
2. Summarize what they see
3. Extract a tiny fraction of the valuable parts
4. Add 1% of the 40% that's actually useful
5. Claim "all best elements have been merged"

**This is a LIE. This is NOT acceptable.**

### The Rule

```
EVERY FILE in the MVP must be read COMPLETELY — not skimmed, not summarized.
EVERY valuable element must be extracted — not "key highlights."
100% of the valuable content must be merged — not 1%, not 10%, not "the best parts."
If the MVP has 200 files, you read 200 files. No shortcuts.
If the fusion takes 3 hours, it takes 3 hours. No rushing.
```

### Enforcement

1. **File-by-file audit trail** — For every MVP file, the agent MUST log:
   - File path
   - What was valuable (or "nothing — skip")
   - What was extracted
   - Where it was merged into NRG

2. **Completeness check** — After fusion, compare:
   - Total MVP files provided vs. total files actually read
   - Total valuable elements identified vs. total elements merged
   - If ratio < 95%, fusion is INCOMPLETE — go back and finish

3. **No "key elements" language** — Agents must NOT say:
   - "I extracted the key elements" (you extracted ALL elements)
   - "I focused on the most important parts" (you covered ALL parts)
   - "Here are the highlights" (there are no highlights — there is the COMPLETE extraction)
   - "I summarized the MVP" (you did NOT summarize — you processed every file)

4. **Time expectation** — A full MVP fusion on a working web app WILL take significant time. This is expected and correct. Rushing = incomplete = rejected.

5. **Proof of completeness** — The fusion report MUST include:
   ```
   FILES PROCESSED: X / Y total (must be Y/Y)
   VALUABLE ELEMENTS FOUND: N
   ELEMENTS MERGED: M / N (must be N/N or justify each skip)
   ELEMENTS SKIPPED: list with reason for each
   ```

**If an agent claims "fusion complete" but only added a few components — the Founder will reject the entire output and the agent starts over.**

---

## Activation Triggers

This skill activates when the Founder says any of:
- "Apply MVP Hybrid Fusion"
- "Merge these MVPs"
- "Here are the MVP files"
- "Fuse this into NRG"
- Provides any MVP project files, MD files, screenshots, or working examples

---

## The Fusion Protocol

### Phase 1: DEEP ANALYSIS

Read every single file the Founder provides. For each file, understand:

1. **What screen/page does it create?** — Map the complete user journey from first screen to last
2. **What does it look like?** — Layout, colors, typography, spacing, visual hierarchy
3. **What does it feel like?** — Animations, transitions, micro-interactions, loading states
4. **What's the flow?** — How does the user move from login to dashboard to query to answer to explore?
5. **What's clever?** — Any UX pattern that's non-obvious but makes the experience great
6. **What components does it use?** — Buttons, cards, modals, drawers, tables, charts, forms
7. **What navigation pattern?** — Sidebar, top bar, tabs, breadcrumbs, bottom nav

Output a summary:

```markdown
## MVP Analysis — [Platform Name]

### User Journey (start to finish)
1. Landing/Login → [describe what user sees and does]
2. Dashboard → [describe layout, cards, data displayed]
3. Query input → [describe how user enters a question]
4. Results → [describe how answer is presented]
5. Details/Explore → [describe drill-down experience]
6. Settings/Profile → [describe user management]

### Best-in-Class Elements Found
| Element | Where | Why It's Excellent | NRG Impact |
|---------|-------|-------------------|------------|
| ... | ... | ... | ... |

### Design System Extracted
- Primary colors: [values]
- Typography: [font, sizes, weights]
- Spacing scale: [values]
- Border radius: [values]
- Shadows: [values]
- Animations: [what, where, timing]
```

### Phase 2: EXTRACTION

For every excellent element found, extract the actual implementation. **Not just visuals — EVERYTHING:**

**System Workflow & Architecture:**
- App initialization flow (what loads first, what's lazy)
- Authentication flow (login, session, refresh, logout)
- Query workflow (input → processing → streaming → result → explore)
- Data fetching patterns (React Query, SWR, custom hooks, caching)
- State management architecture (stores, context, props, URL state)
- Error handling strategy (error boundaries, retry logic, fallbacks)
- Routing structure (nested routes, guards, redirects, deep links)
- Feature flags or progressive disclosure patterns

**Interaction Design:**
- How user input triggers system behavior
- Optimistic updates (show result before server confirms)
- Real-time features (WebSocket, SSE, polling patterns)
- Multi-step workflows (wizards, progressive forms)
- Undo/redo patterns
- Keyboard shortcuts and power-user features
- Drag-and-drop interactions
- Search-as-you-type / autocomplete patterns

**Frontend Components & Visual:**
- Complete JSX/HTML layouts, CSS/Tailwind compositions
- Card designs, table designs, chart integrations
- Modal/drawer patterns, form layouts
- Navigation components, result display patterns
- Grid/flex patterns and responsive breakpoints
- Dark/light mode tokens

**UX Flows:**
- Login → redirect → dashboard (every transition)
- Query → loading → streaming → answer (every phase)
- Click → drawer/modal → detail → back (every navigation)
- Error → message → retry (every failure path)
- Empty → prompt → first action (every empty state)
- Onboarding → first query → first success (new user journey)
- Settings → preferences → apply (configuration flow)
- Export → format select → download (data export flow)

**Add-On Features (things NRG might not have):**
- Search suggestions / query templates / recent queries
- Bookmarks / saved queries / query history
- Export to CSV/PDF/clipboard
- Share query results via link
- Notification system (in-app, email digest)
- Help system / tooltips / guided tours
- Settings / preferences / profile management
- Keyboard shortcut panel
- Dark mode toggle
- Language selector
- Feedback mechanism (thumbs up/down on answers)
- Query comparison (side-by-side results)

**Micro-interactions & Polish:**
- Button hover/active states, input focus/blur effects
- Page transition animations, loading skeletons
- Toast/notification appearances, scroll-triggered reveals
- Favicon, page titles, smooth scrolling, cursor changes
- Copy-to-clipboard feedback, number formatting (Indian locale)

**API & Data Patterns (if MVP does it better):**
- API client architecture (interceptors, retry, caching)
- Request/response transformation patterns
- Streaming response handling (SSE, WebSocket)
- Pagination patterns (infinite scroll, cursor-based)
- Real-time data sync patterns
- Offline support / service worker patterns

### Phase 3: FUSION

The MVP dissolves INTO NRG — not alongside it. One unified product.

**For every extracted element:**

```
MVP Element → Adapt → NRG Component
                │
                ├── Wire to NRG API: frontend/src/services/
                ├── Wire to NRG Auth: frontend/src/hooks/ (JWT + tier claims)
                ├── Wire to NRG Types: frontend/src/types/
                ├── Wire to NRG State: frontend/src/stores/ (Zustand)
                ├── Wire to NRG i18n: frontend/src/i18n/en-IN.ts
                ├── Map to NRG Tokens: frontend/src/styles/
                ├── Add Trust Chain: ConfidenceBadge, CitationDrawer, ProofInspector, HmacProof
                ├── Add Tier Awareness: T1 full / T2 aggregated / T3 anonymized
                ├── Strip Forbidden Vocabulary: "demo" → "production"
                └── Verify: npm run build + npm run lint
```

**Fusion Rules:**

1. **If the MVP's component is visually better → REPLACE NRG's component entirely.** Don't merge two versions. Pick the better one and wire it to NRG's backend.
2. **If the MVP has a component NRG lacks → ADD it.**
3. **If NRG has a security/trust component → KEEP it but RESTYLE** to match the MVP's design language. `ConfidenceBadge`, `CitationDrawer`, `ProofInspector`, `HmacProof`, `ConsentBanner`, `DPDPPanel`, `PermissionBoundary` — stay but match the MVP visual system.
4. **The final product must feel like ONE app.** Consistent corners, colors, spacing everywhere. No seams.
5. **The flow must be continuous.** No jarring transitions between MVP-merged and NRG-original pages.

### Phase 4: THE COMPLETE FLOW TEST

```
FIRST IMPRESSION (< 3 seconds to judge)
├── App loads → Professional, fast, polished
├── Login page → Clean, institutional, trustworthy
└── Would the professor's assistant feel confident?

CORE WORKFLOW
├── Dashboard → Meaningful stats, clear navigation, tier indicator
├── Query input → Obvious where to type, maybe suggestions
├── Submit → Immediate feedback, streaming phases visible
├── Answer → Clean typography, citations inline, confidence shown
├── Explore → Citation drawer, source data, audit proof
└── Did the user get a useful answer with proof?

NAVIGATION
├── Menu/sidebar → Clear labels, logical grouping
├── Page transitions → Smooth, not jarring
├── Back navigation → Works as expected
└── Can the user find anything in < 2 clicks?

EDGE CASES
├── Error → Friendly message, retry, no stack trace
├── Empty → Helpful prompt, suggested first action
├── Loading → Skeleton/spinner that feels alive
├── Slow query → Progress indicator
└── Does every edge case feel intentional?

MOBILE (393px)
├── No horizontal scroll, touch targets ≥ 44px
├── Hamburger/drawer navigation
├── Query input → Keyboard doesn't cover it
└── Would someone use this on their phone?
```

**If any step feels broken, ugly, or amateur — the fusion is NOT done.**

### Phase 5: FUSION REPORT

```markdown
## Hybrid MVP Fusion Report — [Platform]

### Fusion Summary
| Category | Count | Examples |
|----------|-------|---------|
| Layouts | X | Dashboard, query, results |
| Components | X | Cards, search, results |
| Design Tokens | X | Colors, type, spacing |
| Animations | X | Transitions, loading |
| UX Flows | X | Login, query, explore |
| New Features | X | Onboarding, suggestions |

### Files Changed
| File | Change | Why |
|------|--------|-----|
| ... | ... | ... |

### Verification
- [ ] npm run build passes
- [ ] npm run lint passes
- [ ] Complete flow test passes
- [ ] Mobile responsive
- [ ] No forbidden vocabulary
- [ ] Tier awareness preserved
- [ ] Trust chain visible
- [ ] One unified visual language
```

---

## Multiple MVP Fusion

1. **First MVP** → Full fusion. Establish the visual baseline.
2. **Second MVP** → Selective upgrade. Only what's BETTER.
3. **Third+ MVP** → Always upgrade, never downgrade.
4. **Result = NRG + best-of-ALL-MVPs.**

---

## Integration With NRG Workflow

1. **Founder** provides MVP files → "Apply MVP Hybrid Fusion"
2. **Guru** activates this skill, assigns to Frontend Agent
3. **Frontend Agent** executes Phases 1-5 using: `hybrid-mvp-fusion`, `frontend-react-best-practices`, `design-system`, `webapp-testing`
4. **Guru** reviews Fusion Report
5. **QA Agent** verifies complete flow
6. **Founder** does the professor test

### Agent Assignment Template

```
═══ HYBRID MVP FUSION ═══

Source: [path to MVP files]
Platform: [name]

Execute hybrid-mvp-fusion skill (5 phases):
1. Deep Analysis → analysis summary
2. Extraction → all best elements
3. Fusion → merge into NRG frontend
4. Flow Test → verify complete journey
5. Report → produce fusion report

Skills: hybrid-mvp-fusion, frontend-react-best-practices, design-system, webapp-testing
DO NOT touch: src/ (backend), security/, audit/, auth/
DO merge: ALL visual/UX/flow excellence from the MVP
Target: NRG must feel like best UI/UX team built it
Verify: npm build + lint + flow test + mobile
```

---

## Auto-Chained Skills (agent runs ALL of these automatically after fusion)

After Phase 3 (Fusion) completes, the agent MUST automatically run these — the Founder should NOT have to ask:

### Auto-Chain 1: Live UI Audit
Read `.claude/skills/live-ui-audit/SKILL.md` and execute:
- Screenshot every page (all tiers, mobile, empty/error states)
- Run visual checklist (layout, typography, color, components, embarrassment guard)
- Run automated checks (build, lint, forbidden vocab, raw hex, stack traces)
- Flag any P0/P1 issues and FIX THEM before reporting

### Auto-Chain 2: Smart Prompt Library — Flow Queries
Read `.claude/skills/smart-prompt-library/SKILL.md` and run:
- All 5 Showcase queries (S1-S5) — verify answers render correctly in new UI
- All 3 Flow queries (F1-F3) — verify login→query→answer→citations journey
- All Tier queries — verify T1/T2/T3 show different shapes in new UI

### Auto-Chain 3: Query Quality Scorer (if API is running)
Read `.claude/skills/query-quality-scorer/SKILL.md` and run:
- Quick score on 7 Killer queries — verify no regression from UI merge
- Edge cases — verify blocked queries still show proper error UI

### Auto-Chain 4: Project Health (quick)
Read `.claude/skills/project-health/SKILL.md` and run:
- `npm run build` — MUST pass
- `npm run lint` — MUST pass
- `forbidden_vocab_check.sh` — MUST pass
- Python backend import test — MUST still work (fusion shouldn't touch backend)

### Auto-Chain 5: Session Replay Readiness
Produce a structured list of what the Founder should manually test after the merge, formatted as:
```
TEST THIS NOW:
1. Open [URL] → you should see [description]
2. Login as [user] → you should land on [page]
3. Type "[query]" → you should see [expected]
4. Click citations → you should see [expected]
5. Switch to mobile → everything should [expected]

KNOWN ISSUES (will fix in next pass):
- [anything the auto-checks found that needs manual fix]
```

**The Founder says ONE thing. Everything else is automatic.**

---

## NEVER Touch
- DPDP compliance logic (consent, PII detection, egress guard)
- Audit chain (HMAC signing, verification, lineage)
- Per-user binding and tier-aware RBAC enforcement
- Sovereign data residency rules
- Security middleware (JWT validation, rate limiting, injection prevention)

## ALWAYS Take — EVERYTHING That's Better
- **System workflow** — app initialization, authentication flow, query lifecycle
- **Interaction design** — how inputs trigger behavior, optimistic updates, real-time features
- **UX flows** — every transition from login to query to answer to explore to export
- **Frontend components** — layouts, cards, charts, tables, forms, drawers, modals
- **State management** — stores, caching, URL state, optimistic updates
- **Routing & navigation** — page structure, deep linking, breadcrumbs, transitions
- **API interaction patterns** — client architecture, streaming, polling, retry, caching
- **Add-on features** — search suggestions, bookmarks, export, notifications, help, settings, dark mode, feedback, shortcuts
- **Data visualization** — charts, graphs, tables, maps, funnels
- **Mobile experience** — responsive design, touch interactions, gestures
- **Accessibility** — screen reader, keyboard nav, ARIA
- **Performance patterns** — lazy loading, code splitting, prefetching, skeletons
- **Micro-interactions** — hover states, transitions, loading animations, copy feedback
- **Any combination** that makes the product better than either MVP or NRG alone

---

> **The MVP is the teacher of excellence.**
> **NRG is the student with a PhD in backend security.**
> **Take ALL the teacher's lessons — workflow, UX, interactions, features, everything.**
> **Keep the PhD — DPDP, audit chain, HMAC, RBAC, PII detection, egress guard.**
> **The result: a product that does everything better than either could alone.**
