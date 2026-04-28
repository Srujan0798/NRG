# CP-FE-AUDIT Defect Catalogue

Generated: 2026-04-29
Scope: Local frontend code plus already-captured evidence under `evidence/2026-04-28/critical_path/` and `evidence/2026-04-29/`.
No fresh full-stack capture was run for this pass.

## Evidence Coverage

| Route | Evidence used | Console errors | Network 4xx/5xx | Coverage note |
|---|---:|---:|---:|---|
| `/` | `cp8_login_1366.png`, `main-flow-desktop-login-final.png` | 0 in final main-flow JSON | 0 in final main-flow JSON | Unauthenticated root renders login shell, not a separate public hero. |
| `/login` | `cp8_login_1366.png`, `cp8_login_375.png` | 0 in final main-flow JSON | 0 in final main-flow JSON | No explicit `/login` route in `frontend/src/App.tsx`; falls through to login when unauthenticated. |
| `/app/researcher` | `main-flow-desktop-dashboard-final.png`, `main-flow-mobile-dashboard-final.png` | 0 in final main-flow JSON | 0 in final main-flow JSON | Route falls through to role shell, not an explicit route. |
| `/app/government` | `cp5_tier_t2.png`, code inspection | Not captured | Not captured | Route falls through to role shell. |
| `/app/industry` | `cp5_tier_t3.png`, code inspection | Not captured | Not captured | Route maps to production workspace, not the legacy industry dashboard shell. |
| `/app/answer/<id>` | `main-flow-desktop-results-final.png`, `main-flow-mobile-results-final.png` | 0 in final main-flow JSON | 0 in final main-flow JSON | No explicit answer detail route; answer appears inline on researcher dashboard. |
| `/app/audit` | `cp4_audit_drawer.png`, `walk_step_06.png`, code inspection | Not captured | Not captured | Dedicated route exists. |
| `/app/graph` | code inspection | Not captured | Not captured | No explicit route; graph exists as an in-dashboard tab. |
| `/app/settings` | code inspection | Not captured | Not captured | Dedicated production workspace route exists. |
| `/404` | code inspection | Not captured | Not captured | No not-found route; falls through to auth shell. |
| `/app/answer/<id>?error=trigger` | code inspection | Not captured | Not captured | No trigger route/query handling. |
| `/app/answer/<id>?empty=trigger` | code inspection | Not captured | Not captured | No trigger route/query handling. |

## Defects

- id: D-001
  route: `/404`
  defect: "No 404 screen exists. Unknown paths fall through to `AppShell`, so `/404` displays login or the current role dashboard instead of a not-found state."
  screenshot: Not captured; local route inspection.
  severity: P1
  route_file: `frontend/src/App.tsx:202`
  proposed_fix: "Add an explicit not-found route with the same shell, focusable heading, and return-to-app action."

- id: D-002
  route: `/app/answer/<id>`
  defect: "No answer detail route exists despite the audit requirement. Deep links to an answer fall through to the role dashboard and cannot restore the cited answer."
  screenshot: `main-flow-desktop-results-final.png` shows answer only inline.
  severity: P1
  route_file: `frontend/src/App.tsx:138-202`
  proposed_fix: "Add a dedicated answer detail route or redirect with state hydration from `query_id`."

- id: D-003
  route: `/app/answer/<id>?error=trigger`
  defect: "Error-state trigger is not routable. The required CP audit route cannot be opened directly for browser verification."
  screenshot: Not captured; local route inspection.
  severity: P1
  route_file: `frontend/src/App.tsx:138-202`
  proposed_fix: "Add deterministic answer-state fixtures behind query params in the answer detail route."

- id: D-004
  route: `/app/answer/<id>?empty=trigger`
  defect: "Empty-state trigger is not routable. The required CP audit route cannot be opened directly for browser verification."
  screenshot: Not captured; local route inspection.
  severity: P1
  route_file: `frontend/src/App.tsx:138-202`
  proposed_fix: "Add deterministic empty-state rendering for the answer detail fixture route."

- id: D-005
  route: `/app/graph`
  defect: "No direct graph route exists. Graph UI is reachable only through an in-dashboard tab, so direct route capture falls through to the role shell."
  screenshot: Not captured; local route inspection.
  severity: P1
  route_file: `frontend/src/App.tsx:138-202`, `frontend/src/views/ResearcherDashboard.tsx:537`
  proposed_fix: "Map `/app/graph` to the graph workspace or preserve tab state from route."

