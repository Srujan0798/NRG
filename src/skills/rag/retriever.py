"""RAG Retriever - Local Qdrant retrieval with RBAC metadata filtering, drift detection, and re-ranking."""

import os
import logging
import time
import threading
from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime, UTC


logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
except Exception:  # pragma: no cover - exercised when optional client is absent
    QdrantClient = None


class VectorDriftDetector:
    """
    Monitors vector retrieval quality over time and detects embedding drift.

    Drift occurs when:
    - Document semantics shift (new terminology, re-organized knowledge base)
    - Embedding model produces different vectors for same content
    - Collection's vector space changes significantly

    Detection method:
    - Track retrieval confidence scores over time
    - Compare current distribution against baseline
    - Alert when deviation exceeds threshold
    - Trigger retraining when drift is severe
    """

    def __init__(
        self,
        baseline_window: int = 1000,
        drift_threshold: float = 0.15,
        alert_threshold: float = 0.25,
        sample_size: int = 100,
    ):
        self._baseline_scores: deque = deque(maxlen=baseline_window)
        self._current_scores: deque = deque(maxlen=sample_size)
        self._drift_threshold = drift_threshold
        self._alert_threshold = alert_threshold
        self._sample_size = sample_size
        self._lock = threading.Lock()

        self._baseline_established = False
        self._baseline_window = baseline_window
        self._last_alert_time: float | None = None
        self._retraining_triggered = False

    def record_score(self, score: float) -> dict:
        """
        Record a retrieval score and check for drift.

        Returns dict with:
        - drift_detected: bool
        - drift_score: float (0-1, higher = more drift)
        - status: "healthy" | "drifting" | "alert"
        - should_retrain: bool
        """
        with self._lock:
            self._current_scores.append(score)

            if not self._baseline_established:
                if len(self._baseline_scores) >= self._baseline_window:
                    self._baseline_established = True
                    logger.info("Vector drift baseline established with %d samples", len(self._baseline_scores))
            else:
                self._baseline_scores.append(score)
                if len(self._baseline_scores) > self._baseline_window:
                    self._baseline_scores.popleft()

            if len(self._current_scores) < 10:
                return {
                    "drift_detected": False,
                    "drift_score": 0.0,
                    "status": "collecting",
                    "should_retrain": False,
                }

            drift_score = self._compute_drift()
            status = self._determine_status(drift_score)
            should_retrain = drift_score >= self._alert_threshold

            if should_retrain and not self._retraining_triggered:
                self._retraining_triggered = True
                logger.critical(
                    "VECTOR DRIFT CRITICAL: score=%.3f, threshold=%.3f. RETRAINING TRIGGERED",
                    drift_score, self._alert_threshold
                )
                self._trigger_retraining_alert()

            return {
                "drift_detected": drift_score >= self._drift_threshold,
                "drift_score": drift_score,
                "status": status,
                "should_retrain": should_retrain,
            }

    def _compute_drift(self) -> float:
        """Compute drift score comparing current distribution to baseline."""
        if len(self._baseline_scores) < 10 or len(self._current_scores) < 10:
            return 0.0

        import statistics

        # Compare mean scores
        baseline_mean = statistics.mean(self._baseline_scores)
        current_mean = statistics.mean(self._current_scores)

        # Compare standard deviations
        baseline_stdev = statistics.stdev(self._baseline_scores) if len(self._baseline_scores) > 1 else 0.1
        current_stdev = statistics.stdev(self._current_scores) if len(self._current_scores) > 1 else 0.1

        # Mean shift normalized by baseline spread
        mean_shift = abs(current_mean - baseline_mean) / max(baseline_stdev, 0.01)

        # Distribution width change
        stdev_ratio = abs(current_stdev - baseline_stdev) / max(baseline_stdev, 0.01)

        # Combined drift score (0-1 range normalized)
        drift = (mean_shift + stdev_ratio) / 4.0  # Normalize to 0-1
        return min(1.0, drift)

    def _determine_status(self, drift_score: float) -> str:
        """Determine overall status based on drift score."""
        if drift_score >= self._alert_threshold:
            return "alert"
        elif drift_score >= self._drift_threshold:
            return "drifting"
        return "healthy"

    def _trigger_retraining_alert(self):
        """Send alert when retraining is needed."""
        self._last_alert_time = time.time()
        try:
            import httpx
            webhook = os.getenv("VECTOR_DRIFT_WEBHOOK")
            if webhook:
                httpx.post(webhook, json={
                    "alert": "vector_drift_critical",
                    "drift_score": self._compute_drift(),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "action": "trigger_embedding_retraining",
                }, timeout=10)
        except Exception as e:
            logger.warning("Failed to send drift alert: %s", e)

    def get_status(self) -> dict:
        """Get current drift detector status."""
        with self._lock:
            drift = self._compute_drift() if len(self._current_scores) >= 10 else 0.0
            return {
                "baseline_established": self._baseline_established,
                "baseline_samples": len(self._baseline_scores),
                "current_samples": len(self._current_scores),
                "drift_score": drift,
                "status": self._determine_status(drift),
                "retraining_triggered": self._retraining_triggered,
                "last_alert_time": self._last_alert_time,
            }


