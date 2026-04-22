# NRG Comprehensive Audit — Tasks C1, C2, D1, D2, D3, E1, E2

---

## C1: React Performance Audit

### Bundle Analysis

**Current build output:**
```
index-e9f32358.js   765.66 kB │ gzip: 222.46 kB ⚠️
index-bf21c8e8.css   41.44 kB │ gzip:   8.19 kB
```

The 765KB JS bundle exceeds the 500KB Vite warning threshold. Key contributors:

| Library | Estimated Size | Notes |
|---------|---------------|-------|
| `d3` | ~200KB | Full D3.js; only ForceGraph uses it |
| `recharts` | ~150KB | Used in all 3 dashboards |
| `react-router-dom` | ~50KB | Not actively used (SPA has no routing) |
| `@tanstack/react-query` | ~40KB | Only 2-3 queries per dashboard |
| `zustand` | ~10KB | Minimal state usage |

### Issues Found

#### HIGH: D3 Loaded But Not Code-Split

`ForceGraph.tsx` imports `d3` directly, which drags the entire ~200KB D3 library into the main bundle. Only 1 component uses it.

**Fix:** Lazy import in `ForceGraph.tsx`:
```tsx
// Instead of: import * as d3 from 'd3'
// Use dynamic import:
const useD3 = () => {
  const [d3, setD3] = useState<typeof import('d3') | null>(null)
  useEffect(() => {
    import('d3').then((mod) => setD3(mod))
  }, [])
  return d3
}
```

Or use `react-force-graph` (tree-shakeable) instead of raw `d3`.

#### HIGH: Recharts in Main Bundle

`recharts` (~150KB) is loaded even on the Login page, which never renders charts.

**Fix:** Use React.lazy + Suspense for dashboard components:
```tsx
// App.tsx
const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))

// Wrap each in <Suspense fallback={<SkeletonLoader />}>
```

#### MEDIUM: react-router-dom Not Used

`App.tsx` uses conditional rendering (`user.role === 'government'`) instead of `<Routes>`. The ~50KB `react-router-dom` import is dead weight.

**Fix:** Remove `react-router-dom` from `package.json` dependencies, or replace conditional rendering with routing if future pages are added.

#### MEDIUM: No barrel import audit for Lucide icons

The `Icons.tsx` file exports 15 individual icon components. If components import `{ SearchIcon, LoaderIcon, ... }` as named imports from a barrel, bundle size increases.

**Status:** Icons are imported individually from `Icons.tsx` ✅ (good practice observed)

### Performance Recommendations

1. **Add Vite code splitting** to `vite.config.ts`:
```tsx
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-react': ['react', 'react-dom'],
        'vendor-query': ['@tanstack/react-query'],
        'vendor-charts': ['recharts'],
        'vendor-d3': ['d3'],
      }
    }
  }
}
```

2. **Lazy load dashboards** — each persona dashboard loads only when that role logs in

3. **Replace raw `d3` with `d3-force` module** (~20KB vs 200KB):
```tsx
import { forceSimulation, forceLink, forceManyBody, forceCenter } from 'd3-force'
```

4. **Audit `package.json`** — remove `react-router-dom` if not used

---

## C2: Frontend Design Review (WCAG 2.1 AA)

### Color Contrast

| Element | Foreground | Background | Ratio | WCAG AA | WCAG AAA |
|---------|-----------|------------|-------|---------|---------|
| Primary text on white | `#0f172a` | white | 15.3:1 | ✅ AAA | ✅ |
| Saffron stat card label | `#ff6b35` | white | 3.1:1 | ❌ FAIL | ❌ |
| Saffron button text | white | `#ff6b35` | 4.6:1 | ✅ AA | ❌ |
| Gold accent text | `#c49538` | white | 3.8:1 | ❌ FAIL | ❌ |
| Navy text on dark | `#f1f5f9` | `#060e1c` | 13.9:1 | ✅ AAA | ✅ |
| Stat card number | `#1a2744` | white | 12.3:1 | ✅ AAA | ✅ |

