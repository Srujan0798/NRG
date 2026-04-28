#!/usr/bin/env python3
"""Ingest the real NRG research-document corpus into Qdrant.

Default source: set via NRG_DATA_SOURCE_DIR env var
  (default: data/National_Research_Database/Research_Documents/)

The script parses YAML-like frontmatter from 3,310 `.txt` documents, chunks
body text into 512-token windows with 50-token overlap, embeds chunks, and
upserts idempotent Qdrant points into the same collection used by RAG.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from src.skills.rag.embedder import Embedder

_NRG_DATA_BASE = Path(
    os.getenv(
        "NRG_DATA_SOURCE_DIR",
        str(Path(__file__).resolve().parents[1] / "data" / "National_Research_Database"),
    )
)
DEFAULT_SOURCE_DIR = _NRG_DATA_BASE / "Research_Documents"
DEFAULT_PREBUILT_PATH = _NRG_DATA_BASE / "JSON_Data" / "qdrant_ready_payload.json"
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nrg_research")
DEFAULT_BATCH_SIZE = 100
DEFAULT_CHUNK_TOKENS = 512
DEFAULT_OVERLAP_TOKENS = 50
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
DEFAULT_FALLBACK_MODEL = os.getenv(
    "EMBEDDING_FALLBACK_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

logger = logging.getLogger(__name__)


def _qdrant_point_id(logical_point_id: str) -> str:
    """Qdrant requires point IDs to be uints or UUIDs; keep logical ID in payload."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"nrg:{logical_point_id}"))


@dataclass(frozen=True)
class ResearchDocument:
    document_id: str
    title: str
    researcher_ids: list[str]
    affiliation: str
    publication_year: int | None
    abstract: str
    keywords: list[str]
    research_area_tags: list[str]
    access_tier: str | int
    category: str
    body: str
    file_path: str = ""


@dataclass(frozen=True)
class PublicationRecord:
    """Backward-compatible record for the older abstract-ingest tests."""

    pub_id: str
    title: str
    abstract: str
    year: int | None
    institution: str
    keywords: list[str]


