---
name: NRG Project Status
description: Current build status of National Research Graph — what's done, what's remaining, and the 3 data sources driving the project
type: project
---

## The Mission
A professor types a research question → gets verified, structured, cited answers from 600GB of national data → zero bytes leave Indian servers. Three tiers: Researcher (full), Government (aggregated), Industry (anonymized).

## Current State (as of 2026-04-23)
- 899 tests collected, 609 passing, 263 failing (test-code mismatches, not production bugs)
- Full 6-node pipeline: receiver → planner → router → executor → synthesizer → verifier
- Router: 51/51 tests green (2-stage routing, confidence thresholds, eval dataset)
- Audit chain: rebuilt, 0 errors, thread-safe, versioned, 3-tuple verify_chain
- Security: hardened (PII detection, JWT kid/aud/jti, schema fingerprint defense, column-level RBAC)
- Qdrant: 19,322 vectors, 384-dim, HNSW green
- JWT RS256 auth, refresh store, egress guard — all wired
- 6-provider LLM mesh (NVIDIA, OpenAI, Anthropic, Azure, Gemini, Minimax) + local SLM + rule-based
- Text-to-SQL: 41% accuracy baseline (Dhairya audit), agent applied schema fixes
- 39 Claude + 52 Agent skills (91 total)
- Guru Protocol active: Claude = strategy only, agents = execution

## The 3 Data Sources
1. **Core Idea** (`Core_Idea_Clean.md`) — professor's product vision, sovereignty, fine-tuning endgame
2. **Dhairya SQL Audit** (`docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`) — 17-query benchmark, 41% accuracy
3. **Official PostgreSQL Schema** (`db_struct.sql`) — 58-table production schema (our dev has only 18)

## Critical Gap
40 PostgreSQL tables missing from dev SQLite. Dhairya's queries ALL reference missing tables. Protocol #21 (Schema Bridge) addresses this.

## Active Protocols (assigned to agents)
- #19 THE TEST REALIGNMENT — fix 263 test failures
- #20 THE SQL ORACLE — SQL accuracy 41% → 85%
- #21 THE SCHEMA BRIDGE — 58-table PostgreSQL integration
- #11 THE RESILIENT MESH — LLM 270s → 15s hard cap
- #12 THE LIVING PIPELINE — observability + data ingestion

## 16 Protocols Completed
#1-#6, #8-#10, #13-#18 + Dhairya integration + framework updates

## The Endgame (Phase 4-7)
Fine-tuned local model that has internalized 1TB of data via RL loop. Current retrieval architecture becomes the precision fallback, not the primary path.

**Why:** Track across sessions. Don't re-audit what's done.
**How to apply:** Check this before any audit. Verify against code if memory is old.
