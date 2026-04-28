# 6-Node Pipeline Contracts

These JSON Schema contracts define the payload expected on each LangGraph edge.

| Edge | Version | Required Fields | Schema |
| --- | --- | --- | --- |
| `receiver_to_planner` | `1.0.0` | `query_id`, `session_id`, `user_query`, `user_tier`, `conversation_history`, `created_at` | `receiver_to_planner.schema.json` |
| `planner_to_router` | `1.0.0` | `query_id`, `session_id`, `user_query`, `user_tier`, `conversation_history`, `plan`, `planner_metadata` | `planner_to_router.schema.json` |
| `router_to_executor` | `1.0.0` | `query_id`, `session_id`, `user_query`, `user_tier`, `plan`, `intent`, `routing_decision`, `routing_confidence`, `routing_rationale` | `router_to_executor.schema.json` |
| `executor_to_synthesizer` | `1.0.0` | `query_id`, `session_id`, `user_query`, `user_tier`, `routing_decision`, `sql_results`, `retrieved_chunks`, `retrieval_metadata`, `errors`, `warnings`, `retrieval_sources`, `execution_time_ms` | `executor_to_synthesizer.schema.json` |
| `synthesizer_to_verifier` | `1.0.0` | `query_id`, `session_id`, `user_query`, `user_tier`, `synthesized_response`, `citations`, `verification_status`, `context_summary`, `provenance`, `synthesis_method` | `synthesizer_to_verifier.schema.json` |

## receiver_to_planner

Payload emitted by receiver and consumed by planner. It establishes query identity, session identity, user query text, tier, and conversation context.


## planner_to_router

Payload emitted by planner and consumed by router. It adds a query plan with desired skills, schema tables, output shape, DAG metadata, and planner provenance.


## router_to_executor

Payload emitted by router and consumed by executor. It fixes the routing decision, confidence, rationale, ambiguity metadata, and complexity tier for skill execution.


## executor_to_synthesizer

Payload emitted by executor and consumed by synthesizer. It carries structured SQL evidence, retrieved chunks, retrieval metadata, warnings, errors, and execution timings.


## synthesizer_to_verifier

Payload emitted by synthesizer and consumed by verifier. It carries the natural-language response, citations, provenance, synthesis method, and evidence used for faithfulness checks.
