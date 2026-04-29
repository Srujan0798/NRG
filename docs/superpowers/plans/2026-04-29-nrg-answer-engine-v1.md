# NRG Answer Engine v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first general answer-engine milestone: any authorized user can ask a natural research-intelligence question and receive a verified, cited, tier-safe answer with visible proof.

**Architecture:** Consolidate existing `/query`, `/api/query/stream`, LangGraph nodes, tier response filtering, and frontend AnswerEngine surfaces around one canonical Answer Engine v1 contract. Do not create a parallel app; normalize current fast paths, workflow paths, and streaming paths into the same answer envelope and proof UI.

**Tech Stack:** FastAPI, Pydantic, LangGraph, SQLite/PostgreSQL-compatible data access, existing Text-to-SQL/RAG skills, React, TypeScript, Vite, Playwright, pytest.

---

## File Structure

Create:

- `src/api/answer_contract.py` - canonical backend response models and normalizers for Answer Engine v1.
- `src/services/answer_records.py` - append-only Answer Record persistence for query history/follow-ups.
- `tests/contract/test_answer_engine_v1_contract.py` - backend contract tests for canonical envelope.
- `tests/api/test_answer_records_api.py` - saved-answer behavior tests.
- `frontend/tests/lib/answerEngineContract.test.ts` - frontend normalization tests for new payload shape.
- `frontend/tests/e2e/answer_engine_v1_walk.spec.ts` - acceptance walk for Ask -> Answer -> Proof.

Modify:

- `src/api/routes/query.py` - return canonical envelope from normal, fast-path, blocked, and streaming paths.
- `src/api/deps.py` - align confidence labels and cache key policy with v1 contract.
- `src/orchestration/state.py` - carry assumptions, caveats, freshness, source_data, answer_id.
- `src/orchestration/nodes/planner.py` - expose inferred assumptions/defaults.
- `src/orchestration/nodes/router.py` - keep route labels compatible with `sql|rag|hybrid|clarify|blocked`.
- `src/orchestration/nodes/executor.py` - normalize SQL/RAG evidence into source-data structures.
- `src/orchestration/nodes/synthesizer.py` - write conversational answer from evidence with citation discipline.
- `src/orchestration/nodes/verifier.py` - output contract confidence and caveats.
- `src/api/response_filter.py` - preserve canonical fields while stripping forbidden nested data.
- `frontend/src/services/queryService.ts` - normalize old and new API shapes into one client type.
- `frontend/src/types/api.ts` - add Answer Engine v1 types.
- `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx` - render Ask workspace around canonical answer state.
- `frontend/src/components/StreamingAnswerPanel.tsx` - render human phases and final proof payload.
- `frontend/src/components/ProofInspector/ProofInspector.tsx` - show source, SQL/computation, freshness, and audit proof.
- `frontend/src/views/AnswerEngine.tsx` - ensure navigation and answer surfaces use the v1 contract.

Do not touch full graph, full multilingual, fine-tuning, production deployment, or external connectors in this plan.

---

### Task 1: Backend Canonical Answer Contract

**Files:**
- Create: `src/api/answer_contract.py`
- Test: `tests/contract/test_answer_engine_v1_contract.py`
- Modify: `tests/contract/test_api_response_schema.py`

- [ ] **Step 1: Write failing contract tests**

Add `tests/contract/test_answer_engine_v1_contract.py`:

```python
from src.api.answer_contract import (
    AnswerConfidence,
    AnswerEngineResponse,
    CitationRef,
    FreshnessInfo,
    SourceData,
    normalize_workflow_result,
)


def test_answer_engine_response_requires_v1_fields():
    response = AnswerEngineResponse(
        query_id="query-1",
        answer_id="answer-1",
        audit_event_id="audit-1",
        tier="researcher",
        question="Who leads hydrogen catalysis?",
        interpreted_question="Rank hydrogen catalysis researchers over the last five years.",
        assumptions=["Interpreted best as publications, citations, funded projects, and recency."],
        route="hybrid",
        final_answer="IIT-GN appears in the top cohort [1].",
        confidence=AnswerConfidence(level="high", reason="Evidence and citations passed verification."),
        citations=[CitationRef(id="1", source_type="sql_row", label="researchers row", source_id="researchers:1")],
        source_data=SourceData(sql_query="SELECT 1", rows=[{"rank": 1}], documents=[]),
        freshness=FreshnessInfo(database_snapshot=None, document_indexed_at=None, warning=None),
        caveats=[],
        follow_up_suggestions=["Change time range"],
        query_time_ms=124,
    )

    payload = response.model_dump()

    assert payload["final_answer"].startswith("IIT-GN")
    assert payload["confidence"]["level"] == "high"
    assert payload["source_data"]["rows"] == [{"rank": 1}]


def test_normalize_workflow_result_maps_legacy_fields():
    payload = normalize_workflow_result(
        question="Top funding agencies",
        tier=1,
        audit_event_id="audit-1",
        elapsed_ms=321,
        result={
            "query_id": "query-legacy",
            "session_id": "session-1",
            "synthesized_response": "DST leads by total grant amount [cite:structured:0].",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "answer_confidence": "high",
            "sql_query": "SELECT agency, SUM(amount) FROM funding GROUP BY agency",
            "sql_results": [{"agency": "DST", "total": 10}],
            "citations": [{"id": "structured:0", "title": "funding row"}],
            "warnings": [],
            "retrieval_sources": ["structured"],
        },
    )

    assert payload["query_id"] == "query-legacy"
    assert payload["route"] == "sql"
    assert payload["final_answer"].startswith("DST leads")
    assert payload["confidence"]["level"] == "high"
    assert payload["source_data"]["sql_query"].startswith("SELECT agency")
    assert payload["source_data"]["rows"] == [{"agency": "DST", "total": 10}]
```

- [ ] **Step 2: Run contract test and verify it fails**

Run:

```bash
pytest tests/contract/test_answer_engine_v1_contract.py -q
```

Expected: FAIL because `src.api.answer_contract` does not exist.

- [ ] **Step 3: Implement canonical models and normalizer**

Create `src/api/answer_contract.py`:

