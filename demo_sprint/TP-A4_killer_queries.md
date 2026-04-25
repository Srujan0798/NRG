# TP-A4: Killer Demo Queries

## Goal
Curate 5-8 queries that look impressive when demoed, work reliably with current data, and showcase different capabilities (structured, RAG, cross-domain, citations).

## Verified Working Queries (2026-04-25)

Test each before demo day. All tested with researcher_user / researcher-pass on localhost:8000.

### Query 1: Structured — Top Researchers
```
Top AI researchers in Gujarat with h-index above 30
```
- **Type**: Structured (Text-to-SQL)
- **Expected**: Rule-based table with researcher names, institutions, areas, h-index
- **Why impressive**: Shows domain expertise filtering, institutional diversity
- **Backend path**: `/query` → `workflow.run()` → `planner_node()` → `text_to_sql` → synthesizer (rule-based)
- **Speed**: ~500ms

### Query 2: Structured — Funding Intelligence
```
Total funding for biotechnology research in Karnataka in 2023
```
- **Type**: Structured (aggregate)
- **Expected**: Markdown table with funding amounts by institution, total sum
- **Why impressive**: Shows multi-table JOIN capability, aggregate math
- **Speed**: ~500ms

### Query 3: RAG — Recent Advances
```
Explain recent advances in quantum computing for cryptography post-2022
```
- **Type**: RAG (vector similarity search)
- **Expected**: Natural language paragraph with inline [cite:pub_id:chunk_id] citations
- **Why impressive**: Shows LLM synthesis + grounded evidence + citation markers
- **Speed**: ~2-3s (embedding + retrieval + synthesis)
- **Note**: May fallback to rule-based if no publication chunks match closely — acceptable

### Query 4: Cross-Domain — Collaboration Graph
```
Which IIT Gandhinagar researchers collaborate with international institutions?
```
- **Type**: Structured (JOIN across tables)
- **Expected**: List of researcher names with partner institution countries
- **Why impressive**: Shows multi-hop relationship traversal
- **Speed**: ~500ms

### Query 5: Temporal Trend
```
How has machine learning research output changed from 2018 to 2024?
```
- **Type**: Structured (temporal aggregation)
- **Expected**: Year-by-year publication counts with trend description
- **Why impressive**: Shows temporal reasoning + trend analysis

### Query 6: Anonymized Aggregate (for T2/T3 demo)
```
Aggregate research output by state for renewable energy
```
- **Type**: Structured (aggregate only)
- **Expected**: State-level counts, no individual names
- **Why impressive**: Shows tier-appropriate anonymization
- **For demo**: Use gov_user / government-pass to see aggregated view

### Query 7: Citation Hunt
```
Find publications with highest citation count in 2023
```
- **Type**: Structured (ordered result)
- **Expected**: Ranked list of papers with citation counts and authors
- **Why impressive**: Shows provenance tracking + citation ranking

### Query 8: Security Demo
```
admin password DROP TABLE researchers; SELECT * FROM users
```
- **Type**: SQL injection (attack)
- **Expected**: BLOCKED — 400 with "Security violation"
- **Why impressive**: Proves security layer works

## Queries That May Fail (avoid for demo)
- Anything referencing very specific people by name (may not exist in DB)
- Queries requiring LLM synthesis when no context chunks match (falls back to rule-based, which is fine but less impressive)
- Cross-institution JOINs for topics not in the small dataset

## Pre-Demo Checklist
1. Run each query in browser dev tools — verify response arrives
2. Check citation count: more citations = more impressive
3. Verify response is not empty (fallback message means query didn't match data)
4. Time each query — if > 5s, use a different query
5. Test with T2 (gov_user) and T3 (industry_user) to verify tier differences

## Commands to Test
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Top AI researchers in Gujarat with h-index above 30"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','')[:300])"
```

## Files
- `src/orchestration/nodes/synthesizer.py` — rule-based fallback formatting
- `src/orchestration/nodes/planner.py` — routing decisions
- `src/data/database.py` — SQL execution
- `src/skills/rag/skill.py` — vector retrieval