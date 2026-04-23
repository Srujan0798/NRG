import src.orchestration.nodes.synthesizer as synthesizer_module


def test_extract_citations_from_response():
    citations = synthesizer_module._extract_citations(
        "A claim [cite:pub_1:ch_2] and another [cite:researcher-1:0]."
    )

    assert citations == [
        {"id": "pub_1:ch_2", "pub_id": "pub_1", "chunk_id": "ch_2"},
        {"id": "researcher-1:0", "pub_id": "researcher-1", "chunk_id": "0"},
    ]


def test_fallback_synthesis_returns_citations(monkeypatch):
    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)

    result = synthesizer_module.synthesizer_node(
        {
            "user_query": "Find researchers in Gujarat",
            "sql_results": [
                {
                    "researcher_id": "researcher-1",
                    "name": "Dr. Rao",
                    "research_area": "Robotics",
                    "state": "GJ",
                }
            ],
            "retrieved_chunks": [],
            "user_tier": 1,
            "conversation_history": [],
            "intent": "structured",
            "routing_decision": "text_to_sql",
        }
    )

    assert "[cite:structured:0]" in result["synthesized_response"]
    assert result["citations"] == [
        {"id": "structured:0", "pub_id": "structured", "chunk_id": "0"}
    ]
