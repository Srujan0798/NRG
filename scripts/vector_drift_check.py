#!/usr/bin/env python3
"""
Vector Drift Detection — NRG Knowledge Quality Monitor

Runs weekly (or on-demand) to detect vector search quality degradation.
Compares current retrieval results against a known-good benchmark.

SLO: Drift score > 0.85 (perfect match = 1.0, no overlap = 0.0)
Breach: Drift score < 0.60 → WARNING, < 0.40 → CRITICAL

Usage:
    python scripts/vector_drift_check.py [--verbose] [--json-output]
    python scripts/vector_drift_check.py --check-only  # Just report, no alerting
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.rag.retriever import Retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("drift_check")


BENCHMARK_QUERIES = [
    {
        "query": "machine learning researchers in Gujarat",
        "expected_sources": ["IIT Gandhinagar", "Dhirubhai Ambani", "DA-IICT"],
        "expected_topics": ["machine learning", "robotics", "artificial intelligence"],
    },
    {
        "query": "robotics research labs in India",
        "expected_sources": ["IIT Bombay", "IIT Madras", "IIT Delhi"],
        "expected_topics": ["robotics", "control systems", "automation"],
    },
    {
        "query": "artificial intelligence trends 2024",
        "expected_sources": ["IIT", "IIIT", "NIT"],
        "expected_topics": ["deep learning", "neural networks", "nlp"],
    },
    {
        "query": "sustainable energy research funding",
        "expected_sources": ["MNRE", "DST", "CSIR"],
        "expected_topics": ["solar", "wind", "hydrogen", "renewable"],
    },
    {
        "query": "biotechnology publications 2023",
        "expected_sources": ["IIT", "AIIMS", "NIT"],
        "expected_topics": ["genomics", "CRISPR", "bioinformatics"],
    },
    {
        "query": "quantum computing research India",
        "expected_sources": ["IIT", "IISc", "QIC"],
        "expected_topics": ["quantum", "qubit", "cryptography"],
    },
    {
        "query": "data science researchers Maharashtra",
        "expected_sources": ["IIT Bombay", "COEP", "VJTI"],
        "expected_topics": ["data science", "analytics", "machine learning"],
    },
    {
        "query": "renewable energy collaboration international",
        "expected_sources": ["USA", "Germany", "Japan", "Israel"],
        "expected_topics": ["solar", "wind", "green hydrogen"],
    },
    {
        "query": "computer vision research Karnataka",
        "expected_sources": ["IISc", "IIIT Bangalore", "NIT Surathkal"],
        "expected_topics": ["computer vision", "image processing", "CV"],
    },
    {
        "query": "natural language processing researchers Tamil Nadu",
        "expected_sources": ["IIT Madras", "SSN", "Anna University"],
        "expected_topics": ["NLP", "text mining", "LLM"],
    },
]

DRIFT_SCORE_SLO = 0.85
DRIFT_SCORE_WARNING = 0.60
DRIFT_SCORE_CRITICAL = 0.40
COSINE_SHIFT_THRESHOLD = 0.05
DRIFT_CACHE_DIR = Path(os.getenv("NRG_DRIFT_CACHE_DIR", str(Path(__file__).parent.parent / ".cache")))
BENCHMARK_CACHE_FILE = DRIFT_CACHE_DIR / "drift_benchmark.json"
LATEST_RESULTS_FILE = DRIFT_CACHE_DIR / "drift_latest.json"
REFERENCE_CENTROIDS_FILE = DRIFT_CACHE_DIR / "reference_centroids.json"
DEFAULT_STATUS_FILE = DRIFT_CACHE_DIR / "vector_drift_status.json"


def _status_file() -> Path:
    return Path(os.getenv("NRG_VECTOR_DRIFT_STATUS_FILE", str(DEFAULT_STATUS_FILE)))


def _write_status_file(payload: dict) -> None:
    """Persist the latest vector drift status for the API /health endpoint."""
    status_payload = dict(payload)
    alert_level = str(status_payload.get("alert_level", "")).upper()
    if "status" not in status_payload:
        status_payload["status"] = "healthy" if alert_level in {"GREEN", "AMBER"} else "unhealthy"
    status_payload.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    path = _status_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status_payload, indent=2, default=str))


def _load_reference_centroids() -> dict[str, list[float]]:
    """Load cached reference centroids from disk."""
    if not REFERENCE_CENTROIDS_FILE.exists():
        return {}
    try:
        return json.loads(REFERENCE_CENTROIDS_FILE.read_text())
    except Exception:
        return {}


def _save_reference_centroids(data: dict[str, list[float]]):
    """Persist reference centroids after computing from fresh indexing."""
    REFERENCE_CENTROIDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE_CENTROIDS_FILE.write_text(json.dumps(data, indent=2))


def _compute_centroids(retriever: Retriever, embedder) -> dict[str, list[float]]:
    """Compute current mean vectors for each benchmark topic cluster."""
    centroids: dict[str, list[float]] = {}
    for bench in BENCHMARK_QUERIES:
        topic = bench["expected_topics"][0] if bench["expected_topics"] else bench["query"][:30]
        try:
            query_vector = embedder.embed_single(bench["query"])
            result = retriever.retrieve(query_vector=query_vector, user_tier=1, top_k=5)
            chunks = result.get("chunks", [])
            if chunks:
                chunk_vectors = [embedder.embed_single(c) for c in chunks]
                n = len(chunk_vectors)
                centroid = [sum(v[i] for v in chunk_vectors) / n for i in range(len(chunk_vectors[0]))]
                import math
                norm = math.sqrt(sum(v * v for v in centroid))
                centroid = [v / norm for v in centroid]
                centroids[topic] = centroid
        except Exception:
            pass
    return centroids


def _cosine_shift(current: list[float], reference: list[float]) -> float:
    """Compute cosine distance between two vectors. 0=identical, 1=opposite."""
    import math
    dot = sum(a * b for a, b in zip(current, reference))
    norm_a = math.sqrt(sum(a * a for a in current))
    norm_b = math.sqrt(sum(b * b for b in reference))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return 0.5 * (1.0 - dot / (norm_a * norm_b))


def _check_cosine_shift(drift_result: dict, retriever: Retriever, embedder) -> dict:
    """Check cosine shift against reference centroids and trigger reindex if needed."""
    reference = _load_reference_centroids()
    if not reference:
        current = _compute_centroids(retriever, embedder)
        _save_reference_centroids(current)
        return {"status": "baseline_established", "reindex_triggered": False}

    current = _compute_centroids(retriever, embedder)
    max_shift = 0.0
    shifting_topics = []
    for topic, ref_vec in reference.items():
        if topic in current:
            shift = _cosine_shift(current[topic], ref_vec)
            if shift > COSINE_SHIFT_THRESHOLD:
                shifting_topics.append(topic)
                max_shift = max(max_shift, shift)

    if shifting_topics:
        return {
            "status": "cosine_shift_detected",
            "max_shift": round(max_shift, 4),
            "shifting_topics": shifting_topics,
            "reindex_triggered": True,
        }
    return {"status": "stable", "max_shift": round(max_shift, 4), "reindex_triggered": False}


def _trigger_reindex(drift_result: dict, reindex_info: dict):
    """POST to /api/reindex when drift or cosine shift is critical."""
    import httpx
    reindex_url = os.getenv("NRG_API_URL", "http://localhost:8000") + "/api/reindex"
    token = os.getenv("NRG_SERVICE_TOKEN", os.getenv("INTERNAL_SERVICE_TOKEN", ""))
    if not token:
        logger.warning("No service token for reindex trigger - skipping POST")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "reason": f"vector_drift:{drift_result['alert_level']}",
        "drift_score": drift_result["drift_score"],
        "cosine_shift": reindex_info.get("max_shift", 0),
        "shifting_topics": reindex_info.get("shifting_topics", []),
    }
    try:
        resp = httpx.post(reindex_url, json=payload, headers=headers, timeout=15)
        if resp.status_code in (200, 201, 202):
            logger.info("Reindex triggered successfully: %s", resp.json())
        else:
            logger.warning("Reindex trigger failed: %d %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Failed to POST /api/reindex: %s", e)


def _load_benchmark_cache() -> dict:
    """Load cached benchmark results from last run."""
    if not BENCHMARK_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(BENCHMARK_CACHE_FILE.read_text())
    except Exception:
        return {}


def _save_benchmark_cache(data: dict):
    """Save current benchmark results for next comparison."""
    BENCHMARK_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_CACHE_FILE.write_text(json.dumps(data, indent=2, default=str))


def _save_latest_results(data: dict):
    """Save the latest drift run without mutating the known-good baseline."""
    LATEST_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LATEST_RESULTS_FILE.write_text(json.dumps(data, indent=2, default=str))


def _jaccard_overlap(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def run_drift_check(retriever: Retriever, verbose: bool = False) -> dict:
    """Run drift detection against benchmark queries.

    Returns dict with drift_score, per_query_scores, and alert level.
    """
    baseline_results = _load_benchmark_cache()
    latest_results = {}
    per_query_scores = []
    topic_overlaps = []
    embedder = None
    embedder_error: Exception | None = None

    try:
        from src.skills.rag.embedder import Embedder

        embedder = Embedder()
    except Exception as exc:
        embedder_error = exc
        logger.warning("Embedding model unavailable for drift check: %s", exc)

    try:
        for i, bench in enumerate(BENCHMARK_QUERIES):
            query = bench["query"]
            baseline_entry = baseline_results.get(query, {})
            has_baseline = (
                isinstance(baseline_entry, dict)
                and not baseline_entry.get("error")
                and (
                    baseline_entry.get("sources")
                    or baseline_entry.get("topics")
                )
            )
            expected_sources = set(
                baseline_entry.get("sources", [])
                if has_baseline
                else bench["expected_sources"]
            )
            expected_topics = set(
                baseline_entry.get("topics", [])
                if has_baseline
                else bench["expected_topics"]
            )

            try:
                if embedder_error is not None:
                    raise embedder_error
                if embedder is None:
                    raise RuntimeError("Embedding model unavailable for drift check")

                query_vector = embedder.embed_single(query)

                retrieval_result = retriever.retrieve(
                    query_vector=query_vector,
                    user_tier=1,
                    top_k=5,
                )
                metadata = retrieval_result.get("metadata", [])

                retrieved_sources = set()
                retrieved_topics = set()

                for item in metadata:
                    source = item.get("institution", "") or item.get("source", "")
                    if source:
                        retrieved_sources.add(source.lower())
                    topics = item.get("topics", []) or item.get("research_area_tags", [])
                    for t in topics:
                        retrieved_topics.add(t.lower())

                expected_sources_lower = {s.lower() for s in expected_sources}
                source_overlap = _jaccard_overlap(retrieved_sources, expected_sources_lower)

                expected_topics_lower = {t.lower() for t in expected_topics}
                topic_overlap = _jaccard_overlap(retrieved_topics, expected_topics_lower)

                query_score = (source_overlap * 0.4) + (topic_overlap * 0.6)

                per_query_scores.append({
                    "query": query,
                    "source_overlap": round(source_overlap, 3),
                    "topic_overlap": round(topic_overlap, 3),
                    "score": round(query_score, 3),
                    "baseline": "cache" if has_baseline else "static",
                })
                topic_overlaps.append(query_score)

                if verbose:
                    logger.info(
                        "  [%d/%d] '%s' → source=%.2f topic=%.2f score=%.3f",
                        i + 1, len(BENCHMARK_QUERIES), query[:50],
                        source_overlap, topic_overlap, query_score
                    )

                latest_results[query] = {
                    "sources": list(retrieved_sources),
                    "topics": list(retrieved_topics),
                    "score": query_score,
                    "timestamp": time.time(),
                }

            except Exception as exc:
                logger.warning("Query %d failed: %s", i + 1, exc)
                per_query_scores.append({
                    "query": query,
                    "source_overlap": 0.0,
                    "topic_overlap": 0.0,
                    "score": 0.0,
                    "error": str(exc),
                })
                topic_overlaps.append(0.0)
                latest_results[query] = {"error": str(exc), "timestamp": time.time()}

        avg_score = sum(topic_overlaps) / len(topic_overlaps) if topic_overlaps else 0.0

        alert_level = "GREEN"
        if avg_score < DRIFT_SCORE_CRITICAL:
            alert_level = "CRITICAL"
            logger.critical(
                "DRIFT CRITICAL: Score %.3f < %.3f threshold. "
                "Vector embeddings may be corrupted or the wrong model was used.",
                avg_score, DRIFT_SCORE_CRITICAL
            )
        elif avg_score < DRIFT_SCORE_WARNING:
            alert_level = "WARNING"
            logger.warning(
                "DRIFT WARNING: Score %.3f < %.3f threshold. "
                "Retrieval quality has degraded — review recent data ingestion.",
                avg_score, DRIFT_SCORE_WARNING
            )
        elif avg_score < DRIFT_SCORE_SLO:
            alert_level = "AMBER"
            logger.info(
                "DRIFT AMBER: Score %.3f < %.3f SLO target. "
                "Quality is acceptable but below target.",
                avg_score, DRIFT_SCORE_SLO
            )
        else:
            logger.info("DRIFT OK: Score %.3f >= %.3f SLO target", avg_score, DRIFT_SCORE_SLO)

        _save_latest_results(latest_results)

        try:
            if alert_level in {"WARNING", "CRITICAL"}:
                _trigger_reindex(
                    {"alert_level": alert_level, "drift_score": avg_score},
                    {
                        "status": "benchmark_drift_detected",
                        "reindex_triggered": True,
                    },
                )
            elif embedder is not None:
                cosine_info = _check_cosine_shift({}, retriever, embedder)
                if cosine_info.get("reindex_triggered"):
                    _trigger_reindex(
                        {"alert_level": alert_level, "drift_score": avg_score},
                        cosine_info
                    )
        except Exception as e:
            logger.warning("Cosine shift check failed: %s", e)

        return {
            "drift_score": round(avg_score, 3),
            "alert_level": alert_level,
            "slo_target": DRIFT_SCORE_SLO,
            "warning_threshold": DRIFT_SCORE_WARNING,
            "critical_threshold": DRIFT_SCORE_CRITICAL,
            "queries_checked": len(BENCHMARK_QUERIES),
            "per_query": per_query_scores,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    finally:
        if embedder is not None:
            embedder.close()


def establish_baseline(retriever: Retriever, verbose: bool = False) -> dict:
    """Persist a fresh vector drift benchmark and reference centroid baseline."""
    from src.skills.rag.embedder import Embedder

    embedder = Embedder()
    benchmark_results = {}
    try:
        for bench in BENCHMARK_QUERIES:
            query = bench["query"]
            try:
                query_vector = embedder.embed_single(query)
                retrieval_result = retriever.retrieve(
                    query_vector=query_vector,
                    user_tier=1,
                    top_k=5,
                )
                metadata = retrieval_result.get("metadata", [])
                sources = []
                topics = []
                for item in metadata:
                    source = item.get("institution", "") or item.get("source", "")
                    if source:
                        sources.append(source.lower())
                    for topic in item.get("topics", []) or item.get("research_area_tags", []):
                        topics.append(topic.lower())

                benchmark_results[query] = {
                    "sources": sorted(set(sources)),
                    "topics": sorted(set(topics)),
                    "timestamp": time.time(),
                }
            except Exception as exc:
                benchmark_results[query] = {"error": str(exc), "timestamp": time.time()}
                if verbose:
                    logger.warning("Baseline query failed for '%s': %s", query, exc)

        centroids = _compute_centroids(retriever, embedder)
        _save_reference_centroids(centroids)
        _save_benchmark_cache(benchmark_results)

        return {
            "status": "baseline_established",
            "queries_saved": len(benchmark_results),
            "centroids_saved": len(centroids),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    finally:
        embedder.close()


def run_health_check(retriever: Retriever) -> dict:
    """Get Qdrant health for the drift report."""
    health = retriever.health_check()
    indexed = health.get("vectors_indexed", 0)
    total = health.get("vectors_total", 0)
    coverage_pct = (indexed / total * 100) if total > 0 else 0.0
    return {
        "indexed_vectors": indexed,
        "total_vectors": total,
        "coverage_pct": round(coverage_pct, 2),
        "status": health.get("status"),
        "index_built": bool(health.get("index_built")),
        "latency_ms": health.get("latency_ms"),
    }


def _qdrant_ready_for_benchmark(qdrant_health: dict) -> bool:
    """Return True when Qdrant has a reachable, non-empty vector collection."""
    status = qdrant_health.get("status")
    indexed = int(qdrant_health.get("indexed_vectors") or 0)
    index_built = bool(qdrant_health.get("index_built"))
    total = int(qdrant_health.get("total_vectors") or 0)

    return status in {"ok", "degraded"} and total > 0 and (indexed > 0 or index_built)


def main():
    parser = argparse.ArgumentParser(description="NRG Vector Drift Detection")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    parser.add_argument("--check-only", action="store_true",
                        help="Skip benchmark comparison, just show current health")
    parser.add_argument("--establish-baseline", action="store_true",
                        help="Persist current Qdrant retrieval state as the drift baseline")
    args = parser.parse_args()

    logger.info("Starting NRG Vector Drift Detection")
    logger.info("SLO target: drift_score >= %.2f", DRIFT_SCORE_SLO)
    logger.info("WARNING threshold: %.2f | CRITICAL threshold: %.2f",
                DRIFT_SCORE_WARNING, DRIFT_SCORE_CRITICAL)

    retriever = Retriever(timeout=5.0)

    qdrant_health = run_health_check(retriever)
    logger.info(
        "Qdrant health: %s | Indexed: %d/%d (%.1f%%) | Latency: %sms",
        qdrant_health["status"],
        qdrant_health["indexed_vectors"],
        qdrant_health["total_vectors"],
        qdrant_health["coverage_pct"],
        qdrant_health["latency_ms"],
    )

    if args.check_only:
        status = {
            "status": "healthy" if _qdrant_ready_for_benchmark(qdrant_health) else "unhealthy",
            "alert_level": "GREEN" if _qdrant_ready_for_benchmark(qdrant_health) else "UNKNOWN",
            "qdrant": qdrant_health,
        }
        _write_status_file(status)
        print(json.dumps({"qdrant": qdrant_health}, indent=2, default=str))
        return

    if args.establish_baseline:
        if not _qdrant_ready_for_benchmark(qdrant_health):
            result = {
                "status": "baseline_skipped",
                "message": "Qdrant is unhealthy or empty; baseline was not changed.",
                "qdrant": qdrant_health,
            }
            print(json.dumps(result, indent=2, default=str))
            sys.exit(2)
        baseline = establish_baseline(retriever, verbose=args.verbose)
        _write_status_file({
            "status": "healthy",
            "alert_level": "GREEN",
            "baseline": baseline,
            "qdrant": qdrant_health,
        })
        print(json.dumps({"baseline": baseline, "qdrant": qdrant_health}, indent=2, default=str))
        sys.exit(0)

    if not _qdrant_ready_for_benchmark(qdrant_health):
        result = {
            "status": "qdrant_unavailable",
            "message": "Vector drift benchmark skipped because Qdrant is unhealthy or empty.",
            "qdrant": qdrant_health,
        }
        if args.json_output:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("\n" + "=" * 60)
            print("VECTOR DRIFT CHECK SKIPPED")
            print("=" * 60)
            print(result["message"])
            print(f"Qdrant status: {qdrant_health.get('status')}")
            print(
                "Vectors: "
                f"{qdrant_health.get('indexed_vectors', 0)}/"
                f"{qdrant_health.get('total_vectors', 0)}"
            )
            print("=" * 60)
        sys.exit(2)

    drift_result = run_drift_check(retriever, verbose=args.verbose)
    _write_status_file({**drift_result, "qdrant": qdrant_health})

    print("\n" + "=" * 60)
    print("VECTOR DRIFT REPORT")
    print("=" * 60)
    print(f"  Drift Score:    {drift_result['drift_score']:.3f}")
    print(f"  Alert Level:   {drift_result['alert_level']}")
    print(f"  Queries:        {drift_result['queries_checked']}")
    print(f"  SLO Target:     >={drift_result['slo_target']:.2f}")
    print(f"  WARNING:        <{drift_result['warning_threshold']:.2f}")
    print(f"  CRITICAL:       <{drift_result['critical_threshold']:.2f}")
    print("-" * 60)

    if args.verbose or args.json_output:
        print("\nPer-Query Scores:")
        for q in drift_result["per_query"]:
            print(f"  [{q['score']:.3f}] {q['query'][:60]}")
    print("=" * 60)

    if args.json_output:
        output = {
            "drift": drift_result,
            "qdrant": qdrant_health,
        }
        print(json.dumps(output, indent=2, default=str))

    is_healthy = drift_result["alert_level"] in ("GREEN", "AMBER")
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()
