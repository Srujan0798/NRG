# NRG Eternal Execution Protocol - 2026-04-30

**Status:** Active execution protocol
**Purpose:** Give every agent one current, honest operating plan for taking NRG from the present local state to a professor/assistant-ready production path.
**Authority:** This document supersedes broad phase dumps and stale launch-ready claims. It must stay aligned with `Core_Idea_Clean.md`, `.claude/CURRENT_STATE.md`, and the latest evidence folder.
**Current priority:** Deployment-grade proof after local C4 hot-path closure. No more broad cleanup unless a dead file blocks the product path.

---

## 1. Product Truth

NRG is a sovereign research answer engine, not a chatbot and not just a dashboard.

The core user story is:

1. A real user logs in as Researcher, Government, or Industry.
2. They type a natural-language research question, including messy wording.
3. NRG decides whether the question needs SQL, RAG, hybrid retrieval, or a clarifying question.
4. NRG retrieves bounded evidence from the local research data layer.
5. NRG returns a readable answer with citations, source rows, confidence, and an audit event ID.
6. The visible UI lets the user inspect source data and audit proof without confusion.
7. Tier policy changes what the user can see without leaking restricted data.

Everything agents build must serve that path.

---

## 2. Current Truth Snapshot

This section must be updated whenever a major wave finishes.

| Item | Current truth |
| --- | --- |
| Current HEAD when this protocol was rewritten | `9e93adf` |
| Working tree | Not clean; there are active uncommitted code, evidence, docs, and skill-directory changes. Agents must run `git status --short` before editing. |
| Main quality status | C1, C2, C3, C5, C6 have passed in targeted evidence. C4 local 100-user smoke now passes; cluster proof remains open. |
| C4 latest honest evidence | `evidence/2026-04-30/c4_read_model_singleflight_closure.md` |
| Best latest local C4 run | `live_c4_local_smoke_after_read_model_final`: 8522 requests, 0 failures, aggregate P99 313.2ms, `/query` P99 170ms. |
| C4 target | Strict target remains P99 < 500ms for analytical query path under production load; final proof requires the 1000-user cluster run. |
| Audit chain after concurrent run | Healthy after the final local C4 run and targeted tests: `chain_valid=True`, `chain_length=42085`, `error_count=0`. |
| Current blocker | Deployment-grade 1000-user cluster proof, deployed replay, production Qdrant baseline, and founder signing remain external gates. |
| Product stance | Locally show-ready, not production-ready. |

Never claim "launch ready" or "production ready" from local-only evidence.

---

## 3. Mandatory First Reads

Every agent must read these before editing:

1. `.claude/CLAUDE.md`
2. `.claude/CURRENT_STATE.md`
3. `Core_Idea_Clean.md`
4. This protocol
5. The assigned prompt stone in `prompts_hybrid/`
6. Latest relevant evidence in `evidence/2026-04-30/`

Task-specific must-reads:

| Task type | Must read |
| --- | --- |
| Query correctness | `src/api/main.py`, `src/api/query_helpers.py` if present, `src/orchestration/`, `src/skills/text_to_sql/`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |
| Performance | `tests/load/locustfile_c4.py`, `evidence/2026-04-30/c4_read_model_singleflight_closure.md`, `src/data/database_v2.py`, query fast-path/read-model code |
| Frontend main flow | `frontend/src/views/AnswerEngine.tsx`, `frontend/src/services/queryService.ts`, answer/citation/audit components |
| Security and tier | `src/security/`, `src/auth/`, `src/api/middleware/`, `tests/security/`, `tests/audit/` |
| Handover | `docs/handover/`, `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md`, live proof evidence |

---

## 4. Non-Negotiable Visible Path

The final product path is:

```text
login
-> choose/confirm persona
-> dashboard
-> ask messy real query
-> stream planning/retrieval/synthesis/verification phases
-> answer with citations and confidence
-> open source data drawer
-> inspect SQL/proof/audit event
-> switch tier or compare tier output
-> follow-up query preserves context
```

The 90-second walkthrough must show:

