import json


class FakePlannerClient:
    model = "fake-planner"

    def generate(self, system_prompt, user_prompt, conversation_history):
        assert "query planner" in system_prompt.lower()
        assert "DATABASE SCHEMA" in user_prompt
        assert "top researchers in Gujarat" in user_prompt
        return json.dumps(
            {
                "subqueries": ["Find researchers in Gujarat", "Rank by recent publications"],
                "schema_tables": ["researchers", "publications", "researcher_publications"],
                "desired_skills": ["sql", "rag"],
                "expected_output_shape": "ranked list with evidence",
            }
        )


def test_planner_node_returns_strict_plan(monkeypatch):
    import src.orchestration.nodes.planner as planner_module

    monkeypatch.setattr(planner_module, "get_llm_client", lambda: FakePlannerClient())
    monkeypatch.setattr(planner_module, "log_llm_call", lambda *args, **kwargs: None)

    result = planner_module.planner_node(
        {"user_query": "top researchers in Gujarat", "conversation_history": []}
    )

    assert result["plan"]["desired_skills"] == ["sql", "rag"]
    assert "researchers" in result["plan"]["schema_tables"]
    assert result["planner_metadata"]["model"] == "fake-planner"


def test_planner_node_falls_back_when_no_llm(monkeypatch):
    import src.orchestration.nodes.planner as planner_module

    monkeypatch.setattr(planner_module, "get_llm_client", lambda: None)

    result = planner_module.planner_node({"user_query": "anything"})

    assert result["plan"] is not None
    assert "subqueries" in result["plan"]
    assert result["planner_metadata"]["mode"] == "heuristic_fallback"


def test_planner_fallback_uses_catalog_for_funding_tables(monkeypatch):
    import src.orchestration.nodes.planner as planner_module

    monkeypatch.setattr(planner_module, "get_llm_client", lambda: None)

    result = planner_module.planner_node(
        {"user_query": "Top 5 funding agencies by total grant amount"}
    )

    assert "innovation_grant_from_govt" in result["plan"]["schema_tables"]
    assert result["plan"]["desired_skills"] == ["sql"]
    assert result["plan"]["expected_output_shape"] == "ranked_table"
    assert result["planner_metadata"]["catalog"]["route"] == "text_to_sql"
    assert "funding" in result["planner_metadata"]["catalog"]["matched_domains"]
