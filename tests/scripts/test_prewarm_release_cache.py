import pytest

from scripts import prewarm_release_cache as prewarm


def test_default_release_queries_cover_three_acceptance_questions():
    queries = prewarm.default_release_queries()

    assert len(queries) >= 3
    assert any("TRL" in query or "Level 9" in query for query in queries)
    assert any("patent" in query.lower() for query in queries)
    assert any("grant" in query.lower() for query in queries)


def test_query_payload_uses_production_query_contract():
    payload = prewarm.build_query_payload("Top funding agencies", "release-session")

    assert payload == {
        "query": "Top funding agencies",
        "session_id": "release-session",
    }
    assert "question" not in payload


@pytest.mark.asyncio
async def test_prewarm_queries_posts_each_query_to_query_endpoint():
    calls = []

    async def fake_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})

        class Response:
            elapsed = type("Elapsed", (), {"total_seconds": lambda self: 0.25})()

            def raise_for_status(self):
                return None

            def json(self):
                return {"audit_event_id": "audit-1", "sql_results": [{"ok": True}]}

        return Response()

    results = await prewarm.prewarm_queries(
        ["Query A", "Query B"],
        token="token-123",
        api_url="http://api.test",
        session_prefix="test-prewarm",
        post_fn=fake_post,
    )

    assert [call["url"] for call in calls] == [
        "http://api.test/query",
        "http://api.test/query",
    ]
    assert calls[0]["headers"]["Authorization"] == "Bearer token-123"
    assert calls[0]["json"] == {"query": "Query A", "session_id": "test-prewarm-1"}
    assert results[0].rows_returned == 1
