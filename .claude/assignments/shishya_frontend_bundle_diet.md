# SHISHYA ASSIGNMENT: Frontend Bundle Diet (319KB → <250KB)

**FILES**
- `frontend/vite.config.ts` — `splitChunks` / `manualChunks` strategy
- `frontend/package.json` — dependency list to identify heavy packages
- `frontend/dist/assets/` — built chunks to measure
- `.claude/rules/frontend.md` — NRG frontend rules

**PROBLEM**
Largest Vite lazy-loaded chunk is 319KB raw. Spec target is <250KB raw. Current gzip is 87.80KB (acceptable).

**STEPS**
1. `cd frontend && npm run build | tee ../evidence/2026-05-05/bundle_diet/01_before_build.log`
2. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/03_chunk_sizes.log`
3. `npx vite-bundle-visualizer --template treemap -o ../evidence/2026-05-05/bundle_diet/02_bundle_treemap.html` (if available)
4. Identify the 319KB chunk contents: `grep -r "import" src/ | grep -i "plotly\|d3\|chart\|map\|heavy" | head -20`
5. Apply ONE fix: lazy-load with `React.lazy()` + `Suspense`, or add `manualChunk` in `vite.config.ts`, or tree-shake unused imports
6. Rebuild: `npm run build | tee ../evidence/2026-05-05/bundle_diet/04_after_build.log`
7. `ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/05_after_chunk_sizes.log`
8. `npm run test -- --watchAll=false | tee ../evidence/2026-05-05/bundle_diet/06_jest.log`
9. `npm run lint | tee ../evidence/2026-05-05/bundle_diet/07_lint.log`

**SKILLS**
- `.claude/skills/frontend-react-best-practices/SKILL.md`
- `.agents/skills/react-composition-patterns/SKILL.md`
- `.claude/skills/performance/SKILL.md`

**EVIDENCE**
`evidence/2026-05-05/bundle_diet/`
- `00_summary.md` — what changed, before/after sizes, commit SHA
- `03_chunk_sizes.log` — before chunk sizes
- `05_after_chunk_sizes.log` — after chunk sizes
- `06_jest.log` — test output
- `07_lint.log` — lint output
- `08_blockers.md` — what remains blocked

**DONE WHEN**
- [ ] Largest lazy-loaded chunk raw size < 250KB
- [ ] Entry chunk stays < 5KB raw
- [ ] `npm run test -- --watchAll=false` passes (or same count as before)
- [ ] `npm run lint` passes with 0 errors
- [ ] No runtime console errors on `npm run dev` home page
- [ ] Evidence files committed

**HALT RULE**
If bundle size does not drop after 3 attempts, STOP. Escalate to Guru with treemap and chunk analysis.
