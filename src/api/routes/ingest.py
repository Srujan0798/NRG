"""Document ingestion endpoints."""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from src.api.logging_config import get_logger

router = APIRouter(prefix="/api", tags=["ingest"])
logger = get_logger(__name__)

_ingestion_lock = threading.Lock()
_ingestion_jobs: dict[str, dict[str, Any]] = {}


class IngestionJob:
    def __init__(
        self,
        job_id: str,
        source_filename: str,
        collection: str,
        started_at: str,
    ):
        self.job_id = job_id
        self.source_filename = source_filename
        self.collection = collection
        self.started_at = started_at
        self.status = "pending"
        self.completed_at = ""
        self.result = {}
        self.error = ""
        self.ingested = 0
        self.skipped = 0
        self.failed = 0
        self.total = 0

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


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
    import sys
    from pathlib import Path as P

    PROJECT_ROOT = P(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from qdrant_client import QdrantClient
        from scripts.ingest_documents import (
            _detect_source_type, _parse_csv, _parse_txt_directory, _parse_pdf, _parse_txt,
            _load_embedder, _ensure_collection, _embed_chunks, _sha256,
            _get_existing_hashes, DEFAULT_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS, DEFAULT_BATCH_SIZE,
        )
        from qdrant_client.models import PointStruct

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
            _update_job(job_id, status="failed", error=f"Unknown source type: {source_type}")
            return

        embedder = _load_embedder()
        collection_name, vector_size = _ensure_collection(qdrant, collection)

        existing_hashes = _get_existing_hashes(qdrant, collection_name)
        batch: list[PointStruct] = []
        ingested = skipped = failed = 0

        for doc_id, chunk_text, metadata in doc_iter:
            chunk_hash = _sha256(chunk_text)
            if chunk_hash in existing_hashes:
                skipped += 1
                continue

            try:
                vector = _embedder.embed([chunk_text])[0]
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "doc_id": doc_id,
                        "chunk_text": chunk_text,
                        "chunk_hash": chunk_hash,
                        **metadata,
                    },
                )
                batch.append(point)

                if len(batch) >= DEFAULT_BATCH_SIZE:
                    qdrant.upsert(collection_name=collection_name, points=batch)
                    existing_hashes.update(c.chunk_hash for c in batch)
                    batch.clear()

            except Exception as e:
                logger.warning(f"Chunk embedding failed: {e}")
                failed += 1

        if batch:
            qdrant.upsert(collection_name=collection_name, points=batch)

        _update_job(
            job_id,
            status="completed",
            completed_at=datetime.now(UTC).isoformat(),
            ingested=ingested,
            skipped=skipped,
            failed=failed,
            total=ingested + skipped + failed,
        )

    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {e}")
        _update_job(job_id, status="failed", error=str(e))


_ingestion_executor = None


def _get_ingestion_executor():
    global _ingestion_executor
    if _ingestion_executor is None:
        from concurrent.futures import ThreadPoolExecutor

        _ingestion_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ingestion_")
    return _ingestion_executor


@router.post("/ingest")
async def ingest_documents(
    request: Request,
    file: UploadFile = File(...),
    collection: str | None = None,
):
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
    loop.run_in_executor(
        _get_ingestion_executor(),
        _run_ingestion,
        job_id,
        tmp_path,
        collection_name,
    )

    return {"job_id": job_id, "status": "pending", "message": "Ingestion job started"}


@router.get("/ingest/{job_id}")
async def get_ingest_status(job_id: str):
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