1. Researcher login.
2. Messy query such as `best quantum researchers....`.
3. Streaming phases.
4. Query-specific answer, not generic repeated text.
5. Citations and source rows.
6. Tier 1 versus Tier 3 difference or blocked Tier 3 request.
7. Audit event proof.
8. Mobile screenshot or narrow viewport proof.

---

## 5. Stable Response Contract

Every successful query response must expose these fields or their documented equivalent in the frontend adapter:

```json
{
  "query": "original user text",
  "response": "human-readable answer",
  "answer_id": "stable id",
  "audit_event_id": "hmac-bound audit event id",
  "sql_query": "visible SQL or null",
  "sql_results": [],
  "citations": [],
  "tier": 1,
  "query_time_ms": 123,
  "confidence": "high|medium|low",
  "verification": {
    "status": "verified|bounded|blocked|degraded",
    "reason": "short reason"
  }
}
```

Blocked responses must still be structured and must include an audit event ID when possible.

No agent may change this contract without updating backend tests, frontend adapter tests, and handover docs.

---

## 6. Query Lifecycle

The answer engine must follow this lifecycle:

1. Sanitize and preserve useful user intent, even with noisy wording or profanity.
2. Classify intent into structured SQL, unstructured RAG, hybrid, policy-blocked, or clarify.
3. Ask a clarifying question when the requested entity, time range, metric, or scope is too ambiguous to answer safely.
4. Retrieve evidence through the fastest truthful path:
   - C4 read model for known hot-path analytical shapes.
   - Text-to-SQL for structured questions not covered by read models.
   - RAG for document/source questions.
   - Hybrid when both structured and unstructured evidence are needed.
5. Verify that visible claims are grounded in returned rows/chunks.
6. Apply tier filtering before final visible answer.
7. Attach citations, source data, confidence, and audit proof.
8. Cache only tier-safe final payloads using normalized query, tier, and relevant context.

The model may phrase the answer, but it must not invent evidence.

---

## 7. Execution Waves

Run one wave per agent unless explicitly assigning an integration owner. Do not paste all prompt stones to one agent.

### Wave 0 - State Lock

**Goal:** Freeze current truth before feature edits.

**Prompt stone:** `prompts_hybrid/01_master_execution_stone.md`

**Inputs:**
- `.claude/CLAUDE.md`
- `.claude/CURRENT_STATE.md`
- `Core_Idea_Clean.md`
- `git status --short`
- latest evidence under `evidence/2026-04-30/`

**Required output:**
- Update or create `evidence/YYYY-MM-DD/00_current_state.md`.
- State which untracked files are intentional and which are unrelated.
- No feature work.

**Acceptance:**
- Current status is clear.
- C4 is marked open unless fresh C4 evidence proves otherwise.
- No unexplained untracked files are ignored.

### Wave 1 - Backend Answer Correctness

**Goal:** Messy natural-language queries route correctly and return different, relevant answers.

**Prompt stone:** `prompts_hybrid/04_backend_security_data_stone.md`

**Primary work:**
- Keep `/query` and streaming query path aligned with the lifecycle in section 6.
- Preserve useful intent from noisy user text.
- Prevent repeated generic same-answer behavior.
- Return real ranked evidence or a clarifying question for queries like `best quantum researchers....`.
- Bound out-of-corpus questions honestly.

**File ownership:**
- `src/api/`
- `src/orchestration/`
- `src/skills/text_to_sql/`
- backend query tests

**Acceptance:**
- At least 10 messy queries produce relevant distinct answers or safe clarifications.
- Every answer has citations and audit ID.
- Targeted backend tests pass.

### Wave 2 - C4 Read Model And Single-Flight Cache

**Goal:** Close the current performance blocker without weakening correctness or audit proof.

**Prompt stone:** `prompts_hybrid/06_evidence_acceptance_stone.md`

**Status:** Completed locally in `evidence/2026-04-30/c4_read_model_singleflight_closure.md`.