- id: D-006
  route: `/app/researcher`
  defect: "No explicit researcher route exists. It relies on fallback `AppShell`, so the URL does not select the intended persona and depends on current session role."
  screenshot: `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/App.tsx:61-83`, `frontend/src/App.tsx:202`
  proposed_fix: "Add explicit role routes that verify session role or redirect with a clear access message."

- id: D-007
  route: `/app/government`
  defect: "No explicit government route exists. It relies on fallback `AppShell`, so capture depends on whoever is logged in."
  screenshot: `cp5_tier_t2.png`
  severity: P2
  route_file: `frontend/src/App.tsx:61-83`, `frontend/src/App.tsx:202`
  proposed_fix: "Add explicit role route handling for government dashboard."

- id: D-008
  route: `/login`
  defect: "No explicit `/login` route exists. The screen is shown by unauthenticated fallback only, which makes login-state and not-found-state behavior indistinguishable."
  screenshot: `cp8_login_1366.png`
  severity: P2
  route_file: `frontend/src/App.tsx:57-58`, `frontend/src/App.tsx:202`
  proposed_fix: "Add `/login` route and redirect authenticated users to their workspace."

- id: D-009
  route: `/app/researcher`
  defect: "Mobile header nav overflows horizontally; the Knowledge Graph tab is visibly clipped off the right edge."
  screenshot: `main-flow-mobile-dashboard-final.png`
  severity: P1
  route_file: `frontend/src/views/ResearcherDashboard.tsx:238-260`
  proposed_fix: "Use a compact mobile tab switcher or snap carousel with visible affordance and no clipped labels."

- id: D-010
  route: `/app/researcher`
  defect: "Mobile header action row is cramped; persona switcher and tier badge consume the full width and hide logout/theme affordances above the fold."
  screenshot: `main-flow-mobile-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/views/ResearcherDashboard.tsx:212-234`
  proposed_fix: "Move secondary actions into a menu on narrow viewports."

- id: D-011
  route: `/app/researcher`
  defect: "Search suggestions dominate the mobile viewport as oversized purple pills, pushing the actual input far below the panel title."
  screenshot: `main-flow-mobile-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/views/ResearcherDashboard.tsx:292-305`
  proposed_fix: "Render suggestions as a horizontally scrollable compact chip row on mobile."

- id: D-012
  route: `/app/researcher`
  defect: "Search input placeholder is clipped on mobile (`Ask anything about Indian research grants, inst...`)."
  screenshot: `main-flow-mobile-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/views/ResearcherDashboard.tsx:308-327`
  proposed_fix: "Shorten mobile placeholder copy or move helper text outside the input."

- id: D-013
  route: `/app/researcher`
  defect: "Dashboard has inconsistent data in captured states: publications and institutions show `0` in one final dashboard screenshot while adjacent evidence shows populated values."
  screenshot: `main-flow-mobile-dashboard-final.png`, `main-flow-desktop-results-final.png`
  severity: P1
  route_file: `frontend/src/views/ResearcherDashboard.tsx:420-459`
  proposed_fix: "Use one stats loading/error contract and avoid rendering zero as a loaded value until the API has resolved."

- id: D-014
  route: `/app/researcher`
  defect: "Desktop stat cards fade to near-invisible values in the rightmost card, making loaded content look disabled or broken."
  screenshot: `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/components/StatsCard/StatsCard.tsx:109-118`
  proposed_fix: "Remove opacity-driven visual treatment for real stat content and reserve skeleton styling for loading only."

- id: D-015
  route: `/app/researcher`
  defect: "Dashboard mixes card radii and panel styles: search panel uses `nrg-panel`, stats use large rounded cards, login uses tight rounded-lg cards."
  screenshot: `cp8_login_1366.png`, `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/index.css:246-250`, `frontend/src/components/Login.tsx:180-238`, `frontend/src/components/StatsCard/StatsCard.tsx:100-118`
  proposed_fix: "Choose one card radius/shadow scale and apply it across login, dashboard, and answer surfaces."

