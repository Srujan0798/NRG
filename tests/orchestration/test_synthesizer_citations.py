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


def test_system_prompt_requires_tier_voice_four_part_structure_and_numeric_citations():
    prompt = synthesizer_module._build_system_prompt(
        user_tier=2,
        sources=["sql"],
        sql_results=[{"state": "Gujarat", "count": 42}],
        chunks=[],
        context_summary="active_domain=publications; last turns mention Gujarat",
    )

    assert "ministry official" in prompt
    assert "4-paragraph answer" in prompt
    assert "headline number/finding" in prompt
    assert "why it matters to the user's tier" in prompt
    assert "Every sentence containing a number MUST include" in prompt
    assert "active_domain=publications" in prompt


def test_hybrid_fallback_combines_structured_and_document_evidence(monkeypatch):
    monkeypatch.delenv("CLOUD_SYNTHESIS_ALLOWED", raising=False)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)

    result = synthesizer_module.synthesizer_node(
        {
            "user_query": "Find top funding agencies and explain the policy pattern",
            "sql_results": [
                {
                    "gov_organisation_name": "MeitY",
                    "total_grant": 47338100000,
                }
            ],
            "retrieved_chunks": [
                {
                    "publication_id": "DOC-FUNDING-1",
                    "chunk_id": "ch_0",
                    "title": "Funding policy note",
                    "content": "Digital technology programmes concentrate grants around mission-mode agencies.",
                }
            ],
            "user_tier": 2,
            "conversation_history": [],
            "intent": "hybrid",
            "routing_decision": "text_to_sql+rag",
        }
    )

    text = result["synthesized_response"]
    assert "Hybrid Evidence Answer" in text
    assert "Structured finding" in text
    assert "Document context" in text
    assert "Combined answer" in text
    assert "[cite:structured:0]" in text
    assert "[cite:DOC-FUNDING-1:ch_0]" in text
    assert result["provenance"]["synth"] == "rule_based_hybrid"
    assert result["provenance"]["hybrid_evidence"] == {"sql_rows": 1, "document_chunks": 1}


def test_hybrid_fallback_keeps_three_sources_and_deduplicates_repeated_context(monkeypatch):
    monkeypatch.delenv("CLOUD_SYNTHESIS_ALLOWED", raising=False)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)

    result = synthesizer_module.synthesizer_node(
        {
            "user_query": "Synthesize funding concentration across agencies",
            "sql_results": [
                {"gov_organisation_name": "MeitY", "total_grant": 47338100000},
                {"gov_organisation_name": "CSIR", "total_grant": 9100000000},
                {"gov_organisation_name": "ANRF", "total_grant": 6200000000},
            ],
            "retrieved_chunks": [
                {
                    "publication_id": "DOC-FUNDING-1",
                    "chunk_id": "ch_0",
                    "title": "Funding policy A",
                    "content": "Digital mission funding concentrates around implementation agencies.",
                },
                {
                    "publication_id": "DOC-FUNDING-2",
                    "chunk_id": "ch_1",
                    "title": "Funding policy B",
                    "content": "Shared mission-mode funding pattern supports translation.",
                },
                {
                    "publication_id": "DOC-FUNDING-3",
                    "chunk_id": "ch_2",
                    "title": "Funding policy B",
                    "content": "Shared mission-mode funding pattern supports translation.",
                },
            ],
            "user_tier": 2,
            "conversation_history": [],
            "intent": "hybrid",
            "routing_decision": "text_to_sql+rag",
        }
    )

    text = result["synthesized_response"]
    assert "MeitY" in text
    assert "CSIR" in text
    assert "ANRF" in text
    assert "[cite:DOC-FUNDING-1:ch_0]" in text
    assert "[cite:DOC-FUNDING-2:ch_1]" in text
    assert "[cite:DOC-FUNDING-3:ch_2]" in text
    assert text.count("Shared mission-mode funding pattern supports translation") == 1
    assert result["provenance"]["hybrid_evidence"] == {"sql_rows": 3, "document_chunks": 3}
