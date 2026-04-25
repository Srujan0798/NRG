# TP-A3 — Synthesizer Fix: Natural Language Responses

**Owner:** BACKEND  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**Reference:** `src/orchestration/nodes/synthesizer.py`

---

## Objective

Fix the synthesizer so it produces readable natural language prose instead of ASCII tables. Fix the `SovereignLLLMesh` typo. Verify the 3-tier cascade works: cloud LLM → local SLM → rule-based fallback.

---

## Current State

```
Cloud LLM mesh failed: name 'SovereignLLLMesh' is not defined
No healthy llama.cpp server; skipping HuggingFace local model
Using rule-based synthesis
```

- Responses are ASCII tables, not natural language
- `SovereignLLLMesh` has 3 L's — causes NameError
- Local LLM (`llama.cpp`) is not healthy
- Rule-based fallback is the only working path

---

## Fortify Phase (Read & Audit)

1. Read `src/orchestration/nodes/synthesizer.py` fully
2. Find where `SovereignLLLMesh` is referenced — there may be other typos
3. Check `src/config/local_llm.py` — understand the local LLM client
4. Check `src/config/llm_config.py` — understand the cloud LLM mesh
5. Run a test query and capture the current response format:
   ```bash
   curl -s -X POST http://localhost:8000/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"question":"Top 5 funding agencies"}' | python -m json.tool
   ```

---

## Elevate Phase (Fix)

### Fix 1: Fix the typo
- Find `SovereignLLLMesh` (3 L's) → change to `SovereignLLMMesh` (2 L's)
- Search entire codebase for the typo:
  ```bash
  grep -r "SovereignLLL" src/
  ```
- If the correct class name is different, use the actual class name from `src/config/llm_config.py`

### Fix 2: Improve rule-based fallback
Since local LLM is not available and cloud LLM may fail, the rule-based fallback MUST produce readable prose:
- Current: ASCII tables
- Target: Natural language paragraphs with inline citations
- Use a template-based approach:
  ```
  "Based on the data, [insight]. The top [N] [entity type] are:
   1. [Name] — [Metric]: [Value] [cite:pub_id:chunk_id]
   2. ..."
  ```
- Format numbers with Indian conventions (₹, commas, Crores)
- Include source citations in `[cite:pub_id:chunk_id]` format

### Fix 3: Verify the cascade order
The synthesizer should attempt in this order:
1. **Cloud LLM** — highest quality, requires egress guard pass
2. **Local SLM** — `llama.cpp` server, fully offline
3. **Rule-based** — deterministic, always works

Ensure the code actually tries each level before falling back. Do not skip cloud LLM attempt just because it failed once.

### Fix 4: Add synthesizer test
Write `tests/orchestration/test_synthesizer_output.py`:
- `test_synthesizer_returns_string_not_dict` — output is string
- `test_synthesizer_includes_citations` — `[cite:` pattern found
- `test_synthesizer_formats_numbers` — numbers have commas or ₹
- `test_synthesizer_not_ascii_table` — no `+----+` table art

---

## Immortalize Phase (Evidence)

1. Before/after responses:
   ```
   evidence/2026-04-25/demo_sprint/A3_synthesizer_before_after.md
   ```
   Show the same query's response before fix (ASCII table) and after fix (natural prose).

2. Test output:
   ```
   evidence/2026-04-25/demo_sprint/A3_synthesizer_tests.log
   ```
   `pytest tests/orchestration/test_synthesizer_output.py -v`

3. Typo fix evidence:
   ```
   evidence/2026-04-25/demo_sprint/A3_typo_fix.diff
   ```
   Git diff showing the `SovereignLLLMesh` → correct name change.

---

## Acceptance Criteria

- [ ] `grep -r "SovereignLLL" src/` returns 0 results
- [ ] Query response is natural language prose (not ASCII table, not raw JSON)
- [ ] Response includes citations in `[cite:pub_id:chunk_id]` format
- [ ] Numbers are formatted (₹ with commas, or Crore notation)
- [ ] `pytest tests/orchestration/test_synthesizer_output.py -v` passes 4/4
- [ ] No regressions in `pytest tests/orchestration/ -v`

---

## Rollback Plan

If synthesizer breaks completely, restore `src/orchestration/nodes/synthesizer.py` from git. The rule-based fallback should always work as a safety net.
