# NRG Zero-Partial Release-Candidate Validation

Date: 2026-05-01

Status: local release-candidate validation passed for the gates listed below.
This is not a whole-product "100% perfect" or deployed-production claim. Production replay, live Qdrant baseline, cluster C4 load, and founder sign-off remain outside this local campaign.

## Source Truth Used

- `.claude/skills/hybrid-mvp-fusion/SKILL.md`
- `.claude/skills/nrg-validation-campaign/SKILL.md`
- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- `Core_Idea_Clean.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `db_struct.sql`
- `CORPUS/killer_queries.yaml`
- `CORPUS/SQL_AUDIT_RAW_dhairya.sql`

## Fixes Made

- Raised low-contrast muted copy in the legacy login shell from `text-slate-500` to darker accessible slate values.
- Darkened the light-theme warning token used by government-tier pills so small `T2` labels pass WCAG AA contrast.
- Updated Playwright authentication fixtures to seed both `sessionStorage` and `localStorage` with bearer-shaped test sessions.
- Updated browser tests to target the current answer-engine query surface instead of stale hero selectors.
- Made UI evidence capture tests use mocked authenticated sessions and realistic hydration timeouts instead of depending on a live backend login.
- Increased mobile and UI evidence-walk time budgets where full-page screenshots and video capture exceed Playwright's default 30 seconds.

## Validation Matrix

| Surface | Result | Evidence |
| --- | --- | --- |
| Corpus sync | PASS | `01_corpus_sync.log` |
| Dhairya SQL regression and adversarial SQL | PASS: 61 passed, 2 skipped | `02_dhairya_sql_regression.log` |
| Backend/API/security/audit targeted suite | PASS: 195 passed, 1 skipped | `05_backend_security_audit_query.log` |
| Frontend build before browser fixes | PASS | `04_frontend_build.log` |
| Frontend build after browser fixes | PASS | `10_frontend_build_after_ui_fixes.log` |
| Frontend unit/component tests | PASS: 97 passed | `16_frontend_jest_after_browser_fixes.log` |
| Token contrast tests | PASS: 20 passed | `17_frontend_contrast_after_browser_fixes.log` |
| Killer queries | PASS: 3 killer queries captured with SQL/source/audit evidence | `08_killer_queries.log`, `killer/` |
| Browser UI/a11y/evidence walk | PASS: 15 passed | `15_playwright_ui_a11y_release_candidate_pass.log` |
| Desktop/mobile screenshots | PASS: login, dashboard, hero, answer, audit captured at 1366px and 375px | `../ui_ux/after/` |

## Browser Coverage

Final browser command covered:

- axe checks for login, hero, founder, researcher dashboard, government dashboard, and industry dashboard
- keyboard skip link, slash focus, query submission, and reduced-motion state
- answer-engine ask to streaming answer proof path
- no-stack-trace error surface check
- mobile killer query, citation drawer, no-horizontal-scroll checks
- mobile persona switcher and graph modal
- desktop and mobile UI/UX screenshots for login, dashboards, hero, answer, and audit list

Final browser result: `15 passed (2.9m)`.

## Known Boundaries

- This is local validation against the built frontend, local API tests, and mocked browser API paths where appropriate.
- It does not prove deployed infrastructure, production vector index recall, 1000-user cluster C4, or real user acceptance.
- The correct next gate for a stronger claim is deployed replay plus production dependency health and load evidence.
