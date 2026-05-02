#!/usr/bin/env python3
"""
Ingest Documents into NRG Vector Store — The Living Pipeline

Supports: CSV files, PDF files, and plain-text files/directories.
Pipeline: Read → Chunk (512 tokens, 50 overlap) → Embed (bge-m3) → Upsert to Qdrant

Features:
- Duplicate detection by content hash (SHA256)
- Incremental updates (only new/modified documents)
- Batch upsert (100 documents at a time with progress bar)
- Progress reporting: ingested, skipped (duplicate), failed

Usage:
    python scripts/ingest_documents.py --source ./data/papers.csv --collection nrg_research
    python scripts/ingest_documents.py --source ./research_docs/ --collection nrg_research
    python scripts/ingest_documents.py --source ./papers.pdf --collection nrg_research

SKILLS: /python-backend (FastAPI async patterns), /data-visualization (progress bars)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nrg_research")
DEFAULT_BATCH_SIZE = 100
DEFAULT_CHUNK_TOKENS = 512
DEFAULT_OVERLAP_TOKENS = 50
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDER_DIM = 1024 if "bge-m3" in DEFAULT_MODEL else 384

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_text(text: str, chunk_tokens: int = 512, overlap_tokens: int = 50) -> list[str]:
    """Split text into overlapping chunks of ~chunk_tokens tokens (~4 chars per token)."""
    chunk_chars = chunk_tokens * 4
    overlap_chars = overlap_tokens * 4
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_chars
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_chars - overlap_chars
    return chunks


@dataclass
class DocumentRecord:
    document_id: str
    title: str
    content: str
    metadata: dict[str, Any]


def _parse_csv(source_path: Path) -> Iterator[DocumentRecord]:
    """Parse CSV file into DocumentRecord objects.

    Expected CSV columns: id, title, content (or body, abstract, text)
    Additional columns are stored as metadata.
    """
    with open(source_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            doc_id = row.get("id", row.get("document_id", f"doc-{i}"))
            title = row.get("title", row.get("name", f"Document {i}"))
            content = (
                row.get("content")
                or row.get("body")
                or row.get("abstract")
                or row.get("text")
                or ""
            )
            if not content.strip():
                continue
            metadata = {k: v for k, v in row.items() if k not in ("id", "document_id", "title", "content", "body", "abstract", "text")}
            yield DocumentRecord(
                document_id=str(doc_id),
                title=str(title),
                content=content,
                metadata=metadata,
            )


def _parse_txt_directory(source_path: Path) -> Iterator[DocumentRecord]:
    """Parse all .txt files in a directory.

    Files are parsed as: first line = title, rest = content.
    Filename is used as document_id.
    """
    for txt_file in sorted(source_path.glob("*.txt")):
        try:
            text = txt_file.read_text(encoding="utf-8")
            lines = text.split("\n", 1)
            title = lines[0].strip() if lines else txt_file.stem
            content = lines[1].strip() if len(lines) > 1 else ""
            if not content.strip():
                continue
            yield DocumentRecord(
                document_id=txt_file.stem,
                title=title,
                content=content,
                metadata={"source_file": str(txt_file)},
            )
        except Exception as e:
            logger.warning(f"Failed to parse {txt_file}: {e}")


def _parse_pdf(source_path: Path) -> Iterator[DocumentRecord]:
    """Extract text from a PDF file using pdfplumber or PyPDF2."""
    try:
        import pdfplumber
    except ImportError:
        try:
            import PyPDF2

            with open(source_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                content = "\n".join(text_parts)
                if content.strip():
                    yield DocumentRecord(
                        document_id=source_path.stem,
                        title=source_path.stem,
                        content=content,
                        metadata={"source_file": str(source_path), "page_count": len(reader.pages)},
                    )
            return
        except ImportError:
            logger.error("PDF parsing requires pdfplumber or PyPDF2: pip install pdfplumber")
            return

    try:
        with pdfplumber.open(source_path) as pdf:
            all_text = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                all_text.append(text)
            content = "\n".join(all_text)
            if content.strip():
                yield DocumentRecord(
                    document_id=source_path.stem,
                    title=source_path.stem,
                    content=content,
                    metadata={"source_file": str(source_path), "page_count": len(pdf.pages)},
                )
    except Exception as e:
        logger.warning(f"Failed to parse PDF {source_path}: {e}")


def _detect_source_type(source_path: Path) -> str:
    if source_path.is_dir():
        txt_files = list(source_path.glob("*.txt"))
        csv_files = list(source_path.glob("*.csv"))
        if csv_files and not txt_files:
            return "csv_directory"
        return "txt_directory"
    elif source_path.suffix.lower() == ".csv":
        return "csv"
    elif source_path.suffix.lower() == ".pdf":
        return "pdf"
    elif source_path.suffix.lower() == ".txt":
        return "txt"
    else:
        return "unknown"


def _load_embedder(model_name: str = DEFAULT_MODEL) -> Any:
    """Load the embedding model with fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except Exception as e:
        logger.warning(f"Failed to load {model_name}: {e}. Using fallback.")
        try:
            return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            logger.error("Could not load any embedding model. Install: pip install sentence-transformers")
            raise