- id: D-016
  route: `/app/researcher`
  defect: "Visual palette drifts between saffron CTA, violet suggestions, blue active nav, green audit, and orange warning without a clear tier mapping."
  screenshot: `main-flow-desktop-results-final.png`
  severity: P2
  route_file: `frontend/src/index.css:28-79`, `frontend/src/views/ResearcherDashboard.tsx:301`, `frontend/src/components/AnswerPanel/AnswerPanel.tsx:420-436`
  proposed_fix: "Restrict route accent to one tier color plus semantic success/warning colors."

- id: D-017
  route: `/app/answer/<id>`
  defect: "Answer summary truncates at 300 characters and leaves a dangling citation marker (`[cite:innovation_...`) in the visible summary."
  screenshot: `main-flow-desktop-results-final.png`, `main-flow-mobile-results-final.png`
  severity: P1
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:409-412`
  proposed_fix: "Summarize parsed text without raw citation markers, or clamp by line with a full-content disclosure."

- id: D-018
  route: `/app/answer/<id>`
  defect: "Answer citation format is inconsistent: summary body shows raw `[cite:...]` while references show numbered chips."
  screenshot: `cp8_result_1366.png`, `main-flow-desktop-results-final.png`
  severity: P1
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:399-527`
  proposed_fix: "Normalize backend citation markers to numbered inline citations before rendering summary and full answer."

- id: D-019
  route: `/app/answer/<id>`
  defect: "Mobile result surface is extremely tall and repetitive; the SQL result table becomes stacked cards with repeated field labels for every row."
  screenshot: `main-flow-mobile-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:172-198`
  proposed_fix: "Use a compact mobile table pattern with sticky row headers or collapsible rows."

- id: D-020
  route: `/app/answer/<id>`
  defect: "Trust/provenance chips wrap into multiple rows on mobile, pushing answer content down and making the audit ID visually heavier than the answer."
  screenshot: `main-flow-mobile-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:416-443`
  proposed_fix: "Collapse provenance into a compact metadata bar on mobile."

- id: D-021
  route: `/app/answer/<id>`
  defect: "Audit ID chip uses a long monospace hash that still consumes too much horizontal space even when truncated."
  screenshot: `main-flow-desktop-results-final.png`, `main-flow-mobile-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:420-429`
  proposed_fix: "Show a short hash by default and reveal the full hash in copy/proof details."

- id: D-022
  route: `/app/answer/<id>`
  defect: "HMAC verification badge overflowed on narrow mobile evidence, causing horizontal clipping."
  screenshot: `cp8_result_375.png`
  severity: P1
  route_file: `frontend/src/components/VerifiedBadge/VerifiedBadge.tsx:33-40`
  proposed_fix: "Constrain the badge to `max-width: 100%` and truncate the hash text. Implemented in this pass."

- id: D-023
  route: `/app/answer/<id>`
  defect: "SQL retrieval block in earlier evidence clips the query horizontally inside the card on mobile."
  screenshot: `cp8_result_375.png`
  severity: P2
  route_file: `frontend/src/components/SqlBlock/SqlBlock.tsx:36-52`, `frontend/src/components/StreamingAnswerPanel.tsx:85-134`
  proposed_fix: "Use horizontal scroll with visible overflow affordance and copy action fixed outside the scroll region."

- id: D-024
  route: `/app/answer/<id>`
  defect: "Primary answer action row stacks unevenly on mobile; buttons use different widths and alignment."
  screenshot: `cp8_result_375.png`, `main-flow-mobile-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerTrustActions/AnswerTrustActions.tsx`
  proposed_fix: "Use full-width stacked buttons on mobile and consistent icon/button spacing."

- id: D-025
  route: `/app/answer/<id>`
  defect: "Export button appears disabled or secondary despite being a primary utility action; it has muted text next to high-saturation verification chips."
  screenshot: `main-flow-desktop-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:432-442`
  proposed_fix: "Apply one utility-button variant for Export, CSV, Copy, Source Data, and Audit Event."

- id: D-026
  route: `/app/answer/<id>`
  defect: "The answer panel uses `font-hindi` for English summary text, which is not defined in `index.css` and can fall back unpredictably."
  screenshot: `main-flow-desktop-results-final.png`
  severity: P2
  route_file: `frontend/src/components/AnswerPanel/AnswerPanel.tsx:481`, `frontend/src/index.css:455-467`
  proposed_fix: "Use `font-sans` for English answer text and reserve Devanagari font classes for Hindi labels."

