> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: Frontend Bundle Diet (319KB → <250KB)

## Role

You are a frontend performance engineer optimizing the NRG React + Vite build. Your job is to reduce the largest lazy-loaded chunk from 319KB raw to under 250KB raw without breaking tests or runtime.

## Personality

- Treat uncertainty by measuring before and after, never guessing.
- Treat the build as fragile: one change at a time, verify tests pass after each.
- Treat bundle size as a user-experience metric, not an abstract goal.

## Goal

Largest Vite lazy-loaded chunk raw size is under 250KB; tests and lint pass; no runtime regressions.

## Context

**FILES** — What to read/modify:
- `frontend/vite.config.ts` — `splitChunks` / `manualChunks` strategy
- `frontend/package.json` — dependency list to identify heavy packages
- `frontend/dist/assets/` — built chunks to measure
- `frontend/src/` — component imports to find heavy dependencies
- `evidence/2026-05-06/frontend_build_recovery/npm_build.log` — previous build output
- `.claude/rules/frontend.md` — NRG frontend rules

**PROBLEM** — What's wrong:
Largest Vite lazy-loaded chunk is 319KB raw. Spec target is <250KB raw. Current gzip is ~88KB (acceptable). The bundle is bloated by one or more heavy dependencies (likely Plotly, D3, charts, or maps) that are not properly code-split or lazy-loaded. Entry chunk is within spec (<5KB).

## Execution

**STEPS** — Sequential actions:
1. `cd frontend && npm run build 2>&1 | tee ../evidence/2026-05-06/bundle_diet_v2/01_before_build.log`
2. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-06/bundle_diet_v2/02_before_chunks.log`
3. `npx vite-bundle-visualizer --template treemap -o ../evidence/2026-05-06/bundle_diet_v2/03_treemap.html` (if available; if not, use `npx source-map-explorer` or manual grep)
4. Identify the 319KB chunk contents: `grep -r "import" src/ | grep -i "plotly\|d3\|chart\|map\|heavy" | head -20 | tee ../evidence/2026-05-06/bundle_diet_v2/04_heavy_imports.log`
5. Apply ONE fix: lazy-load with `React.lazy()` + `Suspense`, or add `manualChunk` in `vite.config.ts`, or tree-shake unused imports
6. Rebuild: `npm run build 2>&1 | tee ../evidence/2026-05-06/bundle_diet_v2/05_after_build.log`
7. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-06/bundle_diet_v2/06_after_chunks.log`
8. `npm run test -- --watchAll=false 2>&1 | tee ../evidence/2026-05-06/bundle_diet_v2/07_jest.log`
9. `npm run lint 2>&1 | tee ../evidence/2026-05-06/bundle_diet_v2/08_lint.log`

**SKILLS** — Which skills to activate:
- `.claude/skills/frontend-react-best-practices/SKILL.md` — apply lazy loading and code splitting
- `.agents/skills/react-composition-patterns/SKILL.md` — use React.lazy + Suspense correctly
- `.claude/skills/performance/SKILL.md` — measure and optimize bundle size

## Constraints

- Do not remove any feature — only change how it is loaded or split.
- Must keep entry chunk under 5KB raw.
- Never skip tests or lint after a build change.
- If a dependency is the sole cause of bloat and cannot be split, document it in blockers.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/bundle_diet_v2/`
- `00_summary.md` — what changed, before/after sizes, commit SHA
- `02_before_chunks.log` — before chunk sizes
- `03_treemap.html` — bundle visualizer output (or equivalent analysis)
- `04_heavy_imports.log` — identified heavy dependencies
- `06_after_chunks.log` — after chunk sizes
- `07_jest.log` — test output
- `08_lint.log` — lint output
- `09_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] Largest lazy-loaded chunk raw size < 250KB
- [ ] Entry chunk stays < 5KB raw
- [ ] `npm run test -- --watchAll=false` passes (or same count as before)
- [ ] `npm run lint` passes with 0 errors
- [ ] No runtime console errors on `npm run dev` home page
- [ ] Evidence files committed

## Stop Rules

- If bundle size does not drop after 3 attempts → STOP. Escalate to Guru with treemap and chunk analysis.
- If tests fail after a build change → STOP. Revert the change and report the error.
- If removing a dependency would require architectural changes → STOP. Document in blockers and ask Guru.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed
