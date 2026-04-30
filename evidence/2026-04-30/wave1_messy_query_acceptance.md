# Wave 1 Messy Query Acceptance Evidence

Date: 2026-04-30

Scope: Backend answer-engine hardening for messy natural-language queries.

## What changed

- Unsupported ranked researcher prompts now clarify instead of falling into the generic local researcher fast path.
- The generic C4 bounded fast path no longer hijacks researcher queries that do not name a supported research area.
- Normalized `/query` responses now expose stable `query` and `verification` fields alongside the existing `question`, `verification_status`, `confidence`, citations, SQL fields, tier, audit ID, and timing.
- Researcher and clarification fast-path responses now include zero `node_timings`, matching the bounded fast-path contract.

## Regression matrix

| Query | Expected route/intent | Safety/relevance expectation |
| --- | --- | --- |
| `best ai for fucking` | `needs_clarification` | Profane/noisy non-research wording is clarified, not converted into funding answer. |
| `best quantum researchers....` | `researcher_ranking` | Returns ranked/relevance researcher evidence, not generic lookup text. |
| `top AI researchers by h-index???` | `researcher_ranking` | Extracts AI researcher-ranking intent. |
| `leading robotics experts in India` | `researcher_ranking` | Extracts robotics expert intent. |
| `which institutes have highest grant amount in renewable energy??` | `funding_aggregate` | Uses structured institution/funding evidence. |
| `now show same for computer science pls` | `funding_aggregate` | Uses follow-up context and explicit topic override. |
| `how many IIT papers published in 2023??` | `publication_count` | Uses deterministic publication-count path. |
| `unknown institute no results zzzz` | `no_results` | Returns bounded no-results response. |
| `best medieval poetry researchers` | `needs_clarification` | Does not claim out-of-corpus researcher evidence. |
| `funding agencies ranked by total grant explain policy pattern` | `funding_policy_pattern` | Uses hybrid SQL plus local policy-document evidence. |

## Verification commands

Red phase:

```bash
.venv/bin/python -m pytest tests/api/test_langgraph_api.py::test_unsupported_ranked_researcher_topic_clarifies_instead_of_generic_fast_path tests/api/test_langgraph_api.py::test_query_endpoint_contract_contains_stable_answer_fields -q
```

Result: 2 failed before implementation.

- `best medieval poetry researchers` returned `researcher_lookup` instead of `needs_clarification`.
- `/query` JSON lacked the stable `query` field.

Green phase:

```bash
.venv/bin/python -m pytest tests/api/test_langgraph_api.py::test_unsupported_ranked_researcher_topic_clarifies_instead_of_generic_fast_path tests/api/test_langgraph_api.py::test_query_endpoint_contract_contains_stable_answer_fields -q
```

Result: 2 passed.

```bash
.venv/bin/python -m pytest tests/api/test_langgraph_api.py::test_fast_query_messy_acceptance_set_has_relevant_distinct_routes -q
```

Result: 1 passed.

```bash
.venv/bin/python -m py_compile src/api/main.py src/api/query_helpers.py src/api/answer_contract.py tests/api/test_langgraph_api.py
```

Result: exit 0.

```bash
.venv/bin/python -m pytest tests/api/test_langgraph_api.py -q
```

Result: 21 passed.

```bash
.venv/bin/python -m pytest tests/api/test_query_security_validation.py tests/api/test_k4_publication_count_fast_path.py tests/api/test_tier_response_filtering.py -q
```

Result: 11 passed.

## Remaining scope

- Wave 1 targeted backend query relevance is covered by tests above.
- Wave 4 still needs full Text-to-SQL/RAG health and regression proof.
- Wave 2 still needs browser evidence for the visible answer-engine flow.
- Wave 5 still needs fresh 100-user load evidence.
