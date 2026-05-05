# SHISHYA ASSIGNMENT: Frontend Bundle Diet (319KB → <250KB)

> Copy this entire block and paste to your Shishya agent. Do not paraphrase.

---

## Goal
Optionally reduce the largest Vite lazy-loaded chunk from 319KB raw to under
250KB raw. Current gzip is 87.80KB and the enforced build budget is 500KB raw,
so this is an optimization task, not a current release blocker.

## Must Read (in order)
1. `frontend/vite.config.ts` — check splitChunks / manualChunks strategy
2. `frontend/package.json` — identify largest dependencies
3. `.claude/rules/frontend.md` — NRG frontend rules
4. `docs/adr/ADR-008-query-helper-reconciliation.md` — if query helper is bloating bundle

## Exact Commands to Run

```bash
# 1. Build with bundle analysis
cd "$(git rev-parse --show-toplevel)/frontend"
mkdir -p ../evidence/2026-05-05/bundle_diet
npm run build 2>&1 | tee ../evidence/2026-05-05/bundle_diet/01_before_build.log

# 2. Generate bundle report (if vite-bundle-analyzer or rollup-plugin-visualizer exists)
npx vite-bundle-visualizer --template treemap -o ../evidence/2026-05-05/bundle_diet/02_bundle_treemap.html

# 3. If no visualizer, inspect chunks manually
ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/03_chunk_sizes.log

# 4. Identify the 319KB chunk and what modules it contains
grep -r "import" src/ | grep -i "plotly\|d3\|chart\|map\|heavy" | head -20

# 5. Apply ONE of these fixes (pick simplest first):
#    a) Lazy-load a heavy component with React.lazy() + Suspense
#    b) Move a heavy dep to a separate manualChunk in vite.config.ts
#    c) Replace heavy library with lighter alternative (discuss with Guru first)
#    d) Tree-shake unused imports

# 6. Rebuild and measure
npm run build 2>&1 | tee ../evidence/2026-05-05/bundle_diet/04_after_build.log
ls -la dist/assets/ | grep -E "\.js$" | sort -k5 -rn | tee ../evidence/2026-05-05/bundle_diet/05_after_chunk_sizes.log

# 7. Run frontend tests to ensure nothing broke
npm run test -- --watchAll=false 2>&1 | tee ../evidence/2026-05-05/bundle_diet/06_jest.log

# 8. Lint check
npm run lint 2>&1 | tee ../evidence/2026-05-05/bundle_diet/07_lint.log
```

## Acceptance Criteria

- [ ] Largest lazy-loaded chunk raw size < 250KB
- [ ] Entry chunk stays small (< 5KB raw)
- [ ] `npm run test -- --watchAll=false` passes (or same count as before)
- [ ] `npm run lint` passes with 0 errors
- [ ] No runtime console errors on `npm run dev` home page
- [ ] All 3 killer query browser screenshots still render correctly

## Evidence Output Path

Save all evidence to: `evidence/2026-05-05/bundle_diet/`

Required artifacts:
- `00_summary.md` — what you changed, before/after sizes, commit SHA
- `03_chunk_sizes.log` — before chunk sizes
- `05_after_chunk_sizes.log` — after chunk sizes
- `06_jest.log` — test output
- `07_lint.log` — lint output
- `08_blockers.md` — what remains

## If Blocked

Stop immediately and report BLOCKED with:
1. Which chunk is largest and what deps it contains
2. What fix you attempted
3. Why it failed (build error, test break, or size didn't drop)

## Halt Rule

If bundle size does not drop after 3 attempts, STOP. Do not keep adding manualChunks blindly. Escalate to Guru with the treemap and chunk analysis.
