# Batch 5 — Orchestration / AI / RAG

Date: 2026-05-02

## Status Matrix

| Task | Status | Evidence |
|---|---|---|
| A5-01 multi-hop planner 3-hop + 4-hop | PASS | `pytest_multi_hop_planner.log` — 31 passed; added 4-hop chain coverage |
| A5-02 RAG duplicate chunks | PASS | `pytest_rag_retrieval_ingestion.log` — retriever returns 5 unique chunks and preserves chunk offsets |
| A5-03 similarity threshold calibration | PASS | `pytest_rag_retrieval_ingestion.log` — calibrated labeled scores above recall 0.85 / precision 0.80 |
| A5-04 LangGraph/DAG dead-end states | PASS | `pytest_multi_hop_planner.log` — cyclic DAG returns structured `DAGDeadEnd`, not a hang/crash |
| A5-05 malformed synthesizer output | PASS | `pytest_synth_router_retry_security.log` — malformed JSON-like LLM output falls back gracefully |
| A5-06 new document re-embedding | PASS | `live_qdrant_new_doc_ingest.log` — isolated Qdrant collection upserted and retrieved new doc at score 1.0 |
| A5-07 simple query over-classification | PASS | `pytest_multi_hop_planner.log` — simple single-hop plan has no DAG metadata and executor uses direct SQL |
| A5-08 retry backoff | PASS | `pytest_synth_router_retry_security.log` — max 3 attempts, deterministic 2^n backoff |
| A5-09 multi-source synthesis data retention | PASS | `pytest_synth_router_retry_security.log` — hybrid fallback keeps all structured rows |
| A5-10 prompt injection hardening | PASS | `pytest_synth_router_retry_security.log` — user query boundary escapes close-tags and fenced-code delimiters |
| A5-11 3-source synthesis dedupe/citation | PASS | `pytest_synth_router_retry_security.log` — duplicate document context is collapsed while all 3 source citations remain |

## Commands Run

```bash
.venv/bin/python -m py_compile src/orchestration/nodes/planner.py src/orchestration/nodes/executor.py src/skills/rag/retriever.py src/skills/rag/ingest.py src/skills/rag/ingestion.py src/orchestration/nodes/retry_handler.py src/orchestration/nodes/synthesizer.py src/skills/text_to_sql/skill.py
.venv/bin/python -m pytest tests/orchestration/test_multi_hop_planner.py -q -m slow
.venv/bin/python -m pytest tests/skills/test_rag_embedder_retriever.py tests/skills/test_rag_ingest_reranker.py -q
.venv/bin/python -m pytest tests/orchestration/test_remaining_nodes.py tests/orchestration/test_synthesizer_llm.py tests/orchestration/test_synthesizer_citations.py tests/orchestration/test_synthesizer_safety.py tests/orchestration/test_router.py tests/security/test_prompt_injection.py tests/benchmarks/test_text_to_sql_prompt_hardening.py -q
```

## Results

- Syntax check: PASS (`py_compile.log`, no output).
- Planner/DAG: 31 passed.
- RAG retrieval/ingestion/reranker: 32 passed.
- Retry/synth/router/security/prompt hardening: 92 passed, 4 deselected.
- Live local Qdrant isolated ingest: `documents=1`, `vectors_upserted=1`, `points_count=1`, retrieved `batch5-live-doc` with score `1.0`; the temporary `nrg_batch5_test` collection was deleted after verification.

## Notes

- The first plain `pytest tests/orchestration/test_multi_hop_planner.py -q` collected the file but deselected all tests because the file is marked `slow` and repo pytest defaults exclude slow tests. Final proof explicitly used `-m slow`.
- The Qdrant proof used an isolated test collection to avoid mutating the main `nrg_research` vector store.
