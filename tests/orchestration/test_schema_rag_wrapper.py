"""Regression coverage for the LB-8 SchemaRAG orchestration wrapper."""

from src.orchestration.schema_rag import SchemaRAG
from src.skills.text_to_sql.schema_retriever import SchemaRetriever


class KeywordOnlyEmbedder:
    def embed(self, chunks):
        return []


def _rag() -> SchemaRAG:
    retriever = SchemaRetriever(embedder=KeywordOnlyEmbedder())
    return SchemaRAG(retriever)


def test_schema_rag_retrieve_returns_ddl_chunks():
    chunks = _rag().retrieve("grant funding by institute", top_k=3)

    assert chunks
    assert all("CREATE TABLE" in chunk for chunk in chunks)
    assert any("innovation_grant_from_govt" in chunk for chunk in chunks)


def test_schema_rag_join_graph_and_glossary_are_available():
    rag = _rag()

    payload = rag.retrieve_with_join_graph(
        "FDI investment and seed funding for startups",
        top_k=3,
    )
    hint = rag.get_glossary_hint("status")

    assert payload["ddl_chunks"]
    assert "join_graph" in payload
    assert payload["token_estimate"] > 0
    assert hint and "patent_status" in hint


def test_schema_rag_token_reduction_uses_parsed_full_schema():
    stats = _rag().token_reduction_vs_full_schema("innovation credits", top_k=3)

    assert stats["rag_tokens"] > 0
    assert stats["full_tokens"] > stats["rag_tokens"]
    assert stats["reduction_pct"] > 0
    assert stats["total_tables"] >= stats["tables_included"]