- id: D-027
  route: `/login`
  defect: "Login and authenticated dashboard use different shells: login is flat white/slate with square cards, while dashboard is warm glassmorphism with large soft cards."
  screenshot: `cp8_login_1366.png`, `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:137-238`, `frontend/src/views/ResearcherDashboard.tsx:196-283`
  proposed_fix: "Adopt the same app canvas, card radius, header treatment, and elevation scale on login and dashboards."

- id: D-028
  route: `/login`
  defect: "Hero copy dominates the login page at 1366px; the sign-in card is visually secondary even though login is the task."
  screenshot: `cp8_login_1366.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:178-238`
  proposed_fix: "Reduce hero type scale and balance the sign-in card width/weight."

- id: D-029
  route: `/login`
  defect: "Trust markers in the login header are small unclickable pills that look like filters; they do not match the dashboard's consent/audit controls."
  screenshot: `cp8_login_1366.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:169-175`
  proposed_fix: "Render trust state as a compact status strip matching authenticated consent/audit styling."

- id: D-030
  route: `/login`
  defect: "Persona cards use a black border for selected state, while authenticated persona/tier controls use blue/violet fills."
  screenshot: `cp8_login_1366.png`, `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:217-220`, `frontend/src/components/PersonaToggle.tsx:98-125`
  proposed_fix: "Use the same selected persona token and active-state shape in login and authenticated controls."

- id: D-031
  route: `/login`
  defect: "Visible credential prefill exposes full email and password dots by default, which makes the sign-in surface look like a demo fixture."
  screenshot: `cp8_login_1366.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:95-112`, `frontend/src/components/Login.tsx:275-326`
  proposed_fix: "Keep role presets but hide credentials behind a preset selector or use empty fields in production mode."

- id: D-032
  route: `/login`
  defect: "Footer copy says `Frontend local preview · API health checked separately`, which is internal environment language visible to users."
  screenshot: `cp8_login_1366.png`
  severity: P1
  route_file: `frontend/src/components/Login.tsx:383-387`
  proposed_fix: "Replace with production-safe compliance/version copy or hide outside local dev."

- id: D-033
  route: `/app/audit`
  defect: "Audit list opens a citation drawer for an audit event, reusing citation UI semantics for audit data."
  screenshot: `cp4_audit_drawer.png`
  severity: P2
  route_file: `frontend/src/pages/DPDP-Audit.tsx:60-71`
  proposed_fix: "Use an audit-specific drawer title, icon, and field layout."

- id: D-034
  route: `/app/audit`
  defect: "A second fixed `Open event page` button appears at bottom-left when an audit event is selected, separated from the drawer action context."
  screenshot: `cp4_audit_drawer.png`
  severity: P2
  route_file: `frontend/src/pages/DPDP-Audit.tsx:73-81`
  proposed_fix: "Move the deep-link action into the audit drawer footer."

- id: D-035
  route: `/app/audit/event/<id>`
  defect: "Audit event page renders the full hash as a normal mono paragraph, which can wrap awkwardly and dominate the page."
  screenshot: Not captured; local code inspection.
  severity: P2
  route_file: `frontend/src/pages/AuditEvent.tsx:54-58`
  proposed_fix: "Use short hash headline plus copy/reveal control for the full HMAC."

- id: D-036
  route: `/app/settings`
  defect: "Settings screen uses a different production workspace shell and very rounded cards (`rounded-3xl`) unlike login/dashboard answer cards."
  screenshot: Not captured; local code inspection.
  severity: P2
  route_file: `frontend/src/pages/ProductionWorkspace.tsx:200-232`
  proposed_fix: "Normalize settings layout to the same card radius and shell tokens as dashboard."

- id: D-037
  route: `/app/industry`
  defect: "Route `/app/industry` uses `ProductionWorkspace` while logged-in industry role in fallback uses `IndustryDashboard`, creating two competing industry UIs."
  screenshot: `cp5_tier_t3.png`
  severity: P1
  route_file: `frontend/src/App.tsx:70-74`, `frontend/src/App.tsx:186-190`
  proposed_fix: "Choose one industry route surface and redirect the other path to it."

