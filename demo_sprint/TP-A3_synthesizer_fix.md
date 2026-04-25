# TP-A3: Synthesizer Fix

## Goal
Fix the synthesizer node to produce high-quality, well-formatted responses for demo queries — specifically ensuring the fallback (rule-based) synthesis produces clean structured output when no LLM is available.

## Current Issues (from prior session)

1. **Empty responses on no-data queries**: The synthesizer returns bare "No data found" without context or suggestions.
2. **No streaming citations**: Citations appear only in meta event, not as live tokens in the stream.
3. **Citation extraction in streaming mode**: The `_extract_citations` function was defined outside the event generator but needs to be inline or properly imported.

## Fixes Applied (2026-04-25)

### Fix 1: Empty-result suggestions
Added `_generate_search_suggestions()` in synthesizer.py that produces helpful prompts when no data is found:
```python
def _fallback_response(query, context_summary):
    suggestions = _generate_search_suggestions(query)
    if context_summary:
        return f"No new data found for '{query}'. Prior research context: {context_summary}" + suggestion_text
    return f"No data found for your query: '{query}'.{suggestion_text}"
```
Suggestion text includes:
- Broader search terms
- Partial match suggestions
- Author/institution search tips
- Related topic hints

### Fix 2: Streaming citation extraction
In `src/api/main.py` `query_stream` endpoint, citations are now extracted inline from each token as they arrive:
```python
for event in synthesizer_node_streaming(state):
    if event["event"] == "token":
        token_text = event["data"]
        yield f"data: {token_text}\n\n"
        for cite in extract_citations(token_text):
            if cite["id"] not in [c["id"] for c in streamed_citations]:
                streamed_citations.append(cite)
                yield f"event: citation\ndata: {json.dumps(cite)}\n\n"
```

### Fix 3: Phase progress indicators
SSE now emits three phase events before synthesis:
1. `phase: intent_detection` (progress 0.1) — "Analysing query"
2. `phase: retrieval` (progress 0.3) — "Fetching evidence"
3. `phase: synthesis` (progress 0.6) — "Generating response"

## Verification

```bash
# Test empty query with suggestion chips
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST "http://localhost:8000/api/query/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"xyzzy_nonexistent_topic_12345"}' --max-time 5
# Should return suggestion text with search tips
```

## Backend Dependencies
- `src/orchestration/nodes/synthesizer.py` — synthesizer_node_streaming
- `src/api/main.py` — query_stream endpoint (StreamingResponse SSE)
- `src/data/database.py` — NRGDatabase for structured queries

## Files changed (2026-04-25)
- `src/orchestration/nodes/synthesizer.py` — _generate_search_suggestions() added
- `src/api/main.py` — StreamingResponse, phase events, citation streaming