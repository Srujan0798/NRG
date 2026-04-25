# Prompt Engineering Patterns Audit

**Skill**: `prompt-engineering-patterns`
**Date**: 2026-04-25
**Analyst**: Eternal Shishya
**Evidence File**: `evidence/20_PROMPT_ENGINEERING.md`

---

## System Prompts Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| `src/prompts/synth_system.md` | 153 | Synthesis — SQL+RAG → tier-appropriate responses |
| `src/prompts/planner_system.md` | 133 | Planner — query decomposition + retrieval routing |
| `src/prompts/verifier_system.md` | 172 | Verifier — citation faithfulness + security gate |
| `src/prompts/synth_system_local.md` | ? | Local SLM synthesis |

---

## Overall Assessment

**Above average for a production system.** Clear roles, explicit tier rules, security checklists, structured outputs, naturalness guidelines. The `verifier_system.md` is particularly strong with its adversarial design.

**Missing according to the skill**:
1. **Few-shot examples** — no dynamically selected input-output demonstrations
2. **Chain-of-thought** — no reasoning step elicitation for complex queries
3. **Self-verification** — no output quality self-check in synth
4. **Prompt caching** — same system prompt re-sent every request (critical — see below)

---

## synth_system.md (153 lines)

### Strengths

**Tier Access Table** (lines 18-26) — explicit, tabular, unambiguous. Excellent.

**Citation Rules** (lines 30-56) — precise format `[cite:evidence_id:chunk_index]`, 4-step insufficient evidence protocol, explicit "never fabricate" rule. Excellent.

**Naturalness Examples** (lines 70-80) — shows real example output, not just rules. Good.

**Security Checklist** (lines 140-146) — checklist before every response. Excellent.

### Gaps

**Gap 1: No Few-Shot Examples**

The skill says: *"Examples are more effective than descriptions."*

The prompt shows example OUTPUT (lines 70-80) but not INPUT→OUTPUT pairs. The model is told what to do without seeing worked examples.

**Recommendation** — Add 4 few-shot examples as `{Input, Output}` pairs:
```
Example 1 (count query):
Input: "How many publications do IIT Gandhinagar researchers have?"
Output: "IIT Gandhinagar researchers have published 847 papers in total [cite:sql_res_0:0]. Confidence: medium (data covers 2020-2024 only)."
[cite:sql_res_0:0] = {"count": 847}

Example 2 (low confidence):
Input: "What are the latest advances in quantum computing?"
Output: "The available evidence does not support specific recent advances in quantum computing... Data limitation: RAG chunks do not cover publications after 2023. Confidence: low."

Example 3 (tier-3 anonymized):
Input: "Show me AI researchers in Karnataka" [as Tier 3 user]
Output: "Karnataka has 847 AI researchers across 32 institutions [cite:sql_res_0:0]. Individual names are not available at your access level."
```

**Gap 2: No Chain-of-Thought for Complex Queries**

The skill recommends: *"Zero-shot CoT with 'Let's think step by step.'"*

For multi-hop queries (e.g., "Compare Gujarat and Karnataka's AI output and show the funding gap"), the model should reason through steps before generating the response.

**Recommendation** — Add to MANDATE section:
```
For complex multi-part questions, reason through these steps before writing the response:
1. Identify what each part of the question asks
2. Determine which evidence is relevant for each part
3. Note what can be supported vs. what needs caveats
4. Construct the response, surfacing uncertainty where evidence is weak
```

**Gap 3: No Self-Verification Before Output**

The security checklist is good but there's no quality self-check (does the response actually answer the user's question?).

**Recommendation** — Add after the security checklist:
```
Before finalizing, verify:
1. Does the response directly answer the user's specific question?
2. Are all factual claims supported by cited evidence?
3. Is the tier level correct for this user's access?
4. Is uncertainty surfaced where evidence is weak or missing?
5. Does it sound like a research assistant, not a template?
```

**Gap 4: 800 Token Limit Mentioned in Code, Not Prompt**

The `synthesizer.py` has `max_output_tokens: 800` hardcoded, but the prompt never tells the model about length constraints. The skill says: *"Be specific about output constraints."*

**Recommendation** — Add to OUTPUT FORMAT section:
```
Keep responses under 500 words. If the response would exceed this, add a 1-paragraph summary at the top, then continue with details.
```

---

## planner_system.md (133 lines)

### Strengths

**Ambiguity Resolution Table** (lines 37-46) — "best" → "Most publications in last 5 years", "recent" → "Last 3 years (2022–2025)". Excellent — removes need for clarifying questions.

**Retrieval Strategy Table** (lines 48-58) — `sql` vs `rag` vs `sql+rag` routing with rationale. Clear and correct.

**Good vs Bad Decomposition Examples** (lines 91-133) — shows actual working decompositions and their JSON output. Best practice.

**"Never Ask Clarifying Questions" Rule** (line 8) — correct design for a voice-first assistant.

### Gaps

**Gap 1: No Working JSON Examples for Parser**

The planner returns strict JSON (no markdown fences, no preamble), but the prompt doesn't show a single fully-parsed JSON example that has actually worked. The skill says: *"Constructing effective demonstrations with input-output pairs."*