- id: D-038
  route: `all`
  defect: "Design tokens are split across `frontend/src/design-system/**` and `frontend/src/index.css`, while the CP spec expects `frontend/src/styles/tokens.css`; no `frontend/src/styles/` or `frontend/src/components/ui/` package exists."
  screenshot: Code inspection.
  severity: P1
  route_file: `frontend/src/index.css:23-169`, `frontend/src/design-system/tokens/`
  proposed_fix: "Move runtime CSS variables into `frontend/src/styles/tokens.css` and map component primitives to a single `components/ui` layer."

- id: D-039
  route: `all`
  defect: "Literal hex colors remain in route/component styling, blocking the CP-FE-FIX acceptance target for tokenized colors."
  screenshot: Code inspection.
  severity: P2
  route_file: `frontend/src/index.css:28-79`, `frontend/src/views/ResearcherDashboard.tsx:196-201`, `frontend/src/components/Login.tsx:137-159`
  proposed_fix: "Replace literal route colors with design-token variables after the token file is canonical."

- id: D-040
  route: `all`
  defect: "Typography mixes Sohne, JetBrains Mono, undefined `font-hindi`, and `Tiro Devanagari Hindi` without loading a Devanagari font face."
  screenshot: `main-flow-desktop-results-final.png`, `main-flow-mobile-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/index.css:1-17`, `frontend/src/index.css:455-467`, `frontend/src/components/AnswerPanel/AnswerPanel.tsx:481`
  proposed_fix: "Load the Devanagari face explicitly or use a defined fallback stack; remove undefined font utility usage."

- id: D-041
  route: `all`
  defect: "The app uses multiple logo treatments: Ashoka ring on login, dark square Devanagari mark in hero, bordered square mark in dashboard, and `N` in production workspace."
  screenshot: `cp8_login_1366.png`, `cp8_hero_1366.png`, `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:71-92`, `frontend/src/views/Hero.tsx:106-110`, `frontend/src/pages/ProductionWorkspace.tsx:297`
  proposed_fix: "Define one brand mark component and reuse it across all shells."

- id: D-042
  route: `all`
  defect: "Global background uses decorative radial gradients from both `body` and `.nrg-app-canvas`, causing inconsistent warmth/blue tint between screens."
  screenshot: `cp8_hero_1366.png`, `main-flow-desktop-dashboard-final.png`
  severity: P2
  route_file: `frontend/src/index.css:214-225`, `frontend/src/index.css:238-244`
  proposed_fix: "Use one app background token and one optional route accent layer."

- id: D-043
  route: `all`
  defect: "Focus styling is global, but several motion buttons override hover/tap without local focus-visible classes, making keyboard focus quality inconsistent."
  screenshot: Code inspection.
  severity: P2
  route_file: `frontend/src/index.css:530-542`, `frontend/src/views/ResearcherDashboard.tsx:215-230`, `frontend/src/components/AnswerPanel/AnswerPanel.tsx:453-469`
  proposed_fix: "Add explicit focus-visible treatment to reusable button primitives and replace ad hoc motion buttons."

- id: D-044
  route: `all`
  defect: "Several buttons rely on text-only labels where icons exist, while adjacent controls use icon+text; command styling is inconsistent."
  screenshot: `cp8_login_1366.png`, `main-flow-desktop-results-final.png`
  severity: P2
  route_file: `frontend/src/components/Login.tsx:352-366`, `frontend/src/views/ResearcherDashboard.tsx:323-338`, `frontend/src/pages/ProductionWorkspace.tsx:223-229`
  proposed_fix: "Standardize Button variants with icon slots for command actions."

## Low-Risk Fix Applied

- `D-022`: constrained `VerifiedBadge` to `max-w-full`, made the icon non-shrinking, and truncated the visible audit hash so the HMAC proof badge no longer causes mobile overflow.

## Remaining Audit Gaps

- The CP-FE-AUDIT acceptance asks for fresh 1366x768 screenshots for all 12 routes. This pass did not boot the stack or create those screenshots; it used existing evidence only.
- Console and network counts are complete only for the final main-flow evidence JSON, which covers login, dashboard, and answer result on desktop/mobile. Other routes need a fresh Playwright/DevTools capture.
