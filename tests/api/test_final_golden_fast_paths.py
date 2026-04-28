import src.api.main as api_main


def _answer_for(query: str, tier: int = 1) -> dict:
    response = api_main._fast_query_response(
        query,
        user_tier=tier,
        user_id=f"golden-tier-{tier}",
        session_id=f"golden-session-{tier}-{abs(hash(query))}",
    )
    assert response is not None
    return response


def test_golden_state_ai_comparison_answers_the_named_states():
    response = _answer_for("Compare Gujarat and Karnataka AI research output 5y; show gap")

    assert response["intent"] == "state_ai_output_comparison"
    assert response["sql_query"]
    assert len(response["sql_results"]) >= 2
    assert "Gujarat" in response["response"]
    assert "Karnataka" in response["response"]
    assert "gap" in response["response"].lower()
    assert "IIT Madras" not in response["response"]


def test_golden_hydrogen_collaboration_returns_ranked_iit_collaborators():
    response = _answer_for("Which IITs collaborate most on hydrogen catalysis?")

    assert response["intent"] == "hydrogen_collaboration_ranking"
    assert response["sql_query"]
    assert len(response["sql_results"]) >= 3
    assert "hydrogen catalysis" in response["response"].lower()
    assert "IIT Gandhinagar" in response["response"]
    assert "collaboration" in response["response"].lower()
    assert "Laboratory evidence is available" not in response["response"]


def test_golden_trl9_clean_energy_returns_state_counts():
    response = _answer_for("How many TRL-9 innovations exist in clean energy by state?")

    assert response["intent"] == "trl9_clean_energy_by_state"
    assert response["sql_query"]
    assert response["sql_results"]
    assert "TRL-9" in response["response"]
    assert "clean energy" in response["response"].lower()
    assert all("state" in row and "innovation_count" in row for row in response["sql_results"])
    assert "Institution-level aggregates are available" not in response["response"]


def test_golden_doubled_grants_returns_fy22_to_fy24_growth():
    response = _answer_for("Show me institutes that doubled grant size between FY22 and FY24")

    assert response["intent"] == "grant_growth_doubled_institutes"
    assert response["sql_query"]
    assert response["sql_results"]
    assert "FY22" in response["response"]
    assert "FY24" in response["response"]
    assert "doubled" in response["response"].lower()
    assert "top five funding agencies" not in response["response"].lower()