```python
from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

TierName = Literal["researcher", "government", "industry"]
RouteName = Literal["sql", "rag", "hybrid", "clarify", "blocked"]
ConfidenceLevel = Literal["high", "medium", "low", "needs_clarification"]
SourceType = Literal["sql_row", "document_chunk", "graph_edge"]


class AnswerConfidence(BaseModel):
    level: ConfidenceLevel
    reason: str


class CitationRef(BaseModel):
    id: str
    source_type: SourceType
    label: str
    source_id: str
    masked: bool = False


class SourceData(BaseModel):
    sql_query: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)


class FreshnessInfo(BaseModel):
    database_snapshot: str | None = None
    document_indexed_at: str | None = None
    warning: str | None = None


class AnswerEngineResponse(BaseModel):
    query_id: str
    answer_id: str
    audit_event_id: str | None
    tier: TierName
    question: str
    interpreted_question: str
    assumptions: list[str] = Field(default_factory=list)
    route: RouteName
    final_answer: str
    confidence: AnswerConfidence
    citations: list[CitationRef] = Field(default_factory=list)
    source_data: SourceData = Field(default_factory=SourceData)
    freshness: FreshnessInfo = Field(default_factory=FreshnessInfo)
    caveats: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    query_time_ms: int = 0


def tier_name(tier: int | str) -> TierName:
    value = str(tier).lower()
    if value in {"1", "researcher", "tier1", "t1"}:
        return "researcher"
    if value in {"2", "government", "gov", "tier2", "t2"}:
        return "government"
    return "industry"


def normalize_route(route: str | None, intent: str | None = None) -> RouteName:
    value = (route or intent or "").lower()
    if value in {"text_to_sql", "structured", "sql"}:
        return "sql"
    if value in {"rag", "unstructured", "vector"}:
        return "rag"
    if value in {"text_to_sql+rag", "hybrid", "sql+rag"}:
        return "hybrid"
    if value in {"clarify", "needs_clarification"}:
        return "clarify"
    if value == "blocked":
        return "blocked"
    return "hybrid" if "rag" in value and "sql" in value else "sql"


def normalize_confidence(value: Any, verification_status: Any = None) -> AnswerConfidence:
    raw = str(value or "").lower()
    if raw in {"high", "pass", "passed", "true"} or verification_status is True:
        return AnswerConfidence(level="high", reason="Evidence and citations passed verification.")
    if raw in {"medium", "partial", "warning"}:
        return AnswerConfidence(level="medium", reason="Evidence supports the answer with caveats.")
    if raw in {"needs_clarification", "low_clarify", "clarify"}:
        return AnswerConfidence(level="needs_clarification", reason="The query needs clarification before a safe full answer.")
    return AnswerConfidence(level="low", reason="Only partial evidence is available.")


def normalize_citations(raw_citations: list[Any]) -> list[CitationRef]:
    citations: list[CitationRef] = []
    for index, item in enumerate(raw_citations or [], start=1):
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id") or item.get("pub_id") or item.get("source_id") or index)
        source_type: SourceType = "document_chunk" if item.get("chunk_id") or item.get("chunk_text") else "sql_row"
        citations.append(
            CitationRef(
                id=str(index),
                source_type=source_type,
                label=str(item.get("title") or item.get("source") or f"Source {index}"),
                source_id=raw_id,
                masked=bool(item.get("masked", False)),
            )
        )
    return citations


def normalize_workflow_result(
    *,
    question: str,
    tier: int,
    audit_event_id: str | None,
    elapsed_ms: float,
    result: dict[str, Any],
) -> dict[str, Any]:
    response = AnswerEngineResponse(
        query_id=str(result.get("query_id") or uuid.uuid4()),
        answer_id=str(result.get("answer_id") or uuid.uuid4()),
        audit_event_id=audit_event_id,
        tier=tier_name(tier),
        question=question,
        interpreted_question=str(result.get("interpreted_question") or result.get("user_query") or question),
        assumptions=list(result.get("assumptions") or result.get("planner_metadata", {}).get("assumptions") or []),
        route=normalize_route(result.get("routing_decision"), result.get("intent")),
        final_answer=str(result.get("final_answer") or result.get("synthesized_response") or result.get("response") or ""),
        confidence=normalize_confidence(result.get("answer_confidence"), result.get("verification_status")),
        citations=normalize_citations(result.get("citations", [])),
        source_data=SourceData(
            sql_query=result.get("sql_query"),
            rows=list(result.get("sql_results") or []),
            documents=list(result.get("retrieved_chunks") or []),
        ),
        freshness=FreshnessInfo(**dict(result.get("freshness") or {})),
        caveats=list(result.get("caveats") or result.get("warnings") or []),
        follow_up_suggestions=list(result.get("follow_up_suggestions") or []),
        query_time_ms=int(elapsed_ms),
    )
    payload = response.model_dump()
    payload.update(
        {
            "response": payload["final_answer"],
            "status": "success",
            "tier": tier,
            "answer_confidence": payload["confidence"]["level"],
            "sql_query": payload["source_data"]["sql_query"],
            "sql_results": payload["source_data"]["rows"],
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": result.get("provenance", {}),
            "conversation_history": result.get("conversation_history", []),
            "warnings": result.get("warnings", []),
        }
    )
    return payload
```

- [ ] **Step 4: Run contract test and verify it passes**

Run:

```bash
pytest tests/contract/test_answer_engine_v1_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/answer_contract.py tests/contract/test_answer_engine_v1_contract.py tests/contract/test_api_response_schema.py
git commit -m "feat: define answer engine response contract"
```

---

### Task 2: Normalize `/query` Responses Through the Contract

**Files:**
- Modify: `src/api/routes/query.py`
- Modify: `src/api/deps.py`
- Test: `tests/api/test_langgraph_api.py`
- Test: `tests/contract/test_api_response_schema.py`

- [ ] **Step 1: Add failing API assertion for v1 fields**

Extend `tests/api/test_langgraph_api.py::test_query_endpoint_passes_session_id_to_workflow` with:

```python
        assert payload["answer_id"]
        assert payload["question"] == "Summarize sovereign readiness signals"
        assert payload["interpreted_question"]
        assert payload["route"] == "sql"
        assert payload["final_answer"] == "orchestrated answer"
        assert payload["confidence"]["level"] == "high"
        assert payload["source_data"]["sql_query"] == "SELECT name FROM researchers LIMIT 5"
        assert payload["source_data"]["rows"] == [{"name": "A. Researcher"}]
        assert "freshness" in payload
        assert "follow_up_suggestions" in payload
```