class _SentenceTransformerEmbedder:
    """Load bge-m3, with all-MiniLM fallback for dev machines."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        fallback_model: str = DEFAULT_FALLBACK_MODEL,
        deterministic: bool = False,
    ):
        self.model_name = model_name
        self._model: Any | None = None
        self.dimension = 0

        if deterministic:
            from src.skills.rag.embedder import _DeterministicTestEmbeddingModel

            self._model = _DeterministicTestEmbeddingModel(1024)
            self.model_name = "deterministic-1024"
            self.dimension = 1024
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            self.dimension = int(self._model.get_sentence_embedding_dimension())
            logger.info("Loaded embedding model %s (dim=%d)", self.model_name, self.dimension)
        except Exception as primary_error:
            logger.warning("Failed to load %s: %s", model_name, primary_error)
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(fallback_model)
                self.model_name = fallback_model
                self.dimension = int(self._model.get_sentence_embedding_dimension())
                logger.warning(
                    "Using fallback embedding model %s (dim=%d)",
                    self.model_name,
                    self.dimension,
                )
            except Exception as fallback_error:
                raise RuntimeError(
                    f"No embedding model available. Tried {model_name!r} and "
                    f"{fallback_model!r}: {fallback_error}"
                ) from fallback_error

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(  # type: ignore[union-attr]
            list(texts), convert_to_numpy=True, show_progress_bar=False
        )
        return [vector.tolist() for vector in vectors]


class _NullEmbedder:
    """Dry-run embedder that avoids model downloads."""

    model_name = "dry-run"
    dimension = 1024

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self.dimension for _ in texts]


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]
    if "," in text:
        return [part.strip().strip("[]'\"") for part in text.split(",") if part.strip()]
    return [text.strip("[]'\"")]


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def access_tier_to_int(tier: str | int | None) -> int:
    """Convert Tier1/Tier2/Tier3 or numeric values to 1/2/3."""
    if isinstance(tier, int):
        return tier if tier in {1, 2, 3} else 3
    text = str(tier or "Tier3").strip().lower().replace(" ", "")
    mapping = {
        "1": 1,
        "tier1": 1,
        "tier_1": 1,
        "tier-1": 1,
        "2": 2,
        "tier2": 2,
        "tier_2": 2,
        "tier-2": 2,
        "3": 3,
        "tier3": 3,
        "tier_3": 3,
        "tier-3": 3,
    }
    return mapping.get(text, 3)


def _parse_value(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in {'"', "'"} and value[-1:] == value[0]:
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _parse_frontmatter(frontmatter: str) -> dict[str, Any]:
    """Parse the flat YAML subset used in the generated NRG docs."""
    parsed: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] = []

    for raw_line in frontmatter.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-") and current_key:
            current_list.append(stripped[1:].strip().strip("'\""))
            parsed[current_key] = current_list
            continue

        current_key = None
        current_list = []
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            current_key = key
            current_list = []
            parsed[key] = current_list
        else:
            parsed[key] = _parse_value(value)

    return parsed


def _extract_markdown_abstract(body: str) -> str:
    """Best-effort abstract extraction for legacy markdown document formats."""
    patterns = [
        r"###\s*Abstract\s*\n(?P<abstract>.*?)(?:\n###|\n####|\n#|\Z)",
        r"\*\*Abstract:\*\*\s*(?P<abstract>.*?)(?:\n\*\*|\n#|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group("abstract")).strip()
    return ""


def _parse_legacy_metadata_document(text: str, path: Path) -> ResearchDocument | None:
    """Parse non-frontmatter docs that store metadata as JSON/Metadata blocks."""
    metadata_text = ""
    body = text

    if text.startswith("```json"):
        end = text.find("```", len("```json"))
        if end == -1:
            return None
        metadata_text = text[len("```json") : end].strip()
        body = text[end + len("```") :].strip()
    elif text.startswith("Metadata:"):
        start = text.find("{")
        end = text.find("\n}\n", start)
        if start == -1 or end == -1:
            return None
        metadata_text = text[start : end + 2].strip()
        body = text[end + 2 :].strip()
    else:
        return None

    # A few generated docs contain intentionally blank JSON fields as `"key":,`.
    metadata_text = re.sub(r'("[^"]+"\s*:\s*),', r"\1[],", metadata_text)
    try:
        meta = json.loads(metadata_text)
    except json.JSONDecodeError as exc:
        logger.warning("Skipping %s: metadata JSON parse failed: %s", path, exc)
        return None

    return ResearchDocument(
        document_id=str(meta.get("document_id") or path.stem).strip(),
        title=str(meta.get("title") or "").strip(),
        researcher_ids=_as_list(meta.get("researcher_ids")),
        affiliation=str(meta.get("affiliation") or "").strip(),
        publication_year=_coerce_int(meta.get("publication_year")),
        abstract=str(meta.get("abstract") or _extract_markdown_abstract(body)).strip(),
        keywords=_as_list(meta.get("keywords")),
        research_area_tags=_as_list(meta.get("research_area_tags")),
        access_tier=meta.get("access_tier") or "Tier3",
        category=str(meta.get("category") or "").strip(),
        body=body,
        file_path=str(path),
    )


def parse_document_txt(path: Path) -> ResearchDocument | None:
    """Parse one `.txt` document with frontmatter and markdown body."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return None

    if not text.startswith("---"):
        legacy_doc = _parse_legacy_metadata_document(text, path)
        if legacy_doc is not None:
            return legacy_doc
        logger.warning("Skipping %s: missing frontmatter", path)
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.warning("Skipping %s: malformed frontmatter", path)
        return None

    meta = _parse_frontmatter(parts[1])
    return ResearchDocument(
        document_id=str(meta.get("document_id") or path.stem).strip(),
        title=str(meta.get("title") or "").strip(),
        researcher_ids=_as_list(meta.get("researcher_ids")),
        affiliation=str(meta.get("affiliation") or "").strip(),
        publication_year=_coerce_int(meta.get("publication_year")),
        abstract=str(meta.get("abstract") or "").strip(),
        keywords=_as_list(meta.get("keywords")),
        research_area_tags=_as_list(meta.get("research_area_tags")),
        access_tier=meta.get("access_tier") or "Tier3",
        category=str(meta.get("category") or "").strip(),
        body=parts[2].strip(),
        file_path=str(path),
    )