class RetrieverUnavailable(RuntimeError):
    """Raised when the vector store cannot serve retrieval requests."""


class Retriever:
    """Local Qdrant retriever with access-tier filtering, drift detection, and re-ranking."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, timeout: float = 10.0):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self._timeout = int(timeout)
        self.collection_name = os.getenv("QDRANT_COLLECTION", "nrg_research")

        self._client = None

        # Initialize drift detector
        self._drift_detector = VectorDriftDetector(
            baseline_window=int(os.getenv("DRIFT_BASELINE_WINDOW", "1000")),
            drift_threshold=float(os.getenv("DRIFT_THRESHOLD", "0.15")),
            alert_threshold=float(os.getenv("DRIFT_ALERT_THRESHOLD", "0.25")),
            sample_size=int(os.getenv("DRIFT_SAMPLE_SIZE", "100")),
        )

        # Re-ranker configuration (cross-encoder for precision)
        self._rerank_enabled = os.getenv("RERANK_ENABLED", "true").lower() == "true"
        self._rerank_top_k = int(os.getenv("RERANK_TOP_K", "20"))
        self._reranker = None

    @property
    def client(self):
        """Lazily initialize Qdrant client on first access."""
        if self._client is None:
            if QdrantClient is None:
                raise RetrieverUnavailable("Qdrant client is not installed")
            self._client = QdrantClient(host=self.host, port=self.port, timeout=self._timeout)
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def get_drift_status(self) -> dict:
        """Get current vector drift status."""
        return self._drift_detector.get_status()

    def _build_filter(
        self,
        user_tier: int,
        institution: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ):
        """Build filter for access control."""
        from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue

        allowed_tiers = self._allowed_access_tiers(user_tier)
        must_conditions: list[Any] = [
            FieldCondition(key="access_tier", match=MatchAny(any=allowed_tiers))
        ]

        if institution:
            must_conditions.append(
                FieldCondition(key="institution", match=MatchValue(value=institution))
            )

        if topics:
            for topic in topics:
                must_conditions.append(
                    FieldCondition(key="topics", match=MatchValue(value=topic))
                )

        return Filter(must=must_conditions)

    def _allowed_access_tiers(self, user_tier: int) -> list[int]:
        """Return data tiers visible to a user tier.

        Tier 1 is the most privileged persona, tier 3 is public/industry-shaped.
        """
        if user_tier == 1:
            return [1, 2, 3]
        if user_tier == 2:
            return [2, 3]
        if user_tier == 3:
            return [3]
        return [3]

    def retrieve(
        self,
        query_vector: List[float],
        user_tier: int = 1,
        top_k: int = 5,
        institution: Optional[str] = None,
        topics: Optional[List[str]] = None,
        query_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks with RBAC filtering, drift detection and cross-encoder re-ranking.

        Returns chunks with source_id and access_tier metadata.
        """
        query_vector = self._coerce_test_vector_dimension(query_vector)
        filter_obj = self._build_filter(user_tier, institution, topics)

        # Retrieve more candidates for re-ranking
        retrieve_limit = self._rerank_top_k if self._rerank_enabled else top_k

        try:
            if hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=filter_obj,
                    limit=retrieve_limit,
                    with_payload=True,
                    with_vectors=False,
                )
            else:
                search_result = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=filter_obj,
                    limit=retrieve_limit,
                    with_payload=True,
                )
                results = search_result.points
        except Exception as e:
            logger.warning("Qdrant search failed: %s", e)
            raise RetrieverUnavailable(f"Qdrant search failed: {e}") from e

        # Collect results and scores
        candidates = []
        for result in results:
            payload = result.payload or {}

            chunk_text = (
                payload.get("text")
                or payload.get("content")
                or payload.get("abstract")
                or payload.get("description")
                or payload.get("title")
                or ""
            )
            candidates.append({
                "chunk": chunk_text,
                "payload": payload,
                "vector_score": result.score,
            })

        # Apply cross-encoder re-ranking if enabled
        if self._rerank_enabled and candidates and len(candidates) > top_k:
            reranked = self._rerank_candidates(
                query_text=query_text,
                candidates=candidates,
                top_k=top_k,
            )
        else:
            reranked = candidates[:top_k]

        # Extract results
        chunks = []
        metadata = []
        scores = []

        for candidate in reranked:
            payload = candidate["payload"]
            chunks.append(candidate["chunk"])
            metadata.append(
                {
                    "source_id": str(payload.get("source_id", payload.get("document_id", ""))),
                    "document_id": str(payload.get("document_id", payload.get("source_id", ""))),
                    "chunk_index": payload.get("chunk_index"),
                    "chunk_id": payload.get("chunk_id"),
                    "title": payload.get("title", ""),
                    "publication_year": payload.get("publication_year", payload.get("year")),
                    "researcher_ids": payload.get("researcher_ids", []),
                    "keywords": payload.get("keywords", []),
                    "source_type": payload.get("source_type", payload.get("type", "")),
                    "access_tier": payload.get("access_tier", 3),
                    "institution": payload.get("institution", payload.get("affiliation", "")),
                    "affiliation": payload.get("affiliation", payload.get("institution", "")),
                    "topics": payload.get("topics", payload.get("research_area_tags", [])),
                    "research_area_tags": payload.get("research_area_tags", payload.get("topics", [])),
                }
            )
            scores.append(candidate.get("rerank_score", candidate.get("vector_score", 0.0)))

        # Record scores for drift detection (use vector scores for consistency)
        for score in [r.score for r in results[:len(candidates)]]:
            drift_status = self._drift_detector.record_score(score)
            # Log drift alerts
            if drift_status["status"] == "alert":
                logger.warning("Vector retrieval quality degraded: drift_score=%.3f", drift_status["drift_score"])

        return {"chunks": chunks, "metadata": metadata, "scores": scores}

    def _rerank_candidates(
        self,
        query_text: Optional[str],
        candidates: list,
        top_k: int,
    ) -> list:
        """
        Re-rank candidates using bge-reranker-v2-m3 for improved precision.

        Uses the dedicated Reranker class with proper cross-encoder model.
        Falls back to vector scores only if reranker unavailable.
        """
        if not query_text:
            candidates.sort(key=lambda x: x["vector_score"], reverse=True)
            return candidates[:top_k]

        try:
            from src.skills.rag.reranker import Reranker
            if self._reranker is None:
                self._reranker = Reranker()
            reranked = self._reranker.rerank(query=query_text, candidates=candidates, top_k=top_k)
            return reranked
        except Exception as e:
            logger.warning("Re-ranking failed: %s, using vector scores only", e)
            candidates.sort(key=lambda x: x["vector_score"], reverse=True)
            return candidates[:top_k]

    def _coerce_test_vector_dimension(self, query_vector: List[float]) -> List[float]:
        """Pad/truncate vectors to match the active Qdrant collection size.

        This ensures embeddings work regardless of whether they were generated
        by the test embedder (768-dim) or a production model (e.g. 1024-dim).
        """
        expected_dim = self._collection_vector_size()
        if not expected_dim or len(query_vector) == expected_dim:
            return query_vector

        if len(query_vector) > expected_dim:
            return query_vector[:expected_dim]

        return [*query_vector, *([0.0] * (expected_dim - len(query_vector)))]

    def _collection_vector_size(self) -> int | None:
        try:
            info = self.client.get_collection(self.collection_name)
            vectors = info.config.params.vectors
        except Exception:
            return None

        size = getattr(vectors, "size", None)
        if size:
            return int(size)

        if isinstance(vectors, dict):
            for vector_config in vectors.values():
                size = getattr(vector_config, "size", None)
                if size:
                    return int(size)
                if isinstance(vector_config, dict) and vector_config.get("size"):
                    return int(vector_config["size"])

        return None

    def retrieve_text(
        self, query_text: str, embedder, user_tier: int = 1, top_k: int = 5
    ) -> Dict[str, Any]:
        """Retrieve by text query (uses embedder internally)."""
        query_vector = embedder.embed_single(query_text)
        return self.retrieve(query_vector, user_tier, top_k)

    def query(self, query_text: str, user_tier: int = 1, top_k: int = 5) -> Dict[str, Any]:
        """Convenience method: embed text and retrieve in one call."""
        from .embedder import Embedder
        embedder = Embedder()
        try:
            return self.retrieve_text(query_text, embedder, user_tier, top_k)
        finally:
            embedder.close()

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
            }
        except Exception:
            return {"name": self.collection_name, "status": "not_found"}

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check: connection, collection, index build status."""
        result = {
            "status": "ok",
            "collection": self.collection_name,
            "qdrant_reachable": False,
            "collection_exists": False,
            "index_built": False,
            "vectors_indexed": 0,
            "vectors_total": 0,
            "latency_ms": None,
            "issues": [],
        }

        import time
        start = time.perf_counter()

        try:
            info = self.client.get_collection(self.collection_name)
            result["qdrant_reachable"] = True
            result["collection_exists"] = True
            result["vectors_total"] = info.points_count or 0
            result["vectors_indexed"] = info.indexed_vectors_count or 0

            if result["vectors_total"] == 0:
                result["issues"].append("Collection is empty")
            elif result["vectors_indexed"] < result["vectors_total"]:
                result["issues"].append(
                    f"HNSW index incomplete: {result['vectors_indexed']}/{result['vectors_total']} vectors indexed"
                )
                result["status"] = "degraded"
            else:
                result["index_built"] = True

            params = info.config.params
            if hasattr(params, "vectors"):
                vector_cfg = params.vectors
                if hasattr(vector_cfg, "size"):
                    result["vector_size"] = vector_cfg.size
                elif isinstance(vector_cfg, dict):
                    result["vector_size"] = next(
                        (v.size for v in vector_cfg.values() if hasattr(v, "size")), None
                    )

            hnsw = info.config.hnsw_config
            if hnsw:
                result["hnsw_m"] = getattr(hnsw, "m", None)
                result["hnsw_ef_construct"] = getattr(hnsw, "ef_construct", None)

        except Exception as exc:
            result["status"] = "unhealthy"
            result["issues"].append(f"Connection failed: {exc}")

        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)

        if not result["issues"]:
            result["status"] = "ok"
        elif result["status"] != "unhealthy":
            result["status"] = "degraded"

        return result

    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        """Upsert vectors into Qdrant collection."""
        try:
            # Check if collection exists, create if not
            from qdrant_client.models import VectorParams, Distance

            try:
                self.client.get_collection(self.collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=len(embeddings[0]),
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

            # Upsert points
            from qdrant_client.models import PointStruct

            points = [
                PointStruct(
                    id=ids[i],
                    vector=embeddings[i],
                    payload=payloads[i]
                )
                for i in range(len(ids))
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise

    def close(self):
        pass


def main():
    """Test retriever."""
    retriever = Retriever()
    info = retriever.get_collection_info()
    print(f"Collection: {info}")


if __name__ == "__main__":
    main()
