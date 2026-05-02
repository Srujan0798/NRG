"""Compatibility import surface for RAG ingestion helpers."""

from src.skills.rag.ingest import ingest_documents, ingest_publications

__all__ = ["ingest_documents", "ingest_publications"]
