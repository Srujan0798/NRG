═══════════════════════════════════════════════════════════════
TASK: LB-8 — SEMANTIC LAYER + SCHEMA-AWARE RAG FOR TEXT-TO-SQL
AGENT: backend + ml + data-architecture
PRIORITY: P0-blocker (architectural — closes "Schema Context Overload" + "Join Graph Blindness")
MILESTONE: M5b (Performance) + X1 (Schema parity CI)
QUALITY BAR: C3 (Multi-hop) + Source #2 (Dhairya 41% baseline) + Source #3 (db_struct.sql 58 tables)
RISK REGISTER: closes Risk #1 (wrong SQL on first question), Risk #17 (silent wrong answer at scale)
═══════════════════════════════════════════════════════════════

FILES:
  - src/skills/text_to_sql/semantic_layer.yaml (NEW — dbt-style join graph)
  - src/skills/text_to_sql/schema_retriever.py (NEW — top-k DDL retrieval)
  - src/skills/text_to_sql/skill.py (rewire prompt build to use retriever)
  - src/data/schema/business_term_glossary.yaml (NEW — ambiguous term → schema mapping)
  - tests/skills/test_schema_retriever.py (NEW)
  - tests/skills/test_semantic_layer.py (NEW)
  - tests/orchestration/test_join_graph_blindness.py (NEW)
  - evidence/2026-04-26/schema_rag_token_payload_proof.txt (NEW)

PROBLEM:
  Current Text-to-SQL injects the entire 58-table schema (or a static
  hand-picked subset) into every prompt. Three failure modes follow:

  1. **Schema Context Overload** — the LLM exceeds attention budget,
     loses precision in middle layers, and emits hallucinated joins.
     Dhairya 41% baseline is the visible symptom.

  2. **Join Graph Blindness** — when a query needs to traverse a
     non-semantic junction table (e.g. `publications` → `project_grant_map`
     → `funding_sources`), the LLM hallucinates a direct FK
     (`publications.funding_id`) that does not exist. SQL parses
     against neither schema; user sees `relation does not exist`
     or, worse, a confidently wrong result.

  3. **Business-term ambiguity** — "status" can mean grant status,
     TRL stage, peer-review phase, or active-funding stage. Without a
     glossary, the LLM picks one and ships a wrong answer with full
     citation.

  Prompt-hardening (LB-2) and anomaly detection (LB-7) are necessary
  but not sufficient — they react to the LLM's output. A semantic
  layer prevents the LLM from ever seeing the wrong context in the
  first place.

ACTION:
  Phase 1 — FORTIFY (semantic layer + retriever):
    1a. Build `src/skills/text_to_sql/semantic_layer.yaml`. dbt-style.
        For every table-pair that requires traversal through a junction,
        encode the canonical join graph with table names, FK columns,
        and any required filters. Example structure:
          publications:
            related_to:
              funding_sources:
                via: [project_grant_map, project_publication_map]
                on:
                  - publications.id = project_publication_map.publication_id
                  - project_publication_map.project_id = project_grant_map.project_id
                  - project_grant_map.grant_id = funding_sources.id
        Cover at minimum the 12 join-graphs from the killer_queries.yaml
        corpus (KILLER + ADV-1..21).

    1b. Build `src/data/schema/business_term_glossary.yaml`. Maps
        ambiguous business terms → schema columns:
          status:
            grant_status: innovation_grant_from_govt.grant_status
            trl_stage: innovations_at_various_stages_of_technology_readiness_level.stage_of_technology
            peer_review_phase: advance_search_data.review_phase
        Glossary is consulted at planner time; if the user query uses an
        ambiguous term and the planner cannot disambiguate from context,
        it triggers the LB-7 `low_clarify` path and asks the user.

    1c. Build `src/skills/text_to_sql/schema_retriever.py`. At prompt-build
        time:
          - Vectorise `db_struct.sql` DDL per-table (one chunk per table
            including columns, FKs, comments). Use bge-m3 to match the
            embedding model used by the rest of the stack.
          - Embed the user question + planner output.
          - Retrieve top-K=5 most relevant tables.
          - Resolve transitive joins via the semantic_layer.yaml graph
            and append any junction tables in the path.
          - The final prompt receives ≤ 8 tables, never the full 58.

  Phase 2 — ELEVATE (integration + verification):
    2a. Rewire `src/skills/text_to_sql/skill.py` to call
        `schema_retriever.get_relevant_ddl(question, planner_output)`
        instead of injecting the static schema blob.
    2b. Log the exact token payload sent to the LLM for every query.
        Audit-bind it. Operators can spot prompts that drift toward the
        full 58-table dump.
    2c. Wire the glossary into the planner. When the planner cannot
        bind an ambiguous term, it must emit a clarification request
        (LB-7 `low_clarify`), not guess.

  Phase 3 — IMMORTALIZE:
    3a. `tests/orchestration/test_join_graph_blindness.py`: 20+ cases
        from killer_queries.yaml that REQUIRE traversal through a
        junction table. Each must succeed via the semantic layer and
        fail (or pre-cache miss) without it.
    3b. Schema retriever has its own benchmark: given a corpus of 50
        questions + ground-truth relevant tables, achieve recall@5 ≥
        90%. Fail CI on regression.
    3c. Add a watch on the average prompt token count. If average >
        1500 tokens (suggesting the retriever started over-shooting),
        page on-call.

