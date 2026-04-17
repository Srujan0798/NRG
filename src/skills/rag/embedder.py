"""RAG Embedder - Local embedding generation using HuggingFace."""

import os
import logging
from typing import List, Optional
from pathlib import Path
import json

from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class Embedder:
    """Local embedding generator - fully offline."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "ai4bharat/IndicBERTv2-SS"
        )
        self._load_model()

    def _load_model(self):
        """Load embedding model (cached for reuse)."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Model load failed: {e}, using fallback")
            self.model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Fully offline after initial model load.
        """
        if self.model is None:
            return self._dummy_embeddings(len(texts))

        embeddings = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )

        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return self.embed([text])[0]

    def _dummy_embeddings(self, count: int) -> List[List[float]]:
        """Fallback for offline testing."""
        dim = 384
        import numpy as np

        np.random.seed(42)
        return np.random.randn(count, dim).tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()

    def close(self):
        pass


def main():
    """Test embedder."""
    embedder = Embedder()

    test_texts = [
        "Robotics research at IIT Gujarat",
        "Machine learning applications in healthcare",
        "Sustainable energy technologies",
    ]

    embeddings = embedder.embed(test_texts)

    print(f"Model: {embedder.model_name}")
    print(f"Dimension: {embedder.get_dimension()}")
    print(f"Texts embedded: {len(test_texts)}")
    print(f"Sample embedding[0][:5]: {embeddings[0][:5]}")


if __name__ == "__main__":
    main()