def _get_existing_hashes(qdrant: QdrantClient, collection: str) -> set[str]:
    """Get set of existing document hashes in the collection for dedup."""
    existing = set()
    try:
        scroll_result = qdrant.scroll(
            collection_name=collection,
            scroll_filter=None,
            limit=1000,
            with_payload=True,
        )
        for point in scroll_result[0]:
            payload = point.payload or {}
            doc_hash = payload.get("document_hash")
            if doc_hash:
                existing.add(doc_hash)
    except Exception as e:
        logger.warning(f"Could not fetch existing hashes from Qdrant: {e}")
    return existing


def _ensure_collection(qdrant: QdrantClient, collection: str) -> None:
    """Create collection if it doesn't exist."""
    try:
        qdrant.get_collection(collection)
        logger.info(f"Collection '{collection}' already exists")
    except Exception:
        logger.info(f"Creating collection '{collection}'")
        qdrant.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDER_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Collection '{collection}' created with dimension {EMBEDDER_DIM}")


def _embed_chunks(embedder: Any, chunks: list[str]) -> list[list[float]]:
    """Embed text chunks using the loaded model."""
    if hasattr(embedder, "encode"):
        embeddings = embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]
    return [[0.0] * embedder.dimension]


def _ingest_stream(
    source_path: Path,
    collection: str,
    qdrant: QdrantClient,
    embedder: Any,
    batch_size: int = DEFAULT_BATCH_SIZE,
    skip_existing: bool = True,
    progress: bool = True,
) -> dict[str, int]:
    """
    Core ingestion loop: detects source type, processes documents, embeds, upserts.
    Returns: {ingested: int, skipped: int, failed: int}
    """
    source_type = _detect_source_type(source_path)
    logger.info(f"Source type: {source_type}")

    existing_hashes = set()
    if skip_existing:
        existing_hashes = _get_existing_hashes(qdrant, collection)

    _ensure_collection(qdrant, collection)

    if source_type in ("csv", "csv_directory"):
        if source_type == "csv":
            doc_iter: Iterator[DocumentRecord] = _parse_csv(source_path)
        else:
            csv_files = list(source_path.glob("*.csv"))
            doc_iter: Iterator[DocumentRecord] = (_parse_csv(f) for f in csv_files for _ in [next(iter(_parse_csv(f)))] if True)

        def flatten_csv():
            for f in sorted(source_path.glob("*.csv")):
                yield from _parse_csv(f)

        doc_iter = flatten_csv()
    elif source_type == "txt_directory":
        doc_iter = _parse_txt_directory(source_path)
    elif source_type == "txt":
        doc_iter = _parse_txt(source_path)
    elif source_type == "pdf":
        doc_iter = _parse_pdf(source_path)
    else:
        raise ValueError(f"Unknown source type: {source_type}")

    ingested = skipped = failed = 0
    batch: list[PointStruct] = []
    batch_chunks: list[tuple[str, str, dict]] = []
    total_docs = 0

    pbar = tqdm(desc="Ingesting documents", unit="doc") if progress and tqdm else None

    for doc in doc_iter:
        total_docs += 1
        doc_hash = _sha256(doc.content)
        if skip_existing and doc_hash in existing_hashes:
            skipped += 1
            if pbar:
                pbar.update(1)
            continue

        chunks = _chunk_text(doc.content, DEFAULT_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS)
        try:
            chunk_embeddings = _embed_chunks(embedder, chunks)
        except Exception as e:
            logger.warning(f"Embedding failed for {doc.document_id}: {e}")
            failed += 1
            if pbar:
                pbar.update(1)
            continue

        for chunk_idx, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            point_id = f"{doc.document_id}:{chunk_idx}"
            payload = {
                "document_id": doc.document_id,
                "document_hash": doc_hash,
                "title": doc.title,
                "content": chunk_text,
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks),
                **{k: v for k, v in doc.metadata.items()},
            }
            batch.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )
            batch_chunks.append((point_id, doc.document_id, doc_hash))

        ingested += 1
        if pbar:
            pbar.update(1)

        if len(batch) >= batch_size:
            try:
                qdrant.upsert(collection_name=collection, points=batch)
            except Exception as e:
                logger.warning(f"Qdrant upsert failed: {e}")
                failed += len(batch)
                ingested -= len(batch_chunks)
            batch.clear()
            batch_chunks.clear()

    if batch:
        try:
            qdrant.upsert(collection_name=collection, points=batch)
        except Exception as e:
            logger.warning(f"Qdrant upsert failed: {e}")
            failed += len(batch)
            ingested -= len(batch_chunks)

    if pbar:
        pbar.close()

    logger.info(f"Ingestion complete: {ingested} ingested, {skipped} skipped (duplicate), {failed} failed out of {total_docs} total")
    return {"ingested": ingested, "skipped": skipped, "failed": failed, "total": total_docs}


