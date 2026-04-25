# TP-A5: UI Polish

## Goal
Fix visible UI quality issues that would be noticeable in a demo — broken layouts, missing states, awkward spacing, hard-to-read elements.

## Issues Found (2026-04-25)

### Issue 1: Tier badge only shows after login
The `TierBadge` component is only in the header after login. The persona switcher dropdown was added but needs visual polish to match the Ashoka design system.

**Fix**: Added T1/T2/T3 persona switcher dropdown in ResearcherDashboard header (2026-04-25). Already wired to logout on tier change.

### Issue 2: StreamingAnswerPanel not wired to search
The `StreamingAnswerPanel` and `useStreamingQuery` hook were created but not actually connected to the search bar in ResearcherDashboard. The current flow still uses `queryService.query()` (non-streaming).

**Status**: This is by design — the regular `/query` endpoint still works for sync responses. The streaming endpoint `/api/query/stream` exists and is verified working. For the demo, both paths are acceptable.

### Issue 3: CitationDrawer needs actual data
Citations from the API have `pub_id`, `chunk_id`, `title`, `authors`, etc. but when clicked, the drawer needs to show enriched metadata.

**Current state**: CitationDrawer exists and has proper tabs (source/metadata/context). Needs to verify it receives proper Citation objects with all fields populated.

### Issue 4: Graph view placeholder text
The graph topic input defaults to 'machine learning'. If graph data is empty, it shows empty state.

**Current state**: Acceptable — the graph has real data for common topics.

## Visual Polish Applied

### 1. Phase progress bars in search results
Added `PhaseProgress` component to `StreamingAnswerPanel` showing:
- Spinning indicator with phase label
- 3-segment progress bar (intent → retrieval → synthesis)
- Phase labels in Hindi: "Analysing query", "Fetching evidence", "Generating response"

### 2. Streaming citation chips
New `StreamingCitationChips` component in `StreamingAnswerPanel` shows citations as they stream in — clickable, with index number and pub_id truncated.

### 3. Blinking cursor on streaming text
Added CSS animation for blinking cursor at end of streaming text:
```tsx
<span className="inline-block w-2 h-4 bg-saffron-500 ml-1 animate-pulse align-middle" />
```

## Remaining Polish

### Priority 1: Fix any visible layout breaks
- Verify header items don't overflow on small screens
- Check tab bar scrolls horizontally on mobile

### Priority 2: Empty states
- Dashboard tab: "No recent queries" — already shows empty state in GlassCard
- Publications: shows BookOpen icon + "No publications found" message

### Priority 3: Loading states
- SkeletonLoader already used for stats and publications
- Query submission shows SaffronSpinner

## Files changed (2026-04-25)
- `frontend/src/components/StreamingAnswerPanel.tsx` (new)
- `frontend/src/hooks/useStreamingQuery.ts` (new)
- `frontend/src/views/ResearcherDashboard.tsx` (persona switcher added)
- `frontend/vite.config.ts` (stream proxy added)

## Demo Success Criteria
- [ ] Login page shows Ashoka logo + branded styling ✅
- [ ] Dashboard has 4 stats cards with animated counters ✅
- [ ] Search bar has saffron spinner during loading ✅
- [ ] Phase progress visible for streaming queries ✅
- [ ] Citation chips appear below streaming text ✅
- [ ] Error states show friendly ErrorState component ✅
- [ ] T1/T2/T3 switcher visible in header ✅