def _document_from_prebuilt(entry: dict[str, Any]) -> tuple[ResearchDocument, list[float] | None]:
    meta = entry.get("metadata") or {}
    payload = entry.get("payload") or {}
    vector = entry.get("vector") or entry.get("embedding") or entry.get("vectors")
    if isinstance(vector, dict):
        vector = next(iter(vector.values()), None)
    if vector is not None:
        vector = [float(v) for v in vector]

    doc = ResearchDocument(
        document_id=str(meta.get("document_id") or entry.get("id") or "").strip(),
        title=str(meta.get("title") or "").strip(),
        researcher_ids=_as_list(meta.get("researcher_ids")),
        affiliation=str(meta.get("affiliation") or "").strip(),
        publication_year=_coerce_int(meta.get("publication_year")),
        abstract=str(meta.get("abstract") or payload.get("abstract") or "").strip(),
        keywords=_as_list(meta.get("keywords")),
        research_area_tags=_as_list(meta.get("research_area_tags")),
        access_tier=meta.get("access_tier") or "Tier3",
        category=str(meta.get("category") or "").strip(),
        body=str(payload.get("full_text") or payload.get("abstract") or "").strip(),
    )
    return doc, vector


def load_prebuilt_payload(path: Path) -> list[tuple[ResearchDocument, list[float] | None]]:
    """Load qdrant_ready_payload JSON; vectorless records are embedded normally."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}, got {type(data).__name__}")
    return [_document_from_prebuilt(entry) for entry in data]


def discover_txt_files(source_dir: Path) -> list[Path]:
    return sorted(source_dir.glob("*.txt"), key=lambda p: p.name)


def chunk_text(
    text: str,
    max_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap: int = DEFAULT_OVERLAP_TOKENS,
) -> list[str]:
    """Chunk text into approximate model-token windows.

    We split on whitespace but budget each word by a simple subword-token
    estimate. This keeps the default contract at 512 model tokens with
    50-token overlap, instead of under-counting long technical words as one
    token each.
    """
    words = re.findall(r"\S+", text)
    if not words:
        return []
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap < 0 or overlap >= max_tokens:
        raise ValueError("overlap must be >= 0 and smaller than max_tokens")

    chunks: list[str] = []
    token_costs = [max(1, (len(word) + 3) // 4) for word in words]
    start = 0

    while start < len(words):
        end = start
        budget = 0
        while end < len(words):
            next_cost = token_costs[end]
            if end > start and budget + next_cost > max_tokens:
                break
            budget += next_cost
            end += 1

        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break

        overlap_budget = 0
        next_start = end
        while next_start > start and overlap_budget < overlap:
            next_start -= 1
            overlap_budget += token_costs[next_start]
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks


def _chunk_abstract(
    text_value: str, chunk_tokens: int = DEFAULT_CHUNK_TOKENS, overlap_tokens: int = DEFAULT_OVERLAP_TOKENS
) -> list[str]:
    """Backward-compatible wrapper for the previous abstract ingester."""
    return chunk_text(text_value, max_tokens=chunk_tokens, overlap=overlap_tokens)


def _text_for_document(doc: ResearchDocument) -> str:
    if doc.abstract and doc.body:
        return f"{doc.abstract}\n\n{doc.body}"
    return doc.body or doc.abstract or doc.title


def _payload_for_chunk(
    doc: ResearchDocument, chunk_index: int, text: str, point_id: str
) -> dict[str, Any]:
    tier_int = access_tier_to_int(doc.access_tier)
    return {
        "point_id": point_id,
        "document_id": doc.document_id,
        "chunk_index": chunk_index,
        "chunk_id": str(chunk_index),
        "title": doc.title,
        "researcher_ids": doc.researcher_ids,
        "affiliation": doc.affiliation,
        "institution": doc.affiliation,
        "publication_year": doc.publication_year,
        "year": doc.publication_year,
        "research_area_tags": doc.research_area_tags,
        "topics": doc.research_area_tags,
        "keywords": doc.keywords,
        "access_tier": tier_int,
        "access_tier_label": f"Tier{tier_int}",
        "category": doc.category,
        "source_id": doc.document_id,
        "source_type": "research_document",
        "text": text,
        "content": text,
        "file_path": doc.file_path,
    }


def _points_from_documents(
    documents: Sequence[ResearchDocument],
    embedder: Any,
    show_progress: bool = True,
    embed_batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[PointStruct]:
    chunk_jobs: list[tuple[ResearchDocument, int, str, str]] = []
    iterator: Iterable[ResearchDocument] = documents
    if show_progress:
        iterator = tqdm(documents, desc="Chunking documents")

    for doc in iterator:
        chunks = chunk_text(_text_for_document(doc))
        if not chunks:
            continue
        for idx, chunk in enumerate(chunks):
            point_id = f"{doc.document_id}_{idx}"
            chunk_jobs.append((doc, idx, chunk, point_id))

    points: list[PointStruct] = []
    starts = range(0, len(chunk_jobs), embed_batch_size)
    embed_iter: Iterable[int] = starts
    if show_progress:
        embed_iter = tqdm(starts, desc="Embedding chunks")
    for start in embed_iter:
        batch = chunk_jobs[start : start + embed_batch_size]
        vectors = embedder.embed([chunk for _, _, chunk, _ in batch])
        for (doc, idx, chunk, point_id), vector in zip(batch, vectors):
            points.append(
                PointStruct(
                    id=_qdrant_point_id(point_id),
                    vector=vector,
                    payload=_payload_for_chunk(doc, idx, chunk, point_id),
                )
            )
    return points


def _points_from_prebuilt_vectors(
    records: Sequence[tuple[ResearchDocument, list[float] | None]],
) -> list[PointStruct] | None:
    points: list[PointStruct] = []
    for doc, vector in records:
        if vector is None:
            return None
        point_id = f"{doc.document_id}_0"
        points.append(
            PointStruct(
                id=_qdrant_point_id(point_id),
                vector=vector,
                payload=_payload_for_chunk(doc, 0, _text_for_document(doc), point_id),
            )
        )
    return points


def _collection_vector_size(client: QdrantClient, collection_name: str) -> int | None:
    try:
        vectors = client.get_collection(collection_name).config.params.vectors
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


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    recreate: bool = False,
) -> None:
    collections = {collection.name for collection in client.get_collections().collections}
    if recreate and collection_name in collections:
        client.delete_collection(collection_name)
        collections.remove(collection_name)

    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        return

    existing_size = _collection_vector_size(client, collection_name)
    if existing_size and existing_size != vector_size:
        logger.warning(
            "Recreating %s because vector size is %s, expected %s",
            collection_name,
            existing_size,
            vector_size,
        )
        client.delete_collection(collection_name)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def _load_documents(
    source_dir: Path,
    use_prebuilt: Path | None,
    limit: int | None,
    show_progress: bool,
) -> tuple[list[ResearchDocument], list[tuple[ResearchDocument, list[float] | None]] | None]:
    if use_prebuilt:
        records = load_prebuilt_payload(use_prebuilt)
        if limit is not None:
            records = records[:limit]
        return [doc for doc, _ in records], records

    files = discover_txt_files(source_dir)
    if limit is not None:
        files = files[:limit]

    documents: list[ResearchDocument] = []
    iterator: Iterable[Path] = files
    if show_progress:
        iterator = tqdm(files, desc="Parsing documents")
    for path in iterator:
        doc = parse_document_txt(path)
        if doc:
            documents.append(doc)
    return documents, None


def _upsert_batches(
    client: QdrantClient,
    collection_name: str,
    points: Sequence[PointStruct],
    batch_size: int,
    show_progress: bool,
) -> None:
    starts = range(0, len(points), batch_size)
    iterator: Iterable[int] = starts
    if show_progress:
        iterator = tqdm(starts, desc="Upserting to Qdrant")
    for start in iterator:
        client.upsert(collection_name=collection_name, points=list(points[start : start + batch_size]))


def _split_keywords(research_area: str | None) -> list[str]:
    if not research_area:
        return []
    raw = research_area.replace(";", ",").replace("|", ",")
    return [part.strip() for part in raw.split(",") if part.strip()]


def _fetch_publications(db: Any) -> list[PublicationRecord]:
    """Backward-compatible publication fetcher for the old smoke tests."""
    rows = db.execute(
        """
        SELECT publication_id, title, abstract, year
        FROM publications
        ORDER BY publication_id
        """
    )
    records: list[PublicationRecord] = []
    for row in rows:
        abstract = str(row.get("abstract") or "").strip()
        if not abstract:
            continue
        records.append(
            PublicationRecord(
                pub_id=str(row["publication_id"]),
                title=str(row.get("title") or ""),
                abstract=abstract,
                year=int(row["year"]) if row.get("year") is not None else None,
                institution="",
                keywords=[],
            )
        )
    return records


def ingest(
    database_url: str,
    qdrant_host: str,
    qdrant_port: int,
    collection: str,
    dry_run: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> tuple[int, int]:
    """Backward-compatible abstract-ingest API.

    New Task-B usage should call `ingest_qdrant()`. This wrapper remains so
    older tests and scripts that ingest publication abstracts keep working.
    """
    from src.data.database_v2 import NRGDatabase

    db = NRGDatabase(database_url)
    publications = _fetch_publications(db)
    chunk_count = sum(len(_chunk_abstract(pub.abstract)) for pub in publications)

    if dry_run:
        print(f"Ready to ingest {chunk_count} chunks from {len(publications)} publications")
        return len(publications), chunk_count

    embedder = Embedder(model_name=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    try:
        ensure_collection(client, collection, embedder.get_dimension())
        points: list[PointStruct] = []
        for publication in publications:
            chunks = _chunk_abstract(publication.abstract)
            vectors = embedder.embed(chunks)
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                points.append(
                    PointStruct(
                        id=f"{publication.pub_id}:{idx}",
                        vector=vector,
                        payload={
                            "pub_id": publication.pub_id,
                            "publication_id": publication.pub_id,
                            "source_id": publication.pub_id,
                            "source_type": "publication",
                            "chunk_index": idx,
                            "title": publication.title,
                            "year": publication.year,
                            "institution": publication.institution,
                            "keywords": publication.keywords,
                            "access_tier": 1,
                            "text": chunk,
                        },
                    )
                )

        for start in range(0, len(points), batch_size):
            client.upsert(collection_name=collection, points=points[start : start + batch_size])
        return len(publications), chunk_count
    finally:
        embedder.close()


def ingest_qdrant(
    source_dir: Path = DEFAULT_SOURCE_DIR,
    collection: str = DEFAULT_COLLECTION,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    batch_size: int = DEFAULT_BATCH_SIZE,
    limit: int | None = None,
    dry_run: bool = False,
    use_prebuilt: Path | None = None,
    recreate: bool = False,
    embedding_model: str = DEFAULT_MODEL,
    fallback_model: str = DEFAULT_FALLBACK_MODEL,
    deterministic: bool = False,
    show_progress: bool = True,
    client: QdrantClient | None = None,
    embedder: Any | None = None,
) -> dict[str, Any]:
    """Ingest documents into Qdrant and return a summary dict."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    documents, prebuilt_records = _load_documents(source_dir, use_prebuilt, limit, show_progress)
    if embedder is None:
        embedder = (
            _NullEmbedder()
            if dry_run
            else _SentenceTransformerEmbedder(
                model_name=embedding_model,
                fallback_model=fallback_model,
                deterministic=deterministic,
            )
        )

    prebuilt_vector_count = 0
    if prebuilt_records is not None:
        prebuilt_points = _points_from_prebuilt_vectors(prebuilt_records)
        if prebuilt_points is not None:
            points = prebuilt_points
            prebuilt_vector_count = len(points)
        else:
            points = _points_from_documents(
                documents, embedder, show_progress=show_progress, embed_batch_size=batch_size
            )
    else:
        points = _points_from_documents(
            documents, embedder, show_progress=show_progress, embed_batch_size=batch_size
        )

    vector_size = int(getattr(embedder, "dimension", 0) or (len(points[0].vector) if points else 0))
    summary = {
        "collection": collection,
        "documents": len(documents),
        "points": len(points),
        "vector_size": vector_size,
        "embedding_model": getattr(embedder, "model_name", embedding_model),
        "prebuilt_vectors": prebuilt_vector_count,
        "dry_run": dry_run,
    }

    if dry_run:
        return summary

    if client is None:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
    ensure_collection(client, collection, vector_size, recreate=recreate)
    _upsert_batches(client, collection, points, batch_size, show_progress=show_progress)
    summary["collection_points"] = int(client.get_collection(collection).points_count or 0)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest NRG research documents into Qdrant")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--qdrant-host", default=os.getenv("QDRANT_HOST", "localhost"))
    parser.add_argument("--qdrant-port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--use-prebuilt",
        nargs="?",
        const=DEFAULT_PREBUILT_PATH,
        type=Path,
        default=None,
        help="Use JSON_Data/qdrant_ready_payload.json or a supplied path",
    )
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument("--fallback-model", default=DEFAULT_FALLBACK_MODEL)
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args()
    summary = ingest_qdrant(
        source_dir=args.source_dir,
        collection=args.collection,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        batch_size=args.batch_size,
        limit=args.limit,
        dry_run=args.dry_run,
        use_prebuilt=args.use_prebuilt,
        recreate=args.recreate,
        embedding_model=args.embedding_model,
        fallback_model=args.fallback_model,
        deterministic=args.deterministic,
        show_progress=not args.no_progress,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
