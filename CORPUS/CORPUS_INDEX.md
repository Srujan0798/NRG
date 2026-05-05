# NRG Corpus Index

> **Read this file first.** It tells you what NRG is and what order to read the rest.

## What is NRG?

NRG (National Research Graph) is a sovereign research-intelligence platform for India. A professor types *"Who is doing the best research in hydrogen catalysis?"* — and the system figures out everything else from a 600 GB government database, without leaking a single byte.

**NRG is not a chatbot. NRG is not a search engine. NRG is the Research OS of India.**

## Reading Order

### Step 1 — Product Truth
1. `Core_Idea_Clean.md` — what NRG is, what it is not, product principles, UX contract

### Step 2 — Data Truth
2. `db_struct.sql` — canonical PostgreSQL schema (58 tables)
3. `schema/schema_hints.md` — text-to-SQL hints for every table
4. `schema/business_term_glossary.yaml` — business terms mapped to schema

### Step 3 — Quality & State
5. `quality/quality_bar.md` — 6 hard constraints (C1-C6)
6. `state/current_state.md` — what is blocked, what is in progress, what shipped
7. `state/source_of_truth_map.md` — canonical files vs mirrors

### Step 4 — Audit & Benchmarks
8. `SQL_AUDIT_REPORT_DHAIRYA.md` — formatted audit of 17 benchmark queries
9. `killer_queries.yaml` — 3 launch killer queries + 10 adversarial breakers
10. `SQL_AUDIT_RAW_dhairya.sql` — raw Dhairya audit SQL

### Step 5 — Verification Rule
11. `VERIFY.md` — **how to verify reality by scanning actual source files**

## How to Verify This Project

**CORPUS/ contains exact mirrors of canonical files + one verification rule.**

To understand the full project, an AI must:
1. Read the exact mirrors above for requirements
2. Read `VERIFY.md` for what actual source files to scan
3. Scan `src/`, `frontend/src/`, `tests/`, `docker-compose.yml`, `infrastructure/` directly
4. Verify: does source code match requirements?

## Quick Commands

```bash
# Verify corpus mirrors are in sync
python3 scripts/verify_corpus_sync.py

# Scan actual source (run from repo root)
grep -r "@router" src/api/routes/ | wc -l        # count API routes
ls src/auth/rbac.py src/auth/middleware.py        # check auth
ls src/security/pii/ src/security/egress_guard/   # check security
ls src/audit/ .audit/chain.jsonl                  # check audit
ls src/orchestration/nodes/planner.py             # check planner
ls frontend/src/App.tsx frontend/src/views/       # check frontend
find tests/ -name "test_*.py" | wc -l             # count tests
ls docker-compose.yml infrastructure/helm/        # check deployment
```

## What Is in CORPUS/

**Exact mirrors (byte-identical to canonical files):**
- `Core_Idea_Clean.md`
- `db_struct.sql`
- `killer_queries.yaml`
- `api/endpoint_matrix.md`
- `quality/quality_bar.md`
- `state/current_state.md`
- `state/source_of_truth_map.md`
- `SQL_AUDIT_REPORT_DHAIRYA.md`
- `SQL_AUDIT_RAW_dhairya.sql`
- `SQL_AUDIT_REPORT_CLEAN.md`
- `schema/*` (5 files)

**Meta files:**
- `CORPUS_INDEX.md` — this file
- `README.md` — corpus explanation
- `VERIFY.md` — verification rule and source scan commands

**What is NOT in CORPUS/:**
- No summaries of source code
- No interpreted architecture docs
- No condensed frontend/deployment descriptions
- Those live in their actual source locations: `src/`, `frontend/src/`, `infrastructure/`, etc.

## Size

~15 files. Estimated reading time: 30 minutes for mirrors + verification rule.
