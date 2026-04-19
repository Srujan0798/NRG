# NRG Architecture

**Status**: Canonical architecture summary for the current PoC  
**Source of truth**: `Core_Idea_Clean.md`  
**Updated**: 2026-04-19

## Executive Decision

NRG is a sovereign research-intelligence PoC first, with a path toward a fine-tuned local model that lives inside the corpus. Phase 1 must be truthful, runnable, and deterministic before Phase 2/3 infrastructure claims are promoted.

Synthesis policy:

| Mode | Status | Boundary |
| --- | --- | --- |
| `cloud_synthesis` | Optional, explicit via `CLOUD_SYNTHESIS_ALLOWED=true` | Receives only minimized, sanitized evidence packets |
| `local_slm` | Sovereign/offline path | Receives retrieved evidence inside the deployment boundary |
| `rule_based` | Always-available fallback | Formats local SQL/RAG output without external calls |

Cloud synthesis is not allowed to receive raw database dumps, full documents, secrets, unrestricted schemas, emails, phone numbers, or other PII. Local SLM and fine-tuned local models remain the long-term sovereign endgame, not a Phase 1 blocker.

## Current Runtime Shape

```text
React dashboards
  -> FastAPI routes (/login, /query, /stats, /publications, /query/graph)
  -> LangGraph workflow
  -> SQL skill + RAG skill
  -> Synthesizer cascade: cloud-gated -> local -> rule-based
  -> Response metadata: warnings, retrieval_sources, provenance
```

## Data Boundary

Allowed external LLM payloads, only when explicitly enabled:

- User query.
- Minimal retrieved evidence packet.
- Bounded excerpts, not full documents.
- Citation/source identifiers.
- Redaction and evidence-count metadata.

Blocked external LLM payloads:

- Raw 600 GB corpus data.
- Full abstracts or full-text documents.
- Emails, phone numbers, addresses, IDs, and secrets.
- Raw SQL dumps or unrestricted schema exports.
- Generated audit/protocol artifacts.

## Retrieval And Storage

Phase 1 uses the root SQLite database by default via `DATABASE_URL=sqlite:///nrg_research.db`. Relative SQLite paths resolve from the repository root so API behavior is stable regardless of process working directory.

Qdrant configuration is explicit:

- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_COLLECTION=nrg_research`
- Vector dimension from the active embedder, not a hardcoded constant.

If Qdrant or the embedder is unavailable, the API must return structured warnings. It must not pretend that a dependency failure is a valid "no data found" result.

## Knowledge Graph Scope

Phase 1 graph views are DB-backed API responses from `/query/graph`. Neo4j is optional future work and lives under `experiments/knowledge_graph/` unless `FEATURE_KG=1` explicitly activates a future implementation.

## Security And Audit

The active PoC security baseline is:

- JWT auth and persona/tier shaping.
- Prompt sanitization and PII blocking at API boundary.
- Cloud synthesis disabled by default.
- Audit metadata for LLM calls, including cloud usage and evidence counts.
- Generated `.audit`, `.protocol`, and Playwright reports are ignored source artifacts.

## Honest Status

Working or actively wired:

- FastAPI routes for auth, query, stats, publications, and graph.
- LangGraph query flow with visible warning/provenance metadata.
- Controlled synthesis cascade with cloud gate.
- Root database path resolver through `DATABASE_URL`.

Not a current Phase 1 capability unless backed by executable tests:

- Production Kong AI Gateway enforcement.
- Neo4j traversal engine.
- Verified Qdrant population for the full corpus.
- Formal compliance attestation or benchmark claims.
- Fine-tuned local model inside the full data corpus.