- [ ] **Step 2: Run focused API tests and verify failure**

Run:

```bash
pytest tests/api/test_langgraph_api.py::test_query_endpoint_passes_session_id_to_workflow -q
```

Expected: FAIL because `/query` does not yet return all canonical fields.

- [ ] **Step 3: Route workflow responses through `normalize_workflow_result`**

In `src/api/routes/query.py`, import:

```python
from src.api.answer_contract import normalize_workflow_result
```

Replace the manual `response_payload = { ... }` construction after workflow execution with:

```python
        response_payload = normalize_workflow_result(
            question=request.query,
            tier=user_tier,
            audit_event_id=audit_event_id,
            elapsed_ms=latency_ms,
            result={
                **result,
                "provenance": provenance,
                "synthesis_method": synthesis_method,
            },
        )
```

Keep the existing `_apply_tier_filter_to_response`, cache write, and `_remember_sql_domain_context` after normalization.

- [ ] **Step 4: Normalize fast-path responses before filtering**

For `_fast_query_response`, `_academic_follow_up_response`, `_killer_query_response`, and `_advanced_adversarial_response`, wrap the returned dict before tier filtering:

```python
            fast_response = normalize_workflow_result(
                question=request.query,
                tier=user_tier,
                audit_event_id=fast_response.get("audit_event_id"),
                elapsed_ms=0,
                result={
                    **fast_response,
                    "query_id": fast_response.get("query_id", str(uuid.uuid4())),
                    "synthesized_response": fast_response.get("response", ""),
                    "routing_decision": fast_response.get("routing_decision", "text_to_sql"),
                    "verification_status": fast_response.get("verification_status", True),
                },
            )
```

Use the same pattern for the other fast paths, preserving their audit ID and original `sql_query`.

- [ ] **Step 5: Align confidence labels**

In `src/api/deps.py`, change `_answer_confidence_from_verification` to return v1 labels:

```python
def _answer_confidence_from_verification(verification_status: Any) -> str:
    if verification_status in (True, "ok", "pass"):
        return "high"
    if verification_status == "retry":
        return "medium"
    if verification_status in ("needs_clarification", "low_clarify"):
        return "needs_clarification"
    return "low"
```

- [ ] **Step 6: Run API contract and query tests**

Run:

```bash
pytest tests/api/test_langgraph_api.py tests/contract/test_api_response_schema.py tests/contract/test_answer_engine_v1_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/api/routes/query.py src/api/deps.py tests/api/test_langgraph_api.py tests/contract/test_api_response_schema.py
git commit -m "feat: normalize query responses to answer engine contract"
```

---

### Task 3: Blocked And Unsafe Queries Use The Same Envelope

**Files:**
- Modify: `src/api/routes/query.py`
- Test: `tests/api/test_query_security_validation.py`

- [ ] **Step 1: Write failing blocked-envelope test**

Add to `tests/api/test_query_security_validation.py`:

```python
def test_pii_block_returns_answer_engine_envelope(client, auth_headers):
    response = client.post(
        "/query",
        headers=auth_headers,
        json={"query": "Show all researcher phone numbers in clean energy"},
    )

    assert response.status_code in (200, 400)
    payload = response.json()
    if "detail" in payload:
        pytest.fail(f"Blocked query returned raw detail instead of envelope: {payload}")

    assert payload["route"] == "blocked"
    assert payload["status"] == "blocked"
    assert "personal" in payload["final_answer"].lower() or "sensitive" in payload["final_answer"].lower()
    assert payload["confidence"]["level"] == "needs_clarification"
    assert payload["source_data"]["rows"] == []
```

If this file does not expose `client` and `auth_headers` fixtures, copy the login helper pattern from `tests/api/test_langgraph_api.py`.

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/api/test_query_security_validation.py -q
```

Expected: FAIL because blocked queries currently raise raw `HTTPException` detail.

- [ ] **Step 3: Add blocked response helper**

In `src/api/routes/query.py`, add:

```python
def _blocked_answer_payload(
    *,
    question: str,
    user_tier: int,
    audit_event_id: str | None,
    reason: str,
    query_id: str | None = None,
) -> dict:
    return {
        "query_id": query_id or str(uuid.uuid4()),
        "answer_id": str(uuid.uuid4()),
        "audit_event_id": audit_event_id,
        "tier": user_tier,
        "question": question,
        "interpreted_question": question,
        "assumptions": [],
        "route": "blocked",
        "final_answer": (
            "I cannot process this request because it asks for sensitive or restricted information. "
            "Try an aggregate question about institutions, labs, capability areas, or public contact routes instead."
        ),
        "response": (
            "I cannot process this request because it asks for sensitive or restricted information. "
            "Try an aggregate question about institutions, labs, capability areas, or public contact routes instead."
        ),
        "status": "blocked",
        "confidence": {"level": "needs_clarification", "reason": reason},
        "answer_confidence": "needs_clarification",
        "citations": [],
        "source_data": {"sql_query": None, "rows": [], "documents": []},
        "freshness": {"database_snapshot": None, "document_indexed_at": None, "warning": None},
        "caveats": [reason],
        "follow_up_suggestions": [
            "Show aggregate counts by institution",
            "Show labs working in this area",
            "Show public partnership routes",
        ],
        "query_time_ms": 0,
        "sql_query": None,
        "sql_results": [],
        "retrieval_sources": [],
        "warnings": [{"message": reason}],
        "conversation_history": [],
    }
```

- [ ] **Step 4: Return blocked envelope instead of raw exception for sanitizer failures**

In both `/query` and `/api/query/stream`, replace sanitizer `HTTPException(status_code=400...)` behavior for non-rate-limit security violations with the blocked envelope. Keep actual HTTP 429 for rate limits.

For `/query`, return:

```python
            blocked = _blocked_answer_payload(
                question=request.query,
                user_tier=user_tier,
                audit_event_id=None,
                reason=f"Security policy blocked this query: {validation['reason']}",
            )
            return _apply_tier_filter_to_response(blocked, user_tier, user_id, token_payload.get("kid"), getattr(raw_request.state, "request_fingerprint", None) if raw_request else None)
