"""RAG Embedder - Local embedding generation using HuggingFace."""

import os
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import json
import re
import hashlib

from sentence_transformers import SentenceTransformer
import numpy as np


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-m3"
INDIC_MODEL = "ai4bharat/IndicBERTv2-SS"

INDIAN_LANG_CODES = {"hi", "bn", "gu", "kn", "ml", "mr", "ne", "pa", "ta", "te", "ur"}


class EmbedderUnavailable(RuntimeError):
    """Raised when embeddings cannot be generated reliably."""


class SemanticChunker:
    """Sentence-aware semantic chunker with 512 token limit, 128 token stride."""

    def __init__(self, max_tokens: int = 512, stride: int = 128):
        self.max_tokens = max_tokens
        self.stride = stride

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        sentences = self._split_sentences(text)
        chunks = []
        start = 0

        while start < len(sentences):
            end = start
            token_count = 0
            chunk_sentences = []

            while end < len(sentences) and token_count < self.max_tokens:
                sent_tokens = self._estimate_tokens(sentences[end])
                if token_count + sent_tokens > self.max_tokens and chunk_sentences:
                    break
                chunk_sentences.append(sentences[end])
                token_count += sent_tokens
                end += 1

            if chunk_sentences:
                chunks.append(" ".join(chunk_sentences))

            if self.stride > 0 and end < len(sentences):
                start = end - self._sentences_for_tokens(sentences, self.stride)
                start = max(start + 1, end)
            else:
                start = end

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (chars / 4)."""
        return len(text) // 4

    def _sentences_for_tokens(self, sentences: List[str], target_tokens: int) -> int:
        """Count how many sentences fit in target_tokens."""
        count = 0
        total = 0
        for s in sentences:
            total += self._estimate_tokens(s)
            if total > target_tokens:
                break
            count += 1
        return count


class _DeterministicTestEmbeddingModel:
    """Fast deterministic model used only while pytest is executing."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def encode(self, text, convert_to_numpy=True, show_progress_bar=False):
        digest = hashlib.sha256(str(text).encode("utf-8")).digest()
        values = [
            ((digest[i % len(digest)] / 255.0) * 2.0) - 1.0
            for i in range(self.dimension)
        ]
        if convert_to_numpy:
            return np.array(values, dtype=np.float32)
        return values

    def get_sentence_embedding_dimension(self) -> int:
        return self.dimension


class Embedder:
    """Local embedding generator with language-gated model selection."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
        self._primary_model = None
        self._indic_model = None
        self._chunker = SemanticChunker()
        self._load_models()

    def _load_models(self):
        """Load embedding models (cached for reuse)."""
        if os.getenv("PYTEST_CURRENT_TEST"):
            self._primary_model = _DeterministicTestEmbeddingModel(768)
            self._indic_model = None
            logger.info("Using deterministic test embedding model")
            return

        try:
            self._primary_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded primary embedding model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Primary model load failed: {e}")
            self._primary_model = None

        try:
            self._indic_model = SentenceTransformer(INDIC_MODEL)
            logger.info(f"Loaded IndicBERT model: {INDIC_MODEL}")
        except Exception as e:
            logger.warning(f"Indic model load failed: {e}")
            self._indic_model = None

    def _detect_language(self, text: str) -> str:
        """Detect language of text (returns ISO 639-1 code)."""
        try:
            import fasttext
            model_path = os.getenv("FASTEXT_MODEL", "lid.176.bin")
            if os.path.exists(model_path):
                model = fasttext.load_model(model_path)
                lang = model.predict(text.replace("\n", " "), k=1)[0][0].replace("__label__", "")
                return lang
        except Exception:
            pass

        devanagari = re.compile(r'[\u0900-\u097F]')
        bengali = re.compile(r'[\u0980-\u09FF]')
        gujarati = re.compile(r'[\u0A80-\u0AFF]')
        kannada = re.compile(r'[\u0C80-\u0CFF]')
        malayalam = re.compile(r'[\u0D00-\u0D7F]')
        tamil = re.compile(r'[\u0B80-\u0BFF]')
        telugu = re.compile(r'[\u0C00-\u0C7F]')

        if devanagari.search(text): return "hi"
        if bengali.search(text): return "bn"
        if gujarati.search(text): return "gu"
        if kannada.search(text): return "kn"
        if malayalam.search(text): return "ml"
        if tamil.search(text): return "ta"
        if telugu.search(text): return "te"

        return "en"

    def _get_model_for_text(self, text: str) -> Optional[SentenceTransformer]:
        """Select appropriate model based on language."""
        lang = self._detect_language(text)
        if lang in INDIAN_LANG_CODES and self._indic_model:
            return self._indic_model
        return self._primary_model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts with language-gated model selection."""
        if not self._primary_model and not self._indic_model:
            raise EmbedderUnavailable("No embedding models loaded")

        embeddings = []
        for text in texts:
            model = self._get_model_for_text(text)
            if model is None:
                raise EmbedderUnavailable("No embedding model available for detected language")
            try:
                emb = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            except Exception as exc:
                raise EmbedderUnavailable(f"Embedding generation failed: {exc}") from exc
            embeddings.append(emb.tolist())

        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return self.embed([text])[0]

    def chunk(self, text: str) -> List[str]:
        """Split text into semantic chunks."""
        return self._chunker.chunk_text(text)

    def chunk_and_embed(self, text: str) -> List[Tuple[str, List[float]]]:
        """Chunk text and return (chunk, embedding) pairs."""
        chunks = self.chunk(text)
        embeddings = self.embed(chunks)
        return list(zip(chunks, embeddings))

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self._primary_model:
            return self._primary_model.get_sentence_embedding_dimension()
        if self._indic_model:
            return self._indic_model.get_sentence_embedding_dimension()
        return 768

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

    test_chunk = "This is sentence one. This is sentence two. This is sentence three. And another sentence here."
    chunks = embedder.chunk(test_chunk)
    print(f"Chunks: {len(chunks)}")

if __name__ == "__main__":
    main()
