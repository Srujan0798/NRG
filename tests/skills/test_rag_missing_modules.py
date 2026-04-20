def test_rag_ingest_and_reranker_modules_import():
    from src.skills.rag.ingest import ingest_publications
    from src.skills.rag.reranker import Reranker

    assert callable(ingest_publications)
    assert Reranker is not None