**Problem to solve:**
The earlier hardening pass removed several artificial bottlenecks, but the best honest 100-user run still missed C4. The follow-up fix added a read-model layer for known C4 shapes plus single-flight cache fill so concurrent misses do not all run the same expensive SQL.

**Required C4 shapes from `tests/load/locustfile_c4.py`:**
- Researcher lookup by topic and state.
- AI/robotics/renewable-energy researcher ranking.
- Publications by topic, institution, and year.
- Funding by institution, agency, year, and topic.
- State totals and state-wise research distribution.
- Institution publication counts.
- Industry partnership and collaboration opportunity queries.
- Adversarial probes blocked quickly.
- `/stats` count endpoints.

**Primary work:**
1. Define a C4 read-model surface in code:
   - Precomputed Python cache, database view, materialized view, or dedicated table is acceptable.
   - It must be clear how it is generated and refreshed.
2. Route known C4 query shapes to read-model lookups only.
3. Add single-flight cache fill by normalized query and tier.
4. Keep audit IDs real on every response.
5. Keep tier filtering after retrieval and before visible synthesis.
6. Avoid hiding dependency failure with fake `no data` responses.
7. Add regression tests that prove repeated concurrent same-query requests do not fan out into repeated slow DB work.

**File ownership:**
- `src/api/main.py`
- `src/api/query_helpers.py` if present
- `src/data/`
- `src/skills/text_to_sql/`
- `tests/api/`
- `tests/performance/` or `tests/load/`
- migrations only if a read-model table/view is added

**Do not touch:**
- Frontend layout
- Broad docs
- Unrelated cleanup

**Acceptance:**
- Targeted query tests pass.
- Audit chain verifies after a concurrent run.
- Local 100-user Locust evidence passes in `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/locust_output.txt`: 8522 requests, 0 failures, aggregate P99 313.2ms, `/query` P99 170ms.
- Remaining blocker is not local C4 smoke; it is the 1000-user cluster proof in the intended deployment environment.

### Wave 3 - Frontend Main Flow

**Goal:** The visible product feels like a serious answer engine.

**Prompt stone:** `prompts_hybrid/02_main_flow_stone.md`

**Primary work:**
- Verify login -> dashboard -> query -> streaming answer -> citations -> source data -> audit proof.
- Use one stable query adapter.
- Render no-trouble states:
  - loading
  - slow query
  - zero results
  - blocked PII
  - tier restriction
  - backend failure
  - offline/network failure
  - mobile overflow
- Show answer, confidence, citations, source rows, SQL/proof drawer, audit ID, and copy action.

**Acceptance:**
- `npm run build` passes.
- Main-flow browser test or equivalent passes.
- Desktop and mobile screenshots saved under evidence.

### Wave 4 - Security, Tier, Audit

**Goal:** Prove that working answers remain safe.

**Prompt stone:** `prompts_hybrid/05_audit_red_team_stone.md`

**Primary work:**
- Capture raw Tier 1, Tier 2, and Tier 3 JSON.
- Prove Tier 3 has no PII or small-cohort leaks.
- Prove PII and prompt injection are blocked.
- Verify allowed and blocked attempts create audit events.
- Verify HMAC chain after restart and after concurrent load.

**Acceptance:**
- Red-team report with CRITICAL/HIGH findings fixed or explicitly blocked.
- Audit verification evidence saved.
- Tier comparison evidence saved.

### Wave 5 - Production Performance And Cluster Proof

**Goal:** Close C4 with honest production-grade evidence.

**Prompt stone:** `prompts_hybrid/06_evidence_acceptance_stone.md`

**Primary work:**
- Use the completed local 100-user proof after Wave 2 as baseline.
- Profile P50/P95/P99 and failure rate.
- Run cluster 1000-user proof only when local path is stable.
- Measure API, DB, cache, audit, RAG, and frontend wait separately.

**Acceptance:**
- Local C4 is closed only for the 100-user laptop smoke target.
- Production C4 remains open until fresh 1000-user cluster evidence meets the strict target.
- If strict C4 fails, the blocker is named, measured, and assigned.

