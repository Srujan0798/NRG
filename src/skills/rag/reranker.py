"""RAG reranker using bge-reranker-v2-m3 with deterministic fallback."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class RerankerUnavailable(RuntimeError):
    """Raised when reranking cannot run and fallback is disabled."""


class Reranker:
    """Rerank retrieved candidates to the top-k most relevant items."""

    def __init__(self, model_name: str | None = None, fallback: bool = True):
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
        self.fallback = fallback
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        if self.fallback and (
            os.getenv("PYTEST_CURRENT_TEST")
            or os.getenv("RERANKER_DISABLE_MODEL", "").lower() in {"1", "true", "yes"}
        ):
            self.model = None
            return

        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(self.model_name)
            logger.info("Loaded reranker model: %s", self.model_name)
        except Exception as exc:
            if not self.fallback:
                raise RerankerUnavailable(f"Failed to load reranker: {exc}") from exc
            logger.warning("Reranker unavailable; preserving retriever order: %s", exc)
            self.model = None

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        if not candidates:
            return []

        if self.model is None:
            return candidates[:top_k]

        pairs = [(query, _candidate_text(candidate)) for candidate in candidates]
        scores = self.model.predict(pairs)
        ranked = []
        for candidate, score in zip(candidates, scores):
            updated = dict(candidate)
            updated["rerank_score"] = float(score)
            ranked.append(updated)

        ranked.sort(key=lambda item: item.get("rerank_score", 0.0), reverse=True)
        return ranked[:top_k]


def _candidate_text(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("chunk_text")
        or candidate.get("content")
        or candidate.get("text")
        or candidate.get("abstract")
        or candidate.get("title")
        or ""
    )
