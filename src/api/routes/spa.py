"""Frontend SPA shell fallback route."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["spa"])


@router.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("dist/frontend/index.html")