SKILLS TO USE:
  - /prompt-engineering-patterns — schema retrieval, structured output, glossary design
  - /python-backend — async retrieval, embedding cache, dbt-style YAML loader
  - /system-design — semantic-layer pattern, join-graph algebra
  - /testing-strategy — recall@k benchmark, CI gating
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] semantic_layer.yaml covers ≥ 12 join graphs spanning the 58 tables.
  - [ ] business_term_glossary.yaml covers ≥ 30 ambiguous terms (status,
        score, ranking, level, type, output, intake, capacity, etc.)
  - [ ] schema_retriever recall@5 ≥ 90% on the 50-question benchmark.
  - [ ] Avg LLM prompt token count for /query drops by ≥ 60% vs current.
  - [ ] tests/orchestration/test_join_graph_blindness.py: 20+ cases
        succeed; each result includes `cite:` to the junction-table row.
  - [ ] Dhairya 17/17 still PASS via the production planner→retriever→
        text_to_sql path (NOT via fixture pinning).
  - [ ] 70/70 ADV-1..20 pass via the same path.
  - [ ] Quality Bar Constraint #3 score: 9+/10 with semantic-layer
        evidence file attached.
  - [ ] Cost impact: token-count reduction documented; ₹/1k queries
        delta reported.

BEFORE COMMIT:
  - /pre-commit + /code-review-and-quality

GURU ASSIGNMENT NOTE:
  Three independent external reviews (Grok, Cowrk, Principal Auditor)
  all converged on the same diagnosis: NRG exposes the LLM directly
  to a 58-table schema and hopes for the best. Dhairya's 41% is the
  visible symptom; the cause is missing architecture between the LLM
  and the database. A semantic layer + schema RAG is the standard
  pattern for this exact problem (dbt, Denodo, Cube.dev all solve
  the same way). Build it once, build it right, and the pipeline
  stops being a brittle wrapper and becomes a real engine.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md, production_only.md
  - Read docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md (Source #2) — every
    failure pattern is a join-graph or business-term ambiguity case
  - Read db_struct.sql (Source #3) end-to-end; map junction tables
  - Read tests/benchmarks/killer_queries.yaml — the 12+ join graphs
    you must encode in semantic_layer.yaml
  - Read .claude/QUALITY_BAR.md C3 + Live Evidence Requirement
  - Read every SKILL.md listed
  - Fortify → Elevate → Immortalize
  - /pre-commit before commit

DEPENDS ON: LB-6 (schema parity 58 tables) — semantic layer can only
            map joins that exist in the migration
BLOCKS: production launch, Phase 6 (#29 training data), all future
        text-to-sql work
═══════════════════════════════════════════════════════════════
