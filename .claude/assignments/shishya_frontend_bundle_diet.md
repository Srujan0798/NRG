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
- `.claude/rules/frontend.md` — NRG frontend rules

**PROBLEM**
Largest Vite lazy-loaded chunk is 319KB raw. Spec target is <250KB raw. Current gzip is 87.80KB (acceptable).

## Execution

**STEPS** — Sequential actions:
1. `cd frontend && npm run build | tee ../evidence/2026-05-05/bundle_diet/01_before_build.log`
2. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/03_chunk_sizes.log`
3. `npx vite-bundle-visualizer --template treemap -o ../evidence/2026-05-05/bundle_diet/02_bundle_treemap.html` (if available)
4. Identify the 319KB chunk contents: `grep -r "import" src/ | grep -i "plotly\|d3\|chart\|map\|heavy" | head -20`
5. Apply ONE fix: lazy-load with `React.lazy()` + `Suspense`, or add `manualChunk` in `vite.config.ts`, or tree-shake unused imports
6. Rebuild: `npm run build | tee ../evidence/2026-05-05/bundle_diet/04_after_build.log`
7. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/05_after_chunk_sizes.log`
8. `npm run test -- --watchAll=false | tee ../evidence/2026-05-05/bundle_diet/06_jest.log`
9. `npm run lint | tee ../evidence/2026-05-05/bundle_diet/07_lint.log`

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
`evidence/2026-05-05/bundle_diet/`
- `00_summary.md` — what changed, before/after sizes, commit SHA
- `03_chunk_sizes.log` — before chunk sizes
- `05_after_chunk_sizes.log` — after chunk sizes
- `06_jest.log` — test output
- `07_lint.log` — lint output
- `08_blockers.md` — what remains blocked

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