**Recommendation** — Add 3 fully worked examples with the exact JSON the system expects to parse:
```json
// Fully worked example
{
  "subqueries": ["..."],
  "schema_tables": ["..."],
  "desired_skills": ["..."],
  "expected_output_shape": "...",
  "assumptions": ["..."]
}
```

**Gap 2: Schema Table References Are Incomplete**

The prompt references: `researchers`, `publications`, `projects`, `patents`, `collaborations`, `labs`, `institutions`.

But `db_struct.sql` has **58 tables**, and `planner.py:48-74` has a much more complete `TABLE_TO_DOMAIN` mapping including `innovation_grant_from_govt`, `academic_courses_details`, `combined_ipo_patent_data`, `incubation_details`, etc.

The planner is routing queries but doesn't know all the available tables.

**Recommendation**: Dynamically generate the table list from the schema extractor and inject it into the prompt, or reference `src/data/schema/schema_hints.md` as the authoritative table list.

**Gap 3: No Chain-of-Thought for Multi-Hop**

For "Compare Gujarat and Karnataka's AI research and show the funding gap" — this requires 4+ sub-queries across different tables. The planner should reason before outputting JSON.

**Recommendation** — Add:
```
For complex multi-hop questions:
1. Identify all entities in the question
2. Determine which sub-queries can run in parallel vs. must chain
3. Check which tables contain the relevant data
4. Then output the JSON
```

---

## verifier_system.md (172 lines)

### Assessment: Strongest Prompt in the System

The verifier is **adversarial by design** (line 14: *"Flag first, trust never"*) and has:

- Claim-specific support check with evidence ID lookup
- Citation completeness enforcement
- Evidence exhaustion checking (all required chunks cited)
- Tier security enforcement with violation type table
- Numerical accuracy checks ("Top 5" must have exactly 5 items)

This is a **well-engineered quality gate**. The only gaps are the same as others:

**Gap 1**: No few-shot examples of verification failures (showing what a "partially supported" claim looks like)

**Gap 2**: No chain-of-thought for ambiguous cases

---

## Cross-Cutting Issue: No Prompt Caching

**This is the most impactful missing pattern.**

All three prompts (synth, planner, verifier) are re-sent **in full** on every request. The synth_system prompt includes:
- Role definition (5 lines)
- Tier access rules (table, 6 lines)
- Citation rules (30 lines)
- Naturalness rules (40 lines)
- Response structure (40 lines)
- Confidence indicator (10 lines)
- Security checklist (8 lines)
- Output format (10 lines)

**Total: ~153 lines of system prompt, sent on every single request.**

The skill's **Prompt Caching** section says: *"Use `cache_control: {type: 'ephemeral'}` on system prompt."*

For NRG's Anthropic integration, the system prompt (especially the schema hints + RBAC rules) changes rarely. Implementing prompt caching here would:
1. Reduce input token costs by ~80% for the system prompt
2. Improve latency (cached prompts don't count against input token billing)
3. Reduce hallucination risk (stable system prompt = consistent behavior)

**This should be the #1 priority for prompt optimization.**

---

## Token Budget: `max_output_tokens: 800` Is Too Low

`synthesizer.py:52`:
```python
TOKEN_BUDGET_CONFIG = {
    "max_input_tokens": 4000,
    "max_output_tokens": 800,  # ← too low for complex synthesis
}
```

For complex queries generating multi-paragraph responses with citations, 800 tokens is extremely limiting. The skill says: *"Don't lowball `max_tokens`."*

**Recommendation**: Increase to `max_output_tokens: 4096` and use streaming to handle the longer response.

---

## Summary Table

| Prompt | Strength | Gap |
|--------|----------|-----|
| synth_system.md | Tier rules, citation rules, security checklist | No few-shot, no CoT, no self-verification, 800 token cap |
| planner_system.md | Ambiguity resolution, routing table, good/bad examples | No parsed JSON examples, schema refs incomplete |
| verifier_system.md | Adversarial design, claim-level verification, tier enforcement | No few-shot verification failures |

---

## Priority Recommendations

| Priority | Action | Impact |
|----------|--------|--------|
| **#1** | Implement prompt caching for system prompts | ~80% cost reduction on input tokens |
| **#2** | Add few-shot examples to synth_system.md (4 examples) | Better output quality, fewer hallucinations |
| **#3** | Increase `max_output_tokens` from 800 → 4096 | Prevent response truncation |
| **#4** | Add chain-of-thought elicitation for complex queries | Better multi-hop reasoning |
| **#5** | Update planner's table references from 7 → all 58 tables | Better query routing |

---

## References

- Skill: `.agents/skills/prompt-engineering-patterns/SKILL.md`
- Few-shot Learning: `.agents/skills/prompt-engineering-patterns/references/few-shot-learning.md`
- Chain-of Thought: `.agents/skills/prompt-engineering-patterns/references/chain-of-thought.md`
- System Prompts: `.agents/skills/prompt-engineering-patterns/references/system-prompts.md`
- Prompt Templates: `.agents/skills/prompt-engineering-patterns/references/prompt-templates.md`
