#!/usr/bin/env python3
"""Repair stale Qdrant points that have placeholder vectors or missing metadata.

The local NRG vector collection can be created by older data flows that stored
only ``abstract``/``full_text`` payload fields with zero vectors. That state is
reachable, but it cannot serve RBAC-filtered RAG because every point is missing
``access_tier`` and the vectors do not carry semantic signal.

This script is intentionally conservative:
- it only enriches existing points in-place;
- it defaults missing records to Tier 3 public access rather than broad access;
- it does not remove existing payload fields;
- it supports ``--dry-run`` for evidence before mutation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nrg_research")
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
DEFAULT_BATCH_SIZE = 64
DEFAULT_MAX_EMBED_CHARS = 1800

KNOWN_INSTITUTIONS = [
    "IIT Gandhinagar",
    "Dhirubhai Ambani",
    "DA-IICT",
    "IIT Bombay",
    "IIT Madras",
    "IIT Delhi",
    "IISc",
    "Indian Institute of Science",
    "IIIT Bangalore",
    "NIT Surathkal",
    "Anna University",
    "SSN",
    "AIIMS",
    "NIT",
    "COEP",
    "VJTI",
    "CSIR",
    "DST",
    "MNRE",
    "QIC",
]

TOPIC_PATTERNS = {
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "robotics": [r"\brobotics\b", r"\bmanipulation\b", r"\bcontrol systems?\b", r"\bautomation\b"],
    "artificial intelligence": [r"\bartificial intelligence\b", r"\bgenerative ai\b", r"\bai\b"],
    "deep learning": [r"\bdeep learning\b", r"\bneural networks?\b"],
    "natural language processing": [r"\bnatural language processing\b", r"\bnlp\b", r"\btext mining\b", r"\bllm\b"],
    "computer vision": [r"\bcomputer vision\b", r"\bimage processing\b", r"\bmedical image\b"],
    "data science": [r"\bdata science\b", r"\banalytics\b"],
    "quantum computing": [r"\bquantum computing\b", r"\bquantum\b", r"\bqubit\b", r"\bcryptography\b"],
    "renewable energy": [r"\brenewable energy\b", r"\bsolar\b", r"\bwind\b", r"\bgreen hydrogen\b", r"\bhydrogen\b"],
    "biotechnology": [r"\bbiotechnology\b", r"\bgenomics\b", r"\bcrispr\b", r"\bbioinformatics\b", r"\bproteomics\b"],
}


@dataclass(frozen=True)
class RepairCandidate:
    point_id: Any
    text: str
    payload: dict[str, Any]
    vector_norm: float | None
    needs_repair: bool


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def text_from_payload(payload: dict[str, Any], max_chars: int = DEFAULT_MAX_EMBED_CHARS) -> str:
    """Return the strongest available text field for embedding and metadata."""
    parts = [
        payload.get("title"),
        payload.get("abstract"),
        payload.get("text"),
        payload.get("content"),
        payload.get("full_text"),
    ]
    text = "\n\n".join(_normalize_text(part) for part in parts if _normalize_text(part))
    return text[:max_chars]


def vector_norm(vector: Any) -> float | None:
    if isinstance(vector, dict):
        vector = next(iter(vector.values()), None)
    if not vector:
        return None
    return math.sqrt(sum(float(value) * float(value) for value in vector))


def infer_public_metadata(point_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Infer non-sensitive public retrieval metadata from existing text."""
    text = text_from_payload(payload, max_chars=12000)
    lower = text.lower()

    institutions = [
        institution
        for institution in KNOWN_INSTITUTIONS
        if institution.lower() in lower
    ]
    topics = []
    for topic, patterns in TOPIC_PATTERNS.items():
        if any(re.search(pattern, lower) for pattern in patterns):
            topics.append(topic)

    title = _normalize_text(payload.get("title"))
    if not title:
        title = _normalize_text(payload.get("abstract"))[:120] or f"NRG vector record {point_id}"

    institution = institutions[0] if institutions else "NRG research corpus"
    source_id = str(payload.get("source_id") or payload.get("document_id") or point_id)

    return {
        "source_id": source_id,
        "document_id": str(payload.get("document_id") or source_id),
        "source_type": payload.get("source_type") or "research_document",
        "title": title,
        "institution": payload.get("institution") or payload.get("affiliation") or institution,
        "affiliation": payload.get("affiliation") or payload.get("institution") or institution,
        "topics": payload.get("topics") or payload.get("research_area_tags") or topics,
        "research_area_tags": payload.get("research_area_tags") or payload.get("topics") or topics,
        "keywords": payload.get("keywords") or topics,
        "access_tier": int(payload.get("access_tier") or 3),
        "access_tier_label": payload.get("access_tier_label") or "Tier3",
        "text": payload.get("text") or payload.get("content") or _normalize_text(payload.get("abstract")),
        "content": payload.get("content") or payload.get("text") or text,
        "metadata_repair": {
            "tool": "scripts/repair_qdrant_payloads.py",
            "reason": "missing_retrieval_metadata_or_zero_vector",
            "default_access_tier": 3,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }


def _iter_points(
    client: QdrantClient,
    collection: str,
    limit: int | None = None,
    max_embed_chars: int = DEFAULT_MAX_EMBED_CHARS,
) -> Iterable[RepairCandidate]:
    offset = None
    seen = 0
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        for point in points:
            if limit is not None and seen >= limit:
                return
            payload = point.payload or {}
            norm = vector_norm(point.vector)
            text = text_from_payload(payload, max_chars=max_embed_chars)
            needs_repair = (
                not payload.get("access_tier")
                or not payload.get("source_id")
                or not payload.get("topics")
                or not payload.get("institution")
                or norm is None
                or norm < 1e-9
            )
            seen += 1
            yield RepairCandidate(point.id, text, payload, norm, needs_repair)
        if offset is None:
            return


def _load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def repair_collection(
    collection: str,
    host: str,
    port: int,
    model_name: str,
    batch_size: int,
    dry_run: bool,
    limit: int | None = None,
    max_embed_chars: int = DEFAULT_MAX_EMBED_CHARS,
    client: QdrantClient | None = None,
    model: Any | None = None,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    client = client or QdrantClient(host=host, port=port, timeout=60)
    candidates = list(_iter_points(client, collection, limit=limit, max_embed_chars=max_embed_chars))
    repairable = [candidate for candidate in candidates if candidate.needs_repair and candidate.text]
    zero_vectors = sum(1 for candidate in candidates if candidate.vector_norm is None or candidate.vector_norm < 1e-9)
    missing_tier = sum(1 for candidate in candidates if not candidate.payload.get("access_tier"))

    summary: dict[str, Any] = {
        "collection": collection,
        "points_scanned": len(candidates),
        "repairable_points": len(repairable),
        "zero_vector_points": zero_vectors,
        "missing_access_tier_points": missing_tier,
        "dry_run": dry_run,
        "model": model_name,
        "max_embed_chars": max_embed_chars,
    }
    if dry_run or not repairable:
        return summary

    model = model or _load_sentence_transformer(model_name)
    updated = 0
    for start in range(0, len(repairable), batch_size):
        batch = repairable[start : start + batch_size]
        texts = [candidate.text for candidate in batch]
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        points = []
        for candidate, vector in zip(batch, vectors):
            payload = dict(candidate.payload)
            payload.update(infer_public_metadata(candidate.point_id, candidate.payload))
            points.append(
                PointStruct(
                    id=candidate.point_id,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )
        client.upsert(collection_name=collection, points=points)
        updated += len(points)

    summary["points_updated"] = updated
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair stale NRG Qdrant vectors and payload metadata")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--host", default=os.getenv("QDRANT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-embed-chars", type=int, default=DEFAULT_MAX_EMBED_CHARS)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = repair_collection(
        collection=args.collection,
        host=args.host,
        port=args.port,
        model_name=args.model,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        limit=args.limit,
        max_embed_chars=args.max_embed_chars,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
