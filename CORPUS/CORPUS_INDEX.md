# NRG Corpus Index

> **Read this file first.** It tells you what NRG is and what order to read the rest.

## What is NRG?

NRG (National Research Graph) is a sovereign research-intelligence platform for India. A professor types *"Who is doing the best research in hydrogen catalysis?"* — and the system figures out everything else from a 600 GB government database, without leaking a single byte.

**NRG is not a chatbot. NRG is not a search engine. NRG is the Research OS of India.**

## Reading Order for AI Agents

Read these in order. Do not skip.

### Step 1 — Product Truth (5 min)
1. `Core_Idea_Clean.md` — what NRG is, what it is not, product principles, UX contract

### Step 2 — Data Truth (10 min)
2. `db_struct.sql` — canonical PostgreSQL schema (58 tables)
3. `schema/schema_hints.md` — text-to-SQL hints for every table
4. `schema/business_term_glossary.yaml` — business terms mapped to schema

### Step 3 — Quality & State (5 min)
5. `quality/quality_bar.md` — 6 hard constraints (C1-C6). Every task must satisfy these.
6. `state/current_state.md` — what is blocked, what is in progress, what shipped

### Step 4 — Audit & Benchmarks (10 min)
7. `SQL_AUDIT_REPORT_DHAIRYA.md` — formatted audit of 17 benchmark queries (41% baseline)
8. `killer_queries.yaml` — 3 launch killer queries + 10 adversarial breakers
9. `SQL_AUDIT_RAW_dhairya.sql` — raw Dhairya audit SQL

### Step 5 — Architecture (10 min)
10. `architecture/system_overview.md` — how backend, frontend, infra fit together
11. `architecture/data_pipeline.md` — ingestion → storage → query → answer flow
12. `architecture/security_model.md` — auth tiers, DPDP, PII, audit chain

### Step 6 — API & Frontend (10 min)
13. `api/endpoint_matrix.md` — every FastAPI endpoint, method, auth guard
14. `api/auth_flow.md` — JWT, 3 tiers, login/logout
15. `frontend/structure.md` — pages, components, routing, key files
16. `frontend/design_system.md` — design tokens, component library

### Step 7 — Operations (5 min)
17. `tech_stack.md` — what tech is used where, versions
18. `deployment/docker_compose.md` — services, ports, env vars
19. `deployment/infrastructure.md` — K8s, nginx, kong, grafana, prometheus
20. `quality/testing_strategy.md` — test structure, how to run, key commands

### Step 8 — Source Map (2 min)
21. `state/source_of_truth_map.md` — canonical files vs mirrors, what overrides what

## Quick Commands

```bash
# Verify corpus is in sync with canonical files
python3 scripts/verify_corpus_sync.py

# Run all tests
.venv/bin/python -m pytest tests/ -q --tb=short

# Start stack
bash scripts/run_critical_path_final.sh

# Check quality bar
.venv/bin/python scripts/quality_bar_scorecard.py
```

## Corpus Mirror Rule

`CORPUS/` is a portable AI handoff pack. Canonical files live in their normal repo locations. Before trusting `CORPUS/`, run `scripts/verify_corpus_sync.py`. If it says `ok: true`, the mirrors match.
