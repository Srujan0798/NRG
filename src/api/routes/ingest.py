"""Document ingestion endpoints and async ingestion job store."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

router = APIRouter(prefix="/api", tags=["ingest"])

_ingestion_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ingest_worker")
_ingestion_jobs: dict[str, dict] = {}
_ingestion_lock = threading.Lock()


@dataclass
class IngestionJob:
    job_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    source_filename: str = ""
    collection: str = ""
    result: dict = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    total: int = 0
    ingested: int = 0
    skipped: int = 0
    failed: int = 0


def _create_job(source_filename: str, collection: str) -> str:
    job_id = str(uuid.uuid4())[:8]
    with _ingestion_lock:
        _ingestion_jobs[job_id] = IngestionJob(
            job_id=job_id,
            source_filename=source_filename,
            collection=collection or os.getenv("QDRANT_COLLECTION", "nrg_research"),
            started_at=datetime.now(UTC).isoformat(),
        ).__dict__
    return job_id


def _update_job(job_id: str, **kwargs) -> None:
    with _ingestion_lock:
        if job_id in _ingestion_jobs:
            _ingestion_jobs[job_id].update(kwargs)


def _run_ingestion(job_id: str, file_path: Path, collection: str) -> None:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        from scripts.ingest_documents import (
            DEFAULT_BATCH_SIZE,
            DEFAULT_CHUNK_TOKENS,
            DEFAULT_OVERLAP_TOKENS,
            _detect_source_type,
            _embed_chunks,
            _ensure_collection,
            _get_existing_hashes,
            _load_embedder,
            _parse_csv,
            _parse_pdf,
            _parse_txt,
            _parse_txt_directory,
            _sha256,
        )

        _update_job(job_id, status="running")

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant = QdrantClient(url=qdrant_url)
        source_type = _detect_source_type(file_path)

        if source_type == "csv":
            doc_iter = _parse_csv(file_path)
        elif source_type == "txt_directory":
            doc_iter = _parse_txt_directory(file_path)
        elif source_type == "pdf":
            doc_iter = _parse_pdf(file_path)
        elif source_type == "txt":
            doc_iter = _parse_txt(file_path)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        embedder = _load_embedder()
        _ensure_collection(qdrant, collection)
        existing_hashes = _get_existing_hashes(qdrant, collection)

        batch: list[PointStruct] = []
        ingested = skipped = failed = total_docs = 0

        for doc in doc_iter:
            total_docs += 1
            doc_hash = _sha256(doc.content)
            if doc_hash in existing_hashes:
                skipped += 1
                continue

            chunks = []
            start = 0
            chunk_chars = DEFAULT_CHUNK_TOKENS * 4
            overlap_chars = DEFAULT_OVERLAP_TOKENS * 4
            while start < len(doc.content):
                end = start + chunk_chars
                chunk_text = doc.content[start:end].strip()
                if chunk_text:
                    chunks.append(chunk_text)
                start += chunk_chars - overlap_chars

            try:
                chunk_embeddings = _embed_chunks(embedder, chunks)
            except Exception:
                failed += 1
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
                    "job_id": job_id,
                    **{k: v for k, v in doc.metadata.items()},
                }
                batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))

            ingested += 1

            if len(batch) >= DEFAULT_BATCH_SIZE:
                try:
                    qdrant.upsert(collection_name=collection, points=batch)
                except Exception:
                    failed += len(batch)
                batch.clear()

        if batch:
            try:
                qdrant.upsert(collection_name=collection, points=batch)
            except Exception:
                failed += len(batch)

        result = {"ingested": ingested, "skipped": skipped, "failed": failed, "total": total_docs}
        _update_job(
            job_id,
            status="completed",
            result=result,
            completed_at=datetime.now(UTC).isoformat(),
            ingested=ingested,
            skipped=skipped,
            failed=failed,
            total=total_docs,
        )

    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc), completed_at=datetime.now(UTC).isoformat())
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/ingest")
async def ingest_documents(
    request: Request,
    file: UploadFile = File(...),
    collection: Optional[str] = None,
):
    """Trigger async document ingestion into the vector store."""
    claims = getattr(request.state, "auth_claims", None) or {}
    tier = 0
    try:
        from src.auth.middleware import get_user_tier

        tier = get_user_tier(claims)
    except Exception:
        pass

    if tier not in (1,):
        raise HTTPException(status_code=403, detail="Tier 1 (Researcher) access required for ingestion")

    allowed_types = {"text/csv", "application/pdf", "text/plain"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported: csv, pdf, txt",
        )

    if file.size and file.size > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 200MB")

    suffix = ".csv" if file.content_type == "text/csv" else f".{file.content_type.split('/')[1]}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        tmp.write(content)

    collection_name = collection or os.getenv("QDRANT_COLLECTION", "nrg_research")
    job_id = _create_job(source_filename=file.filename or "unknown", collection=collection_name)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_ingestion_executor, _run_ingestion, job_id, tmp_path, collection_name)

    return {"job_id": job_id, "status": "pending", "message": "Ingestion job started"}


@router.get("/ingest/{job_id}")
async def get_ingest_status(job_id: str):
    """Return status of an ingestion job."""
    with _ingestion_lock:
        job = _ingestion_jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "source_filename": job["source_filename"],
        "collection": job["collection"],
        "started_at": job["started_at"],
        "completed_at": job.get("completed_at", ""),
        "result": job.get("result", {}),
        "error": job.get("error", ""),
        "ingested": job.get("ingested", 0),
        "skipped": job.get("skipped", 0),
        "failed": job.get("failed", 0),
        "total": job.get("total", 0),
    }
