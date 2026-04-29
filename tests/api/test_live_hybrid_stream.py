import json

from fastapi.testclient import TestClient

import src.api.main as api_main


def _read_sse_event(body: str, event_name: str) -> dict:
    for block in body.split("\n\n"):
        if f"event: {event_name}\n" not in block:
            continue
        for line in block.splitlines():
            if line.startswith("data: "):
                return json.loads(line.removeprefix("data: "))
    raise AssertionError(f"event {event_name!r} not found in SSE body:\n{body[:1000]}")


def test_live_stream_funding_policy_query_returns_hybrid_sql_and_document_proof():
    api_main._api_cache.invalidate()
    client = TestClient(api_main.app)
    login_response = client.post(
        "/auth/login",
        json={"username": "researcher@iitgn.ac.in", "password": "Researcher@2026"},
    )
    assert login_response.status_code == 200, login_response.text

    with client.stream(
        "GET",
        "/api/query/stream",
        params={
            "query": "Top funding agencies and explain the policy pattern",
            "session_id": "live-hybrid-acceptance",
        },
    ) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    answer = _read_sse_event(body, "answer")

    assert answer["route"] == "hybrid"
    assert answer["source_data"]["sql_query"].startswith("SELECT gov_organisation_name")
    assert len(answer["source_data"]["rows"]) >= 5
    assert len(answer["source_data"]["documents"]) >= 1
    assert answer["provenance"]["synth"] == "rule_based_hybrid"
    assert answer["provenance"]["cloud_synthesis_used"] is False
    assert answer["provenance"]["hybrid_evidence"]["sql_rows"] == len(answer["source_data"]["rows"])
    assert answer["provenance"]["hybrid_evidence"]["document_chunks"] == len(answer["source_data"]["documents"])
    assert answer["audit_event_id"]
