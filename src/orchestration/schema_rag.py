"""LB-8: Schema-RAG orchestration — retrieve top-k relevant DDL for Text-to-SQL.

Usage:
    from src.orchestration.schema_rag import SchemaRAG
    rag = SchemaRAG()
    chunks = rag.retrieve("Which IIT has the highest innovation credits?", top_k=5)
    # chunks = ["CREATE TABLE academic_courses_details (...)", ...]
"""

from __future__ import annotations

from typing import Any

from src.skills.text_to_sql.schema_retriever import SchemaRetriever, get_default_retriever


class SchemaRAG:
    """Orchestration wrapper for schema retrieval with semantic-layer awareness."""

    def __init__(self, retriever: SchemaRetriever | None = None) -> None:
        self._retriever = retriever
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        if self._retriever is None:
            self._retriever = get_default_retriever()
        self._retriever.load()
        self._initialized = True

    def _active_retriever(self) -> SchemaRetriever:
        self._init()
        assert self._retriever is not None
        return self._retriever

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Return top-k DDL chunks relevant to the natural-language query."""
        return self._active_retriever().retrieve_ddl(query, top_k=top_k)

    def retrieve_with_join_graph(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Return DDL chunks plus join-graph metadata for multi-hop queries."""
        retriever = self._active_retriever()
        ddl_chunks = retriever.retrieve_ddl(query, top_k=top_k)
        join_graph = retriever.get_join_graph_for_query(query)
        return {
            "ddl_chunks": ddl_chunks,
            "join_graph": join_graph,
            "token_estimate": sum(len(chunk) for chunk in ddl_chunks) // 4,
        }

    def get_glossary_hint(self, term: str) -> str | None:
        """Return glossary disambiguation hint for an ambiguous term."""
        return self._active_retriever().get_glossary_hint(term)

    def token_reduction_vs_full_schema(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Compare token count: schema-RAG vs full schema dump."""
        retriever = self._active_retriever()
        rag_chunks = retriever.retrieve_ddl(query, top_k=top_k)
        full_schema = retriever.get_full_schema_ddl()
        rag_tokens = sum(len(chunk) for chunk in rag_chunks) // 4
        full_tokens = len(full_schema) // 4
        return {
            "rag_tokens": rag_tokens,
            "full_tokens": full_tokens,
            "reduction_pct": round((1 - rag_tokens / max(full_tokens, 1)) * 100, 1),
            "tables_included": len(rag_chunks),
            "total_tables": retriever.table_count(),
        }