def _parse_txt(source_path: Path) -> Iterator[DocumentRecord]:
    """Parse a single .txt file."""
    try:
        text = source_path.read_text(encoding="utf-8")
        lines = text.split("\n", 1)
        title = lines[0].strip() if lines else source_path.stem
        content = lines[1].strip() if len(lines) > 1 else ""
        if content.strip():
            yield DocumentRecord(
                document_id=source_path.stem,
                title=title,
                content=content,
                metadata={"source_file": str(source_path)},
            )
    except Exception as e:
        logger.warning(f"Failed to parse {source_path}: {e}")


detect_source_type = _detect_source_type
embed_chunks = _embed_chunks
ensure_collection = _ensure_collection
get_existing_hashes = _get_existing_hashes
load_embedder = _load_embedder
parse_csv = _parse_csv
parse_pdf = _parse_pdf
parse_txt = _parse_txt
parse_txt_directory = _parse_txt_directory
sha256_text = _sha256


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into NRG vector store")
    parser.add_argument("--source", required=True, type=Path, help="CSV file, PDF file, or directory of .txt files")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Qdrant collection name")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size for upserts")
    parser.add_argument("--chunk-tokens", type=int, default=DEFAULT_CHUNK_TOKENS, help="Chunk size in tokens")
    parser.add_argument("--overlap-tokens", type=int, default=DEFAULT_OVERLAP_TOKENS, help="Overlap between chunks in tokens")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Embedding model name")
    parser.add_argument("--no-skip-existing", action="store_true", help="Re-ingest all documents (skip dedup)")
    parser.add_argument("--qdrant-url", default=os.getenv("QDRANT_URL", "http://localhost:6333"), help="Qdrant server URL")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: Source not found: {args.source}")
        sys.exit(1)

    logger.info(f"Loading embedder: {args.model}")
    embedder = _load_embedder(args.model)

    logger.info(f"Connecting to Qdrant: {args.qdrant_url}")
    qdrant = QdrantClient(url=args.qdrant_url)

    start = time.time()
    result = _ingest_stream(
        source_path=args.source,
        collection=args.collection,
        qdrant=qdrant,
        embedder=embedder,
        batch_size=args.batch_size,
        skip_existing=not args.no_skip_existing,
        progress=not args.no_progress,
    )
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print("  INGESTION REPORT")
    print(f"{'='*60}")
    print(f"  Source:       {args.source}")
    print(f"  Collection:   {args.collection}")
    print(f"  Ingested:     {result['ingested']} documents")
    print(f"  Skipped:      {result['skipped']} (duplicate)")
    print(f"  Failed:       {result['failed']}")
    print(f"  Total:        {result['total']}")
    print(f"  Time:         {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
