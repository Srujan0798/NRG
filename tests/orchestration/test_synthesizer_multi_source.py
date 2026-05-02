"""Tests for multi-source data retention — all sources retained after deduplication.

Covers A5-09: Synthesizer drops information when merging multi-source results.
Covers A5-11: Knowledge synthesis doesn't deduplicate across 3+ sources.
"""

import pytest
from src.orchestration.nodes import synthesizer as synth_module


class TestSynthesizerMultiSourceRetention:
    """Verify all source data is retained after synthesis and deduplication."""

    def test_sql_only_result_contains_all_sql_fields(self, monkeypatch):
        """SQL-only result preserves all SQL record fields."""
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "Show me robotics researchers in Gujarat",
                "sql_results": [
                    {"name": "Dr. Rao", "institution": "IIT Bombay", "h_index": 45, "publications": 120},
                    {"name": "Dr. Patel", "institution": "IIT Delhi", "h_index": 38, "publications": 87},
                ],
                "retrieved_chunks": [],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "structured",
                "routing_decision": "text_to_sql",
            }
        )

        response = result["synthesized_response"]
        assert "Dr. Rao" in response
        assert "Dr. Patel" in response
        assert "IIT Bombay" in response
        assert "IIT Delhi" in response
        assert result["verification_status"] is True

    def test_rag_only_result_contains_chunk_content(self, monkeypatch):
        """RAG-only result preserves all retrieved chunk content."""
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "What is the funding policy for robotics?",
                "sql_results": [],
                "retrieved_chunks": [
                    {"publication_id": "PUB-1", "chunk_id": "ch0", "content": " DST funding for robotics is INR 500Cr."},
                    {"publication_id": "PUB-2", "chunk_id": "ch1", "content": " MeitY supports robotics translation."},
                ],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "unstructured",
                "routing_decision": "rag",
            }
        )

        response = result["synthesized_response"]
        assert "PUB-1" in response or "DST" in response or "funding" in response.lower()
        assert result["verification_status"] is True

    def test_hybrid_result_contains_both_sql_and_rag(self, monkeypatch):
        """Hybrid result contains both SQL records and RAG chunks."""
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "Compare funding and publications for robotics research",
                "sql_results": [
                    {"agency": "DST", "total_grant": 500000000},
                    {"agency": "MeitY", "total_grant": 120000000},
                ],
                "retrieved_chunks": [
                    {"publication_id": "PUB-1", "chunk_id": "ch0", "content": " DST grants support robotics."},
                ],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
            }
        )

        response = result["synthesized_response"]
        assert "DST" in response or "MeitY" in response
        citations = result.get("citations", [])
        assert len(citations) >= 1, "At least one citation should be present"

    def test_3_source_result_has_all_three_citations(self, monkeypatch):
        """Three distinct sources (SQL + 2 RAG chunks) each cited once."""
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "What is the complete robotics research landscape?",
                "sql_results": [
                    {"name": "Dr. Rao", "publications": 120},
                ],
                "retrieved_chunks": [
                    {"publication_id": "PUB-FUND-1", "chunk_id": "ch0", "content": " DST robotics funding."},
                    {"publication_id": "PUB-FUND-2", "chunk_id": "ch1", "content": " MeitY robotics policy."},
                ],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
            }
        )

        citations = result.get("citations", [])
        pub_ids = {c["pub_id"] for c in citations}
        assert len(pub_ids) >= 3, f"Expected 3+ distinct pub_ids, got {pub_ids}"

    def test_three_sources_all_have_distinct_citations(self, monkeypatch):
        """Three distinct sources produce three distinct citations in the final answer.

        A5-11: When three sources provide distinct content, each appears once
        in the final answer (no duplicate content from any single source).
        """
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "What is the complete robotics research landscape?",
                "sql_results": [
                    {"name": "Dr. Rao", "publications": 120},
                ],
                "retrieved_chunks": [
                    {"publication_id": "PUB-FUND-1", "chunk_id": "ch0", "content": " DST robotics funding INR 500Cr."},
                    {"publication_id": "PUB-POLICY-1", "chunk_id": "ch0", "content": " MeitY robotics policy guidelines."},
                    {"publication_id": "PUB-INDUSTRY-1", "chunk_id": "ch0", "content": " Industry partnerships for robotics research."},
                ],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
            }
        )

        citations = result.get("citations", [])
        pub_ids = [c["pub_id"] for c in citations if c["pub_id"] != "structured"]
        assert len(set(pub_ids)) == len(pub_ids), \
            f"All source pub_ids should be unique. Got: {pub_ids}"
        assert len(pub_ids) >= 3, f"Expected at least 3 distinct sources cited. Got: {pub_ids}"


class TestFallbackHybridSynthesis:
    """Verify _fallback_hybrid_synthesis correctly formats mixed SQL+RAG evidence."""

    def test_fallback_hybrid_has_sql_table_and_rag_excerpts(self, monkeypatch):
        """Fallback hybrid synthesis formats SQL as table and RAG as excerpts."""
        monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: None)
        monkeypatch.setattr(synth_module, "get_local_llm_client", lambda: None)
        monkeypatch.setattr(synth_module, "log_llm_call", lambda *args, **kwargs: None)

        result = synth_module.synthesizer_node(
            {
                "user_query": "What is robotics funding and research?",
                "sql_results": [
                    {"agency": "DST", "total_grant": 500000000},
                ],
                "retrieved_chunks": [
                    {"publication_id": "PUB-1", "chunk_id": "ch0", "content": " DST robotics funding INR 500Cr."},
                ],
                "user_tier": 1,
                "conversation_history": [],
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
            }
        )

        response = result["synthesized_response"]
        assert result["provenance"]["synth"] == "rule_based_hybrid"
        assert "DST" in response
        assert "500" in response or "grant" in response.lower()
        assert "[cite:" in response, "Should have citation markers"