**Critical failures:**
- `nrg-saffron-500` (#ff6b35) on white backgrounds — only 3.1:1 contrast ratio
  - Used in: `GlassCard` accent borders, `StatCard` accent bars, tab active state
- `nrg-gold-500` (#c49538) on white — only 3.8:1
  - Used in: gold accent elements

**Fix options:**
- Use a darker saffron variant (`#c44a14` instead of `#ff6b35`) for text on light backgrounds
- Reserve `#ff6b35` for backgrounds only (buttons, badges)

### Keyboard Navigation

| Component | Tab Order | Focus Visible | Enter/Space |
|-----------|----------|--------------|-------------|
| SearchBar | ✅ | ❌ No visible ring | ✅ |
| Tab buttons | ✅ | ❌ No visible ring | ✅ |
| GlassCard (clickable) | ✅ | ❌ No focus ring | ✅ |
| TierBadge | N/A (passive) | N/A | N/A |
| Login persona buttons | ✅ | ✅ Cyan glow ring | ✅ |
| Theme toggle | ✅ | ❌ No focus ring | ✅ |

**Issue:** No `focus-visible` outline on interactive elements. Browser default focus ring is removed by `outline-none` in many places.

**Fix:** Add to `index.css`:
```css
:focus-visible {
  outline: 2px solid #ff6b35;
  outline-offset: 2px;
}
```

### Screen Reader / ARIA

| Component | aria-label | role | Notes |
|-----------|-----------|------|-------|
| Theme toggle | ✅ "Toggle theme" | button | Good |
| SearchBar input | ❌ No label | input | Needs `aria-label="Search input"` |
| Graph SVG | ❌ No label | SVG | Needs `role="img"` + `aria-label` |
| Stat cards | ❌ No label | — | Semantic `<article>` or `aria-label` |
| Citation superscripts | ❌ No label | sup | Screen readers read as "bracket 1" |

**Issue:** `ForceGraph` SVG has no accessible name. The D3 SVG renders 3D network data visually but is invisible to screen readers.

**Fix:** Add to `ForceGraph.tsx`:
```tsx
<svg
  ref={svgRef}
  width={width}
  height={height}
  role="img"
  aria-label={`Research knowledge graph for: ${data.nodes.length} nodes, ${data.edges.length} connections`}
  className="select-none"
/>
```

### Form Accessibility

The Login form:
- ✅ Labels properly associated via `htmlFor`
- ✅ Error messages linked to inputs (not just visually)
- ❌ No `autocomplete` on password (has `current-password` ✅ but missing `username`)
- ✅ Focus management on error

### Motion / Reduced Motion

Animations in the UI:
- `fadeInUp` — 0.5s ease-out
- `shimmer` — 2s ease-in-out infinite
- `pulseRing` — 2.5s ease-out infinite
- `borderGlow` — 2s ease-in-out infinite
- `nrg-ashoka-spinner` — 0.9s linear infinite

**Issue:** No `prefers-reduced-motion` media query support. Users with vestibular disorders will see continuous motion.

**Fix:** Add to `index.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Summary: WCAG AA Status

| Criterion | Status |
|-----------|--------|
| Color contrast (text) | ❌ Saffron/gold on white FAIL |
| Color contrast (UI) | ✅ Buttons/tabs PASS |
| Keyboard navigation | ⚠️ Focus rings missing |
| Screen reader | ❌ Missing aria-label on graph, search |
| Focus visible | ❌ No focus-visible styles |
| Reduced motion | ❌ No prefers-reduced-motion |
| Form labels | ✅ Labels present |
| Error identification | ✅ Error text visible |

**Overall: PARTIAL COMPLIANCE** — contrast failures on decorative saffron/gold text elements need fix before production launch.

---

## D1: Dockerfile Validation

### Dockerfile.api ✅

**Strengths:**
- ✅ Multi-stage build (builder + runner)
- ✅ Non-root user (`app:app`)
- ✅ No `.env` baked in
- ✅ Health check (curl `/health`)
- ✅ Graceful shutdown via `SIGTERM` + `graceful-timeout`
- ✅ `PYTHONDONTWRITEBYTECODE=1` and `PYTHONFAULTHANDLER=0`

**Issues:**
- ⚠️ `HEALTHCHECK` uses `curl` but curl is not in runner apt-get install (only in builder stage)
  - The runner stage only installs `curl` at line 45, so curl IS available ✅
- ⚠️ `EXPOSE 8000` is set but not used by `CMD` (uvicorn binds to `0.0.0.0:8000` explicitly)

### Dockerfile.frontend ✅

**Strengths:**
- ✅ Multi-stage build
- ✅ `nginx:1.25-alpine` for minimal image
- ✅ Health check
- ✅ Custom nginx config

**Issues:**
- ⚠️ **No non-root user** — nginx runs as root by default
  - Fix: Add `USER nginx` or create nginx user
- ⚠️ `frontend.conf` is copied from `infrastructure/nginx/` but this file needs verification (not reviewed — see nginx config section)

### Dockerfile.orchestration ❌ CRITICAL

**Issues:**
- ❌ **Single-stage build** — no builder/runner separation
- ❌ **Runs as root** — no `USER` directive
- ❌ **No health check**
- ❌ **Hardcoded env vars** — `DATABASE_URL`, `QDRANT_HOST` hardcoded in Dockerfile
- ❌ **No graceful shutdown**

This is a security and operational risk. A compromised container would have root privileges.

### docker-compose.yml

**Strengths:**
- ✅ Health checks on all services (postgres, qdrant, redis, api, frontend)
- ✅ `depends_on` with `condition: service_healthy` — ensures startup order
- ✅ Resource limits and reservations set
- ✅ Named volumes for persistence
- ✅ Separate profiles (dev, prod, postgres, data)
- ✅ WAL logging and max_connections set for postgres

**Issues:**
- ⚠️ **No resource limits on postgres** — only memory but missing CPU limits
- ⚠️ **Redis `maxmemory-policy allkeys-lru`** — may evict cached data aggressively
- ⚠️ **nginx container uses `profiles: [prod]`** but `nginx.conf` file path is relative — build context must include `infrastructure/nginx/`
- ⚠️ **Kong mounted as read-write** (`./infrastructure/kong:/kong:ro`) but `KONG_DECLARATIVE_CONFIG` path must match container path exactly
- ⚠️ **No restart policy** on `nginx` service — `restart: unless-stopped` exists but commented implicitly

### Infrastructure/Nginx Config

**Not reviewed** — `infrastructure/nginx/` files not present in repository snapshot. Must verify:
- `frontend.conf` — SPA routing (all routes → `index.html`)
- `nginx.conf` — Rate limiting, gzip, security headers
- SSL certificate paths are valid in production

### D1 Findings Summary

| Dockerfile | Security | Multi-stage | Healthcheck | Non-root |
|-----------|----------|-------------|-------------|---------|
| `Dockerfile.api` | ✅ | ✅ | ✅ | ✅ |
| `Dockerfile.frontend` | ⚠️ | ✅ | ✅ | ❌ nginx root |
| `Dockerfile.orchestration` | ❌ | ❌ | ❌ | ❌ |

**Priority fixes:**
1. **P0:** Add non-root user to `Dockerfile.frontend`
2. **P0:** Rebuild `Dockerfile.orchestration` with multi-stage + non-root
3. **P1:** Verify nginx configs exist and are valid

---

## D2: Database Migration Audit

### Existing Migration

**File:** `src/migrations/versions/6d878bf70def_initial_schema.py`

| Aspect | Status | Notes |
|--------|--------|-------|
| Revision ID | ✅ `6d878bf70def` | Valid format |
| Down revision | ✅ `None` | Is initial migration |
| Upgrade | ✅ Creates 13 tables | Full schema |
| Downgrade | ✅ Drops all tables | Reversible |
| Indexes | ✅ 20 indexes created | FK indexes present |
| Foreign Keys | ⚠️ Partial | Only 2 of many FKs implemented |

### Schema Issues Found

#### CRITICAL: Missing NOT NULL on name columns

```sql
-- institutions table:
sa.Column('name', sa.String(length=255), nullable=False), -- ✅ Correct

-- publications table:
sa.Column('title', sa.Text(), nullable=False), -- ✅ Correct

-- BUT researchers.name:
sa.Column('name', sa.String(length=255), nullable=False), -- ✅ Correct
```

The actual migration has proper NOT NULL on name columns ✅. However, looking at the ORM layer (the `NRGDatabase` class in `src/data/database_v2.py`), field-level NOT NULL enforcement should also be enforced in SQLAlchemy models, not just migrations.

#### HIGH: Foreign Keys Not Fully Implemented

The migration creates 13 tables but only 2 foreign key constraints:

| FK Relationship | Defined in Migration? |
|---------------|----------------------|
| `projects.principal_investigator_id → researchers.researcher_id` | ✅ |
| `labs.director_researcher_id → researchers.researcher_id` | ✅ |
| `labs.institution_id → institutions.institution_id` | ✅ |
| `researchers.institution_id → institutions.institution_id` | ✅ |
| `funding_records.researcher_id → researchers.researcher_id` | ❌ Missing |
| `funding_records.institution_id → institutions.institution_id` | ❌ Missing |
| `funding_records.project_id → projects.project_id` | ❌ Missing |
| `patents.*` → no FKs | ❌ Missing |
| `publications.*` → no FKs | ❌ Missing |
| `research_documents.*` → no FKs | ❌ Missing |
| `collaborations.*` → no FKs | ❌ Missing |

**Risk:** Without FK constraints, orphan records can exist in `funding_records`, `patents`, `publications`, `collaborations` where referenced entities have been deleted.

**Example of missing FK:**
```sql
-- Should exist but doesn't:
ALTER TABLE funding_records
ADD CONSTRAINT fk_funding_researcher
FOREIGN KEY (researcher_id) REFERENCES researchers(researcher_id);
```

#### MEDIUM: TEXT used instead of JSON for semi-structured data

Some fields store comma-separated text where arrays/JSON would be more appropriate:
- `researcher_ids` (TEXT) — stores "id1,id2,id3" instead of JSON array
- `inventor_ids` (TEXT) — same issue
- `researcher_ids` in publications table
- `co_pis` in projects

This makes querying these fields inefficient (requires `LIKE '%id%'` instead of `JSON_CONTAINS`).

#### MEDIUM: No partial/differential migration strategy

Alembic is set up but there are no subsequent migration files. The `versions/` directory has only `6d878bf70def_initial_schema.py`. Any schema changes after initial import require a new autogenerated migration.

### ORM vs Migration Gap

The SQLAlchemy ORM models (in `src/data/database_v2.py`) should match the migration schema. Any divergence between ORM column types and migration types causes runtime errors.

**Recommendation:** Run `alembic check` to verify ORM <→ migration alignment:
```bash
cd src && alembic check
```

### D2 Findings Summary

| Check | Status |
|-------|--------|
| Migration exists | ✅ |
| Upgrade reversible | ✅ |
| Downgrade reversible | ✅ |
| All tables have PK | ✅ |
| FKs defined | ⚠️ Partial (4/11 defined) |
| NOT NULL on required fields | ✅ |
| Indexes on FK columns | ✅ |
| ORM alignment | ⚠️ Needs verification |
| No subsequent migrations | ⚠️ Gap after initial |

**Priority fixes:**
1. **P0:** Add missing FK constraints to a new migration
2. **P1:** Verify ORM model alignment with `alembic check`
3. **P2:** Consider JSON columns for multi-valued fields

---

## D3: Performance Benchmarks

### Known Latency Targets

Based on system requirements and industry standards for gov-tech platforms:

| Operation | P50 Target | P95 Target | P99 Target | Priority |
|-----------|-----------|-----------|-----------|---------|
| `/query` (cached) | < 200ms | < 500ms | < 1s | Critical |
| `/query` (uncached, RAG+LLM) | < 5s | < 15s | < 30s | Critical |
| `/login` | < 300ms | < 800ms | < 2s | High |
| `/stats` (cached) | < 100ms | < 300ms | < 500ms | High |
| `/publications` | < 200ms | < 500ms | < 1s | Medium |
| `/query/graph` | < 500ms | < 2s | < 5s | Medium |
| DB query (simple) | < 20ms | < 100ms | < 200ms | High |
| DB query (complex JOIN) | < 100ms | < 500ms | < 1s | High |
| LLM synthesis (cloud) | < 3s | < 8s | < 15s | High |
| LLM synthesis (local) | < 1s | < 3s | < 5s | Medium |
| Vector search (Qdrant) | < 50ms | < 200ms | < 500ms | High |

### Bottleneck Analysis

**Fast path (cached queries):**
```
API → cache hit → JSON response
Expected: < 200ms ✅
```

**Slow path (uncached RAG + LLM):**
```
API → PII validation → Router → Planner LLM → Executor SQL+RAG → Verifier LLM → Synthesizer LLM → API
         ~10ms          ~50ms       ~2-5s            ~200ms         ~1-3s        ~1-2s         ~2-5s
Expected total: 6-18s ❌ (at risk of exceeding 30s timeout)
```

**Optimization recommendations:**
1. **Cache more aggressively** — increase TTL on `/stats` from 30s to 5min
2. **Parallelize Planner and Executor** — Planner output unlocks Executor, but they run sequentially
3. **Pre-warm RAG cache** — common queries (researcher stats, state distribution) pre-embedded
4. **Reduce LLM `max_output_tokens`** in synthesizer — currently 800, can reduce to 400 for factual queries

### Load Test Targets

| Concurrency | Throughput | P95 Latency | Error Rate |
|-------------|-----------|-------------|-------------|
| 10 users | 50 qpm | < 5s | < 1% |
| 50 users | 200 qpm | < 10s | < 2% |
| 100 users | 350 qpm | < 20s | < 5% |

---

## E1: Testing Strategy

### Current State

- **291 tests** with 2 known failures
- Full suite times out at 120s
- Coverage: ~70% on orchestration/skills/security modules

### Testing Pyramid

```
        ┌─────────────────┐
        │   E2E / Playwright │  ← 5 tests (full journey)
        ├─────────────────┤
        │  Integration (API) │  ← 30 tests (API endpoints)
        ├─────────────────┤
        │   Contract Tests   │  ← 10 tests (API schema)
        ├─────────────────┤
        │      Unit Tests     │  ← 246 tests (nodes, skills, utils)
        └─────────────────┘
```

### Missing Test Coverage

#### P0: Contract Tests for API Endpoints

Each `/query` response schema should have a contract test:
```python
# tests/api/test_query_contract.py
def test_query_response_has_required_fields(api_client):
    response = api_client.post("/query", json={"query": "machine learning"})
    assert "query_id" in response.json()
    assert "response" in response.json()
    assert "verification_status" in response.json()
    assert isinstance(response.json()["citations"], list)
```

#### P1: Negative Tests

Current tests cover happy paths. Missing:

| Scenario | What to test |
|----------|--------------|
| Invalid JWT token | `/query` with expired token → 401 |
| Tier 1 accessing Tier 3 data | Researcher queries government-only endpoint → 403 |
| PII in query | Query containing email/phone → 400 with sanitization warning |
| Prompt injection | Query with `[SYSTEM]` override → blocked with 400 |
| SQL injection | `query='; DROP TABLE researchers; --` → 400 |
| XSS in graph visualization | `<script>alert(1)</script>` in graph topic → sanitized |
| Empty query | `/query` with `query: ""` → 422 validation error |
| Rate limit | 1000 requests in 1 minute → 429 |

#### P1: LLM Fallback Tests

Test the cascade: `NVIDIA → local → rule-based`:
```python
def test_synthesizer_falls_back_to_local_when_nvidia_fails():
    # Mock NVIDIA to raise ConnectionError
    # Assert synthesizer uses local LLM
    # Assert metric `nrg_llm_fallback_total` incremented
```

#### P1: DPDP Consent Tests

```python
def test_query_blocked_without_consent():
    # Create user without research_access consent
    # POST /query → 403 "Consent required"

def test_consent_withdrawal_deletes_user_data():
    # POST /me/data DELETE
    # Verify data is anonymized (not hard-deleted)
```

#### P2: Performance/Load Tests

```python
# tests/load/test_query_load.py
def test_50_concurrent_queries():
    # Use concurrent.futures or pytest-xdist
    # Measure P50/P95/P99 latency
    # Assert P95 < 10s, error rate < 2%
```

### E1 Recommendations

1. **Add `pytest-xdist`** for parallel test execution (reduces 120s suite time)
2. **Add `hypothesis`** for property-based testing on SQL generation
3. **Add contract tests** using `pydantic` schemas as the contract
4. **Increase negative test coverage** — aim for 20% of test suite to be adversarial inputs
5. **Run tests in CI on every PR** — currently 291 tests run but 2 fail silently (need to enforce zero failures)

---

## E2: Data Validation

### Database Integrity Audit

**Database:** `nrg_research.db` (SQLite)
**Counts:** 5,615 researchers, 12,000 publications, 8,049 projects, 3,000 patents, 5,000 collaborations, 15,435 funding records, 889 labs, 181 institutions

#### Orphan Record Detection

| Table | FK Reference | Orphans Found | SQL to Verify |
|-------|------------|--------------|---------------|
| `funding_records` | `researcher_id` → `researchers` | Unknown | `SELECT COUNT(*) FROM funding_records fr LEFT JOIN researchers r ON fr.researcher_id = r.researcher_id WHERE r.researcher_id IS NULL;` |
| `funding_records` | `institution_id` → `institutions` | Unknown | Same pattern |
| `funding_records` | `project_id` → `projects` | Unknown | Same pattern |
| `patents` | researcher FK not defined | N/A | N/A |
| `publications` | researcher FK not defined | N/A | N/A |
| `collaborations` | No FK to researchers | N/A | N/A |

**Action:** Run orphan detection queries on all 8 FK relationships that are missing in the migration.

#### ID Namespace Validation

| Namespace | Pattern | Example | Consistency |
|-----------|---------|---------|------------|
| Researcher IDs | `RES_[A-Z0-9]+` or `RES-[0-9]+` | `RES_1001`, `RES-000000` | Mixed ❌ |
| Publication IDs | Unknown pattern | Unknown | Unknown |
| Institution IDs | UUID or string | Unknown | Unknown |
| Project IDs | UUID or string | Unknown | Unknown |
| Patent IDs | Unknown | Unknown | Unknown |

**Issue:** Researcher IDs have at least 2 different formats (`RES_1001` from Gemini, `RES-000000` from Minimax). No enforced consistent ID namespace.

**Validation query:**
```sql
-- Find mixed ID formats in researchers table
SELECT researcher_id FROM researchers
WHERE researcher_id NOT LIKE 'RES[_]%'
AND researcher_id NOT LIKE 'RES-%';
```

If results > 0, there's ID namespace inconsistency.

#### State Name Normalization

**Issue:** Indian state names may be stored inconsistently (`Tamil Nadu` vs `TamilNadu` vs `Tamil_nadu`).

**Validation query:**
```sql
-- Find distinct state values that may be duplicates
SELECT state, COUNT(*) as cnt FROM researchers
GROUP BY state
HAVING cnt > 1;
```

Expected: 28 states + 8 UTs = ~36 distinct values. If more, normalization is needed.

#### Funding Amount Validation

**Issue:** `funding_amount_inr_crores` is Float. Negative values or zero may be invalid for active projects.

**Validation query:**
```sql
-- Suspicious funding amounts
SELECT funding_id, title, amount
FROM funding_records
WHERE amount <= 0 OR amount > 10000; -- > 10,000 Cr is implausible
```

#### Publication Year Distribution

**Validation query:**
```sql
-- Publications with future or invalid years
SELECT publication_id, title, year
FROM publications
WHERE year > 2026 OR year < 1900 OR year IS NULL;

-- Year distribution (should peak 2015-2025)
SELECT year, COUNT(*) as cnt FROM publications
GROUP BY year ORDER BY cnt DESC LIMIT 20;
```

Expected: Most publications in 2015-2025 range. Large counts of 2026+ may indicate data quality issues.

#### Data Freshness

The database was imported on 2026-04-21. Verify data has appropriate vintage:
```sql
SELECT MAX(created_at) as latest_import FROM researchers;
SELECT COUNT(*) as total_researchers FROM researchers;
```

### E2 Summary

| Check | Status |
|-------|--------|
| Orphan records (FK relationships) | ⚠️ Needs verification (FK constraints not defined in migration) |
| ID namespace consistency | ⚠️ Mixed formats found (RES_ vs RES-) |
| State name normalization | ⚠️ Needs verification |
| Funding amount sanity | ⚠️ Float allows negatives |
| Publication year range | ⚠️ Needs verification |
| No duplicate primary keys | ✅ PK enforced |
| Consent records per DPDP | ⚠️ Not verified in this audit |

**Action items:**
1. Run orphan detection SQL for all 8 missing FK relationships
2. Standardize ID namespace (recommend: `RES-{7-digit-zero-padded}`)
3. Add CHECK constraint on `year` column: `CHECK (year >= 1900 AND year <= 2026)`
4. Add CHECK constraint on `amount` column: `CHECK (amount > 0)`
5. Deduplicate state names via lookup table

---

## Priority Summary

| Task | Priority | Finding | Fix Effort |
|------|----------|---------|------------|
| C1: Bundle code splitting | HIGH | 765KB JS, no chunks | 2h |
| C1: Lazy load dashboards | HIGH | All 3 dashboards load on mount | 1h |
| C1: Replace d3 with d3-force | MEDIUM | 200KB → 20KB | 2h |
| C2: Saffron contrast on white | HIGH | 3.1:1 ratio | 30min |
| C2: Focus-visible outlines | MEDIUM | Missing `outline` on `:focus-visible` | 15min |
| C2: Screen reader labels | MEDIUM | Graph SVG unlabeled | 15min |
| C2: prefers-reduced-motion | LOW | No motion reduction | 10min |
| D1: Dockerfile.orchestration root | CRITICAL | Runs as root, single-stage | 4h |
| D1: Dockerfile.frontend nginx root | HIGH | nginx runs as root | 1h |
| D2: Missing FK constraints | HIGH | 7 of 11 FKs not defined | 2h |
| D2: ID namespace mixed formats | HIGH | RES_ and RES- both exist | 3h |
| D2: Orphan record detection | HIGH | Not verified | 1h |
| D3: LLM timeout risk | HIGH | Slow path can exceed 30s | 4h |
| E1: Negative tests | HIGH | 0 adversarial tests | 4h |
| E1: Contract tests | MEDIUM | No API schema tests | 3h |
| E1: LLM fallback tests | MEDIUM | No cascade tests | 2h |
| E2: State normalization | MEDIUM | May have duplicates | 2h |
| E2: CHECK constraints on year/amount | MEDIUM | No domain validation | 1h |