### Wave 6 - Final Handover

**Goal:** Produce professor/assistant-ready proof.

**Prompt stone:** `prompts_hybrid/07_show_readiness_handover_stone.md`

**Primary work:**
- Create 90-second walkthrough.
- Create final evidence index.
- Update handover docs after product path is proven.
- Keep claims honest.

**Acceptance:**
- One final handover report.
- Evidence paths listed.
- Known blockers clearly separated from passed gates.

---

## 8. Agent Operating Rules

1. One agent, one wave, one prompt stone.
2. Read mandatory docs before editing.
3. Run `git status --short` before editing and before final response.
4. Do not overwrite unrelated user or agent work.
5. No broad cleanup during feature work.
6. No deleting files unless import/reference search proves they are dead.
7. No feature is done without fresh command output.
8. Every agent final response must include:
   - files changed
   - tests run
   - evidence paths
   - blockers
   - commit SHA if committed
9. If changing a response contract, update backend tests and frontend adapter tests in the same wave.
10. If C4 is measured, include the exact Locust command, environment variables, and output path.

---

## 9. Quality Gates

Minimum final gate:

| Gate | Required proof |
| --- | --- |
| Backend query correctness | Targeted messy-query tests and JSON samples |
| Text-to-SQL | Dhairya/regression query tests or documented blocked gaps |
| RAG | `/health` reports honest Qdrant/RAG state; no fake no-data fallback |
| Tier safety | Raw Tier 1/2/3 JSON evidence |
| Security | PII block and prompt-injection block tests |
| Audit | Chain verify after restart and after concurrent load |
| Frontend | `npm run build`, browser proof, desktop/mobile screenshots |
| Performance | Local 100-user Locust proof; cluster 1000-user proof before production claim |
| Handover | Final evidence index and 90-second walkthrough |

---

## 10. Go/No-Go Language

Use these labels exactly:

| Label | Meaning |
| --- | --- |
| `locally show-ready` | The local user-visible path works with evidence, but production gates may remain open. |
| `C4 local closed / cluster pending` | Local 100-user smoke met the C4 target, but production-grade 1000-user cluster evidence is still missing. |
| `cluster-blocked` | Cannot be proven on laptop and needs deployed environment. |
| `production-ready` | Only allowed after all quality gates pass with fresh evidence. |
| `blocked` | A named external dependency or failing gate prevents progress. |

Forbidden claim patterns:

- Do not say `launch ready` while the 1000-user cluster C4 proof is missing.
- Do not say `production ready` from local-only evidence.
- Do not say `RAG working` unless `/health` and retrieval evidence prove it.
- Do not say `secure` without raw tier/security/audit evidence.

---

## 11. Immediate Next Assignment

Assign the next backend/performance agent this exact mission:

```text
Read:
- .claude/CLAUDE.md
- .claude/CURRENT_STATE.md
- Core_Idea_Clean.md
- docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md
- evidence/2026-04-30/c4_read_model_singleflight_closure.md
- tests/load/locustfile_c4.py

Goal:
Take the completed local C4 read-model/single-flight layer to deployment-grade proof.

Do:
1. Verify the local 100-user C4 evidence and keep it as baseline.
2. Run the same profile against the intended deployment target with production worker/logging settings.
3. Run the 1000-user cluster profile only after deployment health is stable.
4. Preserve audit-chain verification after load.
5. If the cluster run fails, name the exact bottleneck with P50/P95/P99, failures, and evidence path.
6. Write evidence under evidence/YYYY-MM-DD/.

Do not:
- Touch frontend layout.
- Perform broad cleanup.
- Claim production readiness from local-only proof.
```

---

## 12. Summary

The project direction is finalized:

- Build the real answer engine first.
- Make the visible experience trustworthy and simple.
- Prove tier safety and audit proof.
- Use the local C4 read-model/single-flight pass as baseline and close the remaining production proof with deployment load evidence.
- Only then package final handover.

The next valuable work is not another planning document. The next valuable work is Wave 5: deployed 1000-user C4 proof and final external-gate closure.