```

For streaming, emit `event: phase` with blocked state, then `event: meta` containing the blocked payload, then `event: done`.

- [ ] **Step 5: Run security tests**

Run:

```bash
pytest tests/api/test_query_security_validation.py tests/api/test_langgraph_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/api/routes/query.py tests/api/test_query_security_validation.py
git commit -m "feat: return safe answer envelope for blocked queries"
```

---

### Task 4: Add Answer Record Persistence

**Files:**
- Create: `src/services/answer_records.py`
- Modify: `src/api/routes/query.py`
- Test: `tests/api/test_answer_records_api.py`

- [ ] **Step 1: Write failing tests for saved answer records**

Create `tests/api/test_answer_records_api.py`:

```python
from pathlib import Path

from src.services.answer_records import AnswerRecordStore


def test_answer_record_store_round_trip(tmp_path: Path):
    store = AnswerRecordStore(tmp_path / "answers.sqlite")
    store.save(
        user_id="user-1",
        session_id="session-1",
        payload={
            "answer_id": "answer-1",
            "query_id": "query-1",
            "question": "Top funding agencies",
            "final_answer": "DST leads [1].",
            "tier": 1,
            "audit_event_id": "audit-1",
            "confidence": {"level": "high", "reason": "Verified."},
            "citations": [{"id": "1"}],
        },
    )

    rows = store.list_for_session(user_id="user-1", session_id="session-1")

    assert len(rows) == 1
    assert rows[0]["answer_id"] == "answer-1"
    assert rows[0]["payload"]["final_answer"] == "DST leads [1]."
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/api/test_answer_records_api.py -q
```

Expected: FAIL because `src.services.answer_records` does not exist.

- [ ] **Step 3: Implement SQLite-backed store**

Create `src/services/answer_records.py`:

```python
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class AnswerRecordStore:
    def __init__(self, path: str | Path | None = None):
        default_path = Path(os.getenv("NRG_ANSWER_RECORDS_DB", "data/answer_records.sqlite"))
        self.path = Path(path or default_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS answer_records (
                    answer_id TEXT PRIMARY KEY,
                    query_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    tier INTEGER,
                    audit_event_id TEXT,
                    question TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(self, *, user_id: str, session_id: str | None, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO answer_records
                (answer_id, query_id, user_id, session_id, tier, audit_event_id, question, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["answer_id"],
                    payload["query_id"],
                    user_id,
                    session_id,
                    payload.get("tier"),
                    payload.get("audit_event_id"),
                    payload.get("question", ""),
                    json.dumps(payload, default=str),
                ),
            )

    def list_for_session(self, *, user_id: str, session_id: str | None, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM answer_records
                WHERE user_id = ? AND (? IS NULL OR session_id = ?)
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, session_id, session_id, limit),
            ).fetchall()
        return [
            {
                "answer_id": row["answer_id"],
                "query_id": row["query_id"],
                "session_id": row["session_id"],
                "tier": row["tier"],
                "audit_event_id": row["audit_event_id"],
                "question": row["question"],
                "created_at": row["created_at"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]


_store: AnswerRecordStore | None = None


def get_answer_record_store() -> AnswerRecordStore:
    global _store
    if _store is None:
        _store = AnswerRecordStore()
    return _store
```

- [ ] **Step 4: Save records after response filtering**

In `src/api/routes/query.py`, import:

```python
from src.services.answer_records import get_answer_record_store
```

After tier filtering and before return/cache for successful `/query` responses:

```python
        try:
            get_answer_record_store().save(
                user_id=user_id,
                session_id=request.session_id,
                payload=response_payload,
            )
        except Exception:
            logger.warning("Answer record persistence failed", exc_info=True)
```

Do not block the query if persistence fails.

- [ ] **Step 5: Run record tests**

Run:

```bash
pytest tests/api/test_answer_records_api.py tests/api/test_langgraph_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/services/answer_records.py src/api/routes/query.py tests/api/test_answer_records_api.py
git commit -m "feat: persist answer records for query history"
```

---

### Task 5: Enrich Orchestration State With Assumptions, Caveats, Freshness, And Follow-Ups

**Files:**
- Modify: `src/orchestration/state.py`
- Modify: `src/orchestration/nodes/planner.py`
- Modify: `src/orchestration/nodes/executor.py`
- Test: `tests/orchestration/test_router.py`
- Test: `tests/orchestration/test_verifier_node.py`

- [ ] **Step 1: Add state-field test**

Add to `tests/orchestration/test_verifier_node.py`:

```python
from src.orchestration.state import NRGState


def test_nrg_state_carries_answer_engine_v1_fields():
    state = NRGState(
        user_query="Who is best in hydrogen catalysis?",
        assumptions=["Interpreted best as recent evidence-backed composite score."],
        caveats=["Citation data is incomplete for 2026."],
        follow_up_suggestions=["Change time range"],
        freshness={"database_snapshot": "2026-04-29"},
    )

    data = state.to_dict()

    assert data["assumptions"]
    assert data["caveats"]
    assert data["follow_up_suggestions"] == ["Change time range"]
    assert data["freshness"]["database_snapshot"] == "2026-04-29"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/orchestration/test_verifier_node.py::test_nrg_state_carries_answer_engine_v1_fields -q
```

Expected: FAIL because these fields are not on `NRGState`.

- [ ] **Step 3: Add fields to `NRGState`**

In `src/orchestration/state.py`, add:

```python
    interpreted_question: str = ""
    assumptions: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    follow_up_suggestions: list[str] = field(default_factory=list)
    freshness: dict = field(default_factory=dict)
    source_data: dict = field(default_factory=dict)
    answer_id: str = ""
```

- [ ] **Step 4: Planner emits useful defaults**

In `src/orchestration/nodes/planner.py`, add a helper:

```python
def _default_assumptions(query: str) -> list[str]:
    lowered = query.lower()
    assumptions: list[str] = []
    if any(word in lowered for word in ("best", "top", "leading", "strongest")):
        assumptions.append("Interpreted ranking as an evidence-backed composite of output, recency, funding, and impact where available.")
    if not re.search(r"\b(20\d{2}|last\s+\d+\s+years?|all-time|all time|between)\b", lowered):
        assumptions.append("Used recent five-year context unless the query or data path specified another range.")
    return assumptions
```

Merge these assumptions into the planner return:

```python
                "assumptions": _default_assumptions(planning_query),
                "interpreted_question": planning_query,
```

Do the same for heuristic fallback.

- [ ] **Step 5: Executor emits freshness/source_data shell**

In `src/orchestration/nodes/executor.py`, add to returned dicts:

```python
        "freshness": {
            "database_snapshot": None,
            "document_indexed_at": None,
            "warning": None,
        },
        "source_data": {
            "sql_query": results.get("sql_query"),
            "rows": results.get("sql_results", []),
            "documents": results.get("retrieved_chunks", []),
        },
```

Apply to SQL-only, RAG-only, parallel, DAG, and fast-path returns.

- [ ] **Step 6: Run orchestration tests**

Run:

```bash
pytest tests/orchestration/test_router.py tests/orchestration/test_verifier_node.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/orchestration/state.py src/orchestration/nodes/planner.py src/orchestration/nodes/executor.py tests/orchestration/test_verifier_node.py
git commit -m "feat: carry answer engine metadata through orchestration"
```

---

### Task 6: Verifier Produces Evidence Confidence And Caveats

**Files:**
- Modify: `src/orchestration/nodes/verifier.py`
- Modify: `src/api/answer_contract.py`
- Test: `tests/orchestration/test_verifier_numeric_faithfulness.py`
- Test: `tests/orchestration/test_verifier_node.py`

- [ ] **Step 1: Add confidence/caveat verifier test**

Add to `tests/orchestration/test_verifier_node.py`:

```python
from src.orchestration.nodes.verifier import verifier_node


def test_verifier_marks_unsupported_numeric_answer_low_confidence():
    state = {
        "user_query": "Top grants",
        "synthesized_response": "DST disbursed 999 crore [cite:structured:0].",
        "sql_results": [{"agency": "DST", "total": 10}],
        "citations": [{"pub_id": "structured", "chunk_id": "0"}],
        "user_tier": 1,
    }

    result = verifier_node(state)

    assert result["answer_confidence"] in {"low", "needs_clarification"}
    assert result["caveats"]
    assert result["unsupported_claims"]
```

- [ ] **Step 2: Run focused verifier test and verify failure**

Run:

```bash
pytest tests/orchestration/test_verifier_node.py::test_verifier_marks_unsupported_numeric_answer_low_confidence -q
```

Expected: FAIL because current verifier labels may not use v1 confidence/caveats.

- [ ] **Step 3: Normalize verifier output**

At the end of `verifier_node`, ensure return dict contains:

```python
    answer_confidence = "high"
    caveats = []
    if unsupported_claims:
        answer_confidence = "low"
        caveats.append("Some numeric claims were not supported by retrieved evidence.")
    elif faithfulness_score < 0.85:
        answer_confidence = "medium"
        caveats.append("Answer is supported, but citation or evidence coverage is incomplete.")

    return {
        **existing_result,
        "answer_confidence": answer_confidence,
        "answer_confidence_score": faithfulness_score,
        "caveats": caveats,
    }
```

Preserve existing `verification_status`, `faithfulness_score`, `unsupported_claims`, and citation enrichment behavior.

- [ ] **Step 4: Run verifier tests**

Run:

```bash
pytest tests/orchestration/test_verifier_node.py tests/orchestration/test_verifier_numeric_faithfulness.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/orchestration/nodes/verifier.py tests/orchestration/test_verifier_node.py
git commit -m "feat: expose evidence confidence from verifier"
```

---

### Task 7: Streaming Endpoint Emits V1 Phases And Final Envelope

**Files:**
- Modify: `src/api/routes/query.py`
- Modify: `frontend/src/hooks/useStreamingQuery.ts`
- Test: `tests/api/test_critical_path_stream.py`
- Test: `frontend/tests/e2e/streaming_answer.spec.ts`

- [ ] **Step 1: Add stream phase contract test**

Extend `tests/api/test_critical_path_stream.py` with:

```python
def test_stream_emits_human_answer_engine_phases(client, auth_headers):
    with client.stream(
        "POST",
        "/api/query/stream",
        headers=auth_headers,
        json={"query": "Top funding agencies by total grant amount"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    for phase in [
        "understanding",
        "planning",
        "searching_records",
        "checking_documents",
        "synthesizing",
        "verifying",
    ]:
        assert f'"phase": "{phase}"' in body
    assert '"answer_id"' in body
    assert '"source_data"' in body
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/api/test_critical_path_stream.py -q
```

Expected: FAIL because stream emits legacy phase names and no final envelope.

- [ ] **Step 3: Update streaming phase emissions**

In `src/api/routes/query.py`, emit these phase events in order:

```python
yield 'event: phase\ndata: {"phase": "understanding", "label": "Understanding your question", "progress": 0.08}\n\n'
yield 'event: phase\ndata: {"phase": "planning", "label": "Planning retrieval", "progress": 0.18}\n\n'
yield 'event: phase\ndata: {"phase": "searching_records", "label": "Searching research records", "progress": 0.42}\n\n'
yield 'event: phase\ndata: {"phase": "checking_documents", "label": "Checking documents", "progress": 0.58}\n\n'
yield 'event: phase\ndata: {"phase": "synthesizing", "label": "Synthesizing answer", "progress": 0.78}\n\n'
yield 'event: phase\ndata: {"phase": "verifying", "label": "Verifying sources", "progress": 0.92}\n\n'
```

Keep backward compatibility in frontend by mapping old names and new names.

- [ ] **Step 4: Emit final `answer` envelope event**

At stream completion, build `final_payload` with `normalize_workflow_result(...)` and emit:

```python
yield f"event: answer\ndata: {json.dumps(final_payload)}\n\n"
yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
yield "event: done\ndata: \n\n"
```

- [ ] **Step 5: Update frontend phase type support**

In `frontend/src/types/api.ts`, extend `StreamPhaseName` with:

```ts
  | 'understanding'
  | 'searching_records'
  | 'checking_documents'
```

In `frontend/src/hooks/useStreamingQuery.ts`, add phase labels to `PHASES` and update `normalizeLegacyPhase`.

- [ ] **Step 6: Run stream tests**

Run:

```bash
pytest tests/api/test_critical_path_stream.py -q
cd frontend && npm test -- --run frontend/tests/e2e/streaming_answer.spec.ts
```

Expected: pytest PASS. Frontend command should PASS if the repo's Vitest config supports this path; if not, use the existing frontend test command from `package.json` for this spec.

- [ ] **Step 7: Commit**

```bash
git add src/api/routes/query.py frontend/src/hooks/useStreamingQuery.ts frontend/src/types/api.ts tests/api/test_critical_path_stream.py
git commit -m "feat: stream answer engine phases and final envelope"
```

---

### Task 8: Frontend Types And Query Service Normalize V1 Payloads

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/services/queryService.ts`
- Test: `frontend/tests/lib/answerEngineContract.test.ts`
- Test: `frontend/tests/lib/queryServiceSanitization.test.ts`

- [ ] **Step 1: Write frontend normalization test**

Create `frontend/tests/lib/answerEngineContract.test.ts`:

```ts
import { normalizeQueryResponse } from '../../src/services/queryService'

describe('Answer Engine v1 normalization', () => {
  it('preserves v1 proof fields', () => {
    const response = normalizeQueryResponse({
      query_id: 'query-1',
      answer_id: 'answer-1',
      audit_event_id: 'audit-1',
      tier: 1,
      question: 'Top funding agencies',
      interpreted_question: 'Rank agencies by grant total',
      assumptions: ['Used recent five-year context'],
      route: 'sql',
      final_answer: 'DST leads [1].',
      confidence: { level: 'high', reason: 'Verified' },
      citations: [{ id: '1', source_type: 'sql_row', label: 'funding row', source_id: 'funding:1' }],
      source_data: { sql_query: 'SELECT 1', rows: [{ agency: 'DST' }], documents: [] },
      freshness: { database_snapshot: '2026-04-29', document_indexed_at: null, warning: null },
      caveats: [],
      follow_up_suggestions: ['Change time range'],
      query_time_ms: 100,
    })

    expect(response.answer_id).toBe('answer-1')
    expect(response.response).toBe('DST leads [1].')
    expect(response.final_answer).toBe('DST leads [1].')
    expect(response.confidence?.level).toBe('high')
    expect(response.source_data?.sql_query).toBe('SELECT 1')
    expect(response.assumptions).toEqual(['Used recent five-year context'])
  })
})
```

- [ ] **Step 2: Run frontend test and verify failure**

Run:

```bash
cd frontend && npm test -- --run tests/lib/answerEngineContract.test.ts
```

Expected: FAIL because the client type/normalizer does not expose all v1 fields.

- [ ] **Step 3: Add v1 interfaces**

In `frontend/src/types/api.ts`, add:

```ts
export type AnswerRoute = 'sql' | 'rag' | 'hybrid' | 'clarify' | 'blocked'
export type AnswerConfidenceLevel = 'high' | 'medium' | 'low' | 'needs_clarification'

export interface AnswerEngineConfidence {
  level: AnswerConfidenceLevel
  reason: string
}

export interface AnswerEngineCitation {
  id: string
  source_type: 'sql_row' | 'document_chunk' | 'graph_edge'
  label: string
  source_id: string
  masked?: boolean
}

export interface AnswerEngineSourceData {
  sql_query?: string | null
  rows: Array<Record<string, unknown>>
  documents: Array<Record<string, unknown>>
}

export interface AnswerEngineFreshness {
  database_snapshot?: string | null
  document_indexed_at?: string | null
  warning?: string | null
}
```

Extend `NRGQueryResponse` with optional v1 fields: `answer_id`, `question`, `interpreted_question`, `assumptions`, `route`, `final_answer`, `confidence`, `source_data`, `freshness`, `caveats`, `follow_up_suggestions`, `query_time_ms`.

- [ ] **Step 4: Export and update `normalizeQueryResponse`**

In `frontend/src/services/queryService.ts`, export `normalizeQueryResponse` if not already exported, and map v1 fields:

```ts
  const sourceData = raw?.source_data || {
    sql_query: raw?.sql_query ?? null,
    rows: Array.isArray(raw?.sql_results) ? raw.sql_results : [],
    documents: Array.isArray(raw?.retrieved_chunks) ? raw.retrieved_chunks : [],
  }
```

Return:

```ts
    answer_id: raw?.answer_id,
    question: raw?.question || request.query,
    interpreted_question: raw?.interpreted_question,
    assumptions: Array.isArray(raw?.assumptions) ? raw.assumptions : [],
    route: raw?.route,
    final_answer: responseText,
    confidence: raw?.confidence,
    source_data: {
      ...sourceData,
      rows: sanitizeSqlRowsForTier(sourceData.rows || [], tier),
    },
    freshness: raw?.freshness,
    caveats: Array.isArray(raw?.caveats) ? raw.caveats : [],
    follow_up_suggestions: Array.isArray(raw?.follow_up_suggestions) ? raw.follow_up_suggestions : [],
    query_time_ms: raw?.query_time_ms,
```

- [ ] **Step 5: Run frontend normalization tests**

Run:

```bash
cd frontend && npm test -- --run tests/lib/answerEngineContract.test.ts tests/lib/queryServiceSanitization.test.ts
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/services/queryService.ts frontend/tests/lib/answerEngineContract.test.ts
git commit -m "feat: normalize answer engine payloads in frontend"
```

---

### Task 9: Upgrade ProofInspector For Source, SQL, Freshness, And Audit

**Files:**
- Modify: `frontend/src/components/ProofInspector/ProofInspector.tsx`
- Modify: `frontend/src/views/AnswerEngine.tsx`
- Test: `frontend/tests/components/ProofInspector.test.tsx`
- Test: `frontend/tests/components/AnswerEngineSurface.test.tsx`

- [ ] **Step 1: Add proof inspector test for v1 fields**

Extend `frontend/tests/components/ProofInspector.test.tsx` with:

```tsx
it('renders source data, freshness, and audit proof from v1 payload fields', () => {
  const container = render(
    <ProofInspector
      role="researcher"
      confidence="high"
      citations={[{ id: '1', title: 'Funding source', source: 'sql_row' }]}
      sqlQuery="SELECT agency FROM funding"
      sqlResults={[{ agency: 'DST', total: 10 }]}
      rowsReturned={1}
      auditEventId="audit-1"
      freshness={{ database_snapshot: '2026-04-29', document_indexed_at: null, warning: null }}
      assumptions={['Used recent five-year context']}
      caveats={[]}
    />
  )

  expect(container.textContent).toContain('Funding source')
  expect(container.textContent).toContain('2026-04-29')
  expect(container.textContent).toContain('Used recent five-year context')
  expect(container.textContent).toContain('audit-1')
})
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
cd frontend && npm test -- --run tests/components/ProofInspector.test.tsx
```

Expected: FAIL because `ProofInspector` does not accept freshness/assumptions/caveats props.

- [ ] **Step 3: Add props and render sections**

In `frontend/src/components/ProofInspector/ProofInspector.tsx`, extend props:

```ts
  freshness?: {
    database_snapshot?: string | null
    document_indexed_at?: string | null
    warning?: string | null
  }
  assumptions?: string[]
  caveats?: string[]
```

Render:

```tsx
        {assumptions.length > 0 && (
          <section className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">Assumptions</p>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-nrg-text">
              {assumptions.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        )}
```

Add similar compact sections for `freshness` and `caveats`.

- [ ] **Step 4: Pass fields from AnswerEngine surface**

Where `ProofInspector` is used in `frontend/src/views/AnswerEngine.tsx`, pass v1 fields from the normalized query response or streaming proof payload:

```tsx
freshness={latestAnswer?.freshness}
assumptions={latestAnswer?.assumptions || []}
caveats={latestAnswer?.caveats || []}
```

- [ ] **Step 5: Run component tests**

Run:

```bash
cd frontend && npm test -- --run tests/components/ProofInspector.test.tsx tests/components/AnswerEngineSurface.test.tsx
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ProofInspector/ProofInspector.tsx frontend/src/views/AnswerEngine.tsx frontend/tests/components/ProofInspector.test.tsx
git commit -m "feat: show answer proof metadata in inspector"
```

---

### Task 10: QueryWorkbench And StreamingAnswerPanel Render Conversational Answer + Proof

**Files:**
- Modify: `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx`
- Modify: `frontend/src/components/StreamingAnswerPanel.tsx`
- Modify: `frontend/src/hooks/useStreamingQuery.ts`
- Test: `frontend/tests/components/QueryWorkbench.test.tsx`
- Test: `frontend/tests/e2e/answer_engine_v1_walk.spec.ts`

- [ ] **Step 1: Add QueryWorkbench behavior test**

Extend `frontend/tests/components/QueryWorkbench.test.tsx` with:

```tsx
it('keeps Ask workspace query-first and exposes proof callbacks', () => {
  const onCitationClick = vi.fn()
  const onProofOpen = vi.fn()
  const onProofChange = vi.fn()
  const container = render(
    <QueryWorkbench
      role="researcher"
      onCitationClick={onCitationClick}
      onProofOpen={onProofOpen}
      onProofChange={onProofChange}
    />
  )

  expect(container.getByTestId('query-workbench')).toBeTruthy()
  expect(container.textContent).toContain('Start with one high-signal question')
  expect(container.querySelector('input, textarea')).toBeTruthy()
})
```

- [ ] **Step 2: Run component tests and verify current behavior**

Run:

```bash
cd frontend && npm test -- --run tests/components/QueryWorkbench.test.tsx
```

Expected: PASS if current query-first contract is already met. If it fails, adjust labels/test IDs without changing the product direction.

- [ ] **Step 3: Add final envelope handling to streaming hook**

In `frontend/src/hooks/useStreamingQuery.ts`, add an `answer` event listener:

```ts
source.addEventListener('answer', (event) => {
  const payload = parseEventData((event as MessageEvent).data)
  if (payload && typeof payload === 'object') {
    appendToken(String(payload.final_answer || payload.response || ''))
    setAuditEventId(payload.audit_event_id || null)
    payload.citations?.forEach(addCitation)
    optionsRef.current.onComplete?.({
      elapsed_ms: Number(payload.query_time_ms || 0),
      synthesis_tier: String(payload.synthesis_method || 'unknown'),
      verification_status: payload.confidence?.level !== 'low',
      citations: (payload.citations || []).map(toStreamCitation),
      provenance: payload.provenance || {},
      query_id: String(payload.query_id),
      audit_event_id: payload.audit_event_id,
    }, String(payload.final_answer || payload.response || ''))
  }
})
```

Prevent duplicated answer text by setting full text when the answer event arrives after token streaming instead of always appending. Use `setFullText` if token stream already produced text.

- [ ] **Step 4: Ensure `StreamingAnswerPanel` renders proof actions after final answer**

Keep `AnswerTrustActions`, citation chips, and `VerifiedBadge`, but make sure they appear for both legacy `verified` event and new `answer` event. The panel should show no raw JSON.

- [ ] **Step 5: Add e2e acceptance walk**

Create `frontend/tests/e2e/answer_engine_v1_walk.spec.ts`:

```ts
import { test, expect } from '@playwright/test'

test('Answer Engine v1 Ask -> Answer -> Proof path is visible', async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-username').fill('researcher@iitgn.ac.in')
  await page.getByTestId('login-password').fill('Researcher@2026')
  await page.getByTestId('login-submit').click()
  await page.waitForURL(/\/app\/researcher/)

  await page.goto('/app')
  await expect(page.getByTestId('query-workbench')).toBeVisible()
  await page.getByRole('textbox').first().fill('Which institutes produce the most granted patents per INR 10 Cr government funding?')
  await page.keyboard.press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible()
  await expect(page.getByText(/Verifying|Synthesizing|Searching|Planning/i)).toBeVisible()
})
```

- [ ] **Step 6: Run frontend tests**

Run:

```bash
cd frontend && npm test -- --run tests/components/QueryWorkbench.test.tsx
npx playwright test tests/e2e/answer_engine_v1_walk.spec.ts --project=chromium
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/QueryWorkbench/QueryWorkbench.tsx frontend/src/components/StreamingAnswerPanel.tsx frontend/src/hooks/useStreamingQuery.ts frontend/tests/components/QueryWorkbench.test.tsx frontend/tests/e2e/answer_engine_v1_walk.spec.ts
git commit -m "feat: render answer engine ask-answer-proof workflow"
```

---

### Task 11: Tier-Safe Exports And Source Downloads

**Files:**
- Modify: `frontend/src/components/ProofInspector/ProofInspector.tsx`
- Modify: `frontend/src/services/queryService.ts`
- Test: `frontend/tests/components/ProofInspector.test.tsx`
- Test: `frontend/tests/lib/queryServiceSanitization.test.ts`

- [ ] **Step 1: Add CSV export test for visible rows only**

Extend `frontend/tests/components/ProofInspector.test.tsx`:

```tsx
it('offers CSV export only for visible source rows', () => {
  const container = render(
    <ProofInspector
      role="industry"
      confidence="medium"
      citations={[]}
      sqlQuery="SELECT institution, email FROM researchers"
      sqlResults={[{ institution: 'IIT-GN' }]}
      rowsReturned={1}
      auditEventId="audit-1"
    />
  )

  expect(container.textContent).toContain('IIT-GN')
  expect(container.textContent).not.toContain('email')
})
```

- [ ] **Step 2: Run proof tests**

Run:

```bash
cd frontend && npm test -- --run tests/components/ProofInspector.test.tsx tests/lib/queryServiceSanitization.test.ts
```

Expected: PASS after previous sanitization behavior; if it fails, keep filtering in `queryService.ts` and do not rely on UI hiding.

- [ ] **Step 3: Add CSV generation helper**

In `ProofInspector.tsx`, add:

```ts
const toCsv = (rows: Array<Record<string, unknown>>) => {
  if (!rows.length) return ''
  const headers = Object.keys(rows[0])
  const escape = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`
  return [headers.join(','), ...rows.map((row) => headers.map((header) => escape(row[header])).join(','))].join('\n')
}
```

Add a `Download visible rows` button only when `sourceRows.length > 0`. Use a Blob download in browser. Do not export hidden original rows.

- [ ] **Step 4: Run tests**

Run:

```bash
cd frontend && npm test -- --run tests/components/ProofInspector.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProofInspector/ProofInspector.tsx frontend/tests/components/ProofInspector.test.tsx
git commit -m "feat: export tier-safe visible source rows"
```

---

### Task 12: Final Acceptance And Evidence

**Files:**
- Modify: `docs/specs/NRG_ANSWER_ENGINE_V1_SPEC.md` if reality differs from spec
- Create: `evidence/2026-04-29/answer_engine_v1_acceptance.md`

- [ ] **Step 1: Run backend focused suite**

Run:

```bash
pytest \
  tests/contract/test_answer_engine_v1_contract.py \
  tests/api/test_langgraph_api.py \
  tests/api/test_answer_records_api.py \
  tests/api/test_query_security_validation.py \
  tests/api/test_critical_path_stream.py \
  tests/orchestration/test_verifier_node.py \
  tests/orchestration/test_verifier_numeric_faithfulness.py \
  -q
```

Expected: PASS with zero failures.

- [ ] **Step 2: Run frontend focused suite**

Run:

```bash
cd frontend && npm test -- --run \
  tests/lib/answerEngineContract.test.ts \
  tests/lib/queryServiceSanitization.test.ts \
  tests/components/ProofInspector.test.tsx \
  tests/components/QueryWorkbench.test.tsx \
  tests/components/AnswerEngineSurface.test.tsx
```

Expected: PASS with zero failures.

- [ ] **Step 3: Run e2e acceptance walk**

Run:

```bash
cd frontend && npx playwright test tests/e2e/answer_engine_v1_walk.spec.ts --project=chromium
```

Expected: PASS and Playwright artifact generated.

- [ ] **Step 4: Write evidence report**

Create `evidence/2026-04-29/answer_engine_v1_acceptance.md` with:

```markdown
# Answer Engine v1 Acceptance Evidence

Date: 2026-04-29

## Backend

Command:
`pytest tests/contract/test_answer_engine_v1_contract.py tests/api/test_langgraph_api.py tests/api/test_answer_records_api.py tests/api/test_query_security_validation.py tests/api/test_critical_path_stream.py tests/orchestration/test_verifier_node.py tests/orchestration/test_verifier_numeric_faithfulness.py -q`

Result:
Record the exact backend command result, including the pass/fail count and the final pytest summary line.

## Frontend

Command:
`cd frontend && npm test -- --run tests/lib/answerEngineContract.test.ts tests/lib/queryServiceSanitization.test.ts tests/components/ProofInspector.test.tsx tests/components/QueryWorkbench.test.tsx tests/components/AnswerEngineSurface.test.tsx`

Result:
Record the exact frontend test result, including the pass/fail count and the final Vitest summary line.

## E2E

Command:
`cd frontend && npx playwright test tests/e2e/answer_engine_v1_walk.spec.ts --project=chromium`

Result:
Record the exact Playwright result and artifact path printed by the command.

## Acceptance

- Ask workspace visible.
- Query progresses through human-readable phases.
- Final answer uses canonical envelope.
- Source/SQL/audit proof visible.
- Blocked PII query returns safe envelope.
- Tier filtering remains enforced before frontend render.
```

- [ ] **Step 5: Run unresolved-marker scan**

Run:

```bash
rg -n "T[O]DO|T[B]D|F[I]XME|<(paste|replace|fill)[^>]*>" docs/specs/NRG_ANSWER_ENGINE_V1_SPEC.md docs/superpowers/plans/2026-04-29-nrg-answer-engine-v1.md evidence/2026-04-29/answer_engine_v1_acceptance.md
```

Expected: no matches.

- [ ] **Step 6: Commit**

```bash
git add docs/specs/NRG_ANSWER_ENGINE_V1_SPEC.md evidence/2026-04-29/answer_engine_v1_acceptance.md
git commit -m "test: capture answer engine v1 acceptance evidence"
```

---

## Self-Review Checklist

- [ ] The implementation changes existing `/query` and AnswerEngine surfaces rather than creating a parallel stack.
- [ ] Canonical payload still preserves legacy frontend fields (`response`, `sql_query`, `sql_results`) during transition.
- [ ] Blocked queries return safe product language, not raw security internals.
- [ ] Tier filtering remains backend/API-first.
- [ ] Fast paths and workflow paths both normalize into the same envelope.
- [ ] Streaming and non-streaming endpoints converge on the same final payload shape.
- [ ] Saved Answer Records store tier-safe payloads after filtering.
- [ ] Proof UI shows source rows/documents, SQL/computation, freshness, assumptions, caveats, and audit ID.
- [ ] Fine-tuning, full graph, full multilingual, production deployment, and external connectors remain out of v1 scope.
