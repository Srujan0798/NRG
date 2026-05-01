import asyncio

import src.api.main as api_main


def test_c4_load_queries_return_specific_read_model_answers():
    cases = {
        "find robotics researchers in Gujarat": ("robotics", "gujarat"),
        "AI researchers in Karnataka": ("artificial intelligence", "karnataka"),
        "funding trends by year": ("funding", "year"),
        "publication counts by institution": ("publication", "institution"),
        "patent opportunities in AI": ("patent", "artificial intelligence"),
        "startup incubation results": ("startup", "incubation"),
    }

    responses = []
    for query, expected_terms in cases.items():
        response = api_main._c4_read_model_response(
            query,
            user_tier=1,
            session_id="c4-test",
        )
        assert response is not None, query
        assert response["routing_decision"] == "fast_path"
        assert response["route"] == "c4_read_model"
        assert response["synthesis_method"] == "rule_based_read_model"
        assert response["citations"], query
        assert response["sql_results"], query
        assert response["node_timings"]["executor"] == 0.0
        answer = response["response"].lower()
        for term in expected_terms:
            assert term in answer, (query, answer)
        responses.append(response["response"])

    assert len(set(responses)) == len(responses)


def test_c4_read_model_anonymizes_researcher_rows_for_tier3():
    response = api_main._c4_read_model_response(
        "researchers open to collaboration",
        user_tier=3,
        session_id="c4-tier3-test",
    )

    assert response is not None
    assert "Tier 3" in response["response"]
    assert response["sql_results"]
    assert all("email" not in row for row in response["sql_results"])
    assert all(str(row.get("researcher", "")).startswith("Researcher ") for row in response["sql_results"])


def test_c4_funding_institution_query_uses_safe_seed_when_read_model_empty(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "_c4_read_model_snapshot",
        lambda: {"funding_by_institute": [], "funding_by_agency": [], "research_area_funding": []},
    )

    response = api_main._c4_read_model_response(
        "Compare funding allocation across major institutions",
        user_tier=2,
        session_id="c4-empty-funding-test",
    )

    assert response is not None
    assert response["status"] == "success"
    assert response["intent"] == "funding_aggregate"
    assert response["verification_status"] is True
    assert response["sql_results"]
    assert response["citations"]


def test_c4_state_output_query_uses_safe_seed_when_read_model_empty(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "_c4_read_model_snapshot",
        lambda: {"researchers_by_state": [], "publication_by_area": [], "publication_by_year": []},
    )

    response = api_main._c4_read_model_response(
        "Compare Gujarat and Karnataka AI research output and show gap",
        user_tier=1,
        session_id="c4-empty-state-test",
    )

    assert response is not None
    assert response["status"] == "success"
    assert response["intent"] == "state_research_output_comparison"
    assert response["verification_status"] is True
    assert [row["state"] for row in response["sql_results"]] == ["Gujarat", "Karnataka"]
    assert response["citations"]


def test_query_cache_singleflight_builds_same_key_once():
    api_main._api_cache.invalidate("singleflight-test")
    key = "singleflight-test:c4"
    calls = 0

    async def scenario():
        nonlocal calls

        async def build():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.01)
            return {"value": calls}

        return await asyncio.gather(
            *[
                api_main._get_or_build_query_cache_singleflight(key, build, ttl=30)
                for _ in range(12)
            ]
        )

    results = asyncio.run(scenario())

    assert calls == 1
    assert [payload for payload, _ in results] == [{"value": 1}] * 12
    assert sum(1 for _, cache_hit in results if cache_hit) >= 11
