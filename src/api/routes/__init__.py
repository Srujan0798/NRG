"""NRG API routes package."""

from .auth import router as auth_router
from .query import router as query_router
from .data import router as data_router
from .graph import router as graph_router
from .health import router as health_router
from .admin import router as admin_router
from .ingest import router as ingest_router
from .audit import router as audit_router

__all__ = [
    "auth_router",
    "query_router",
    "data_router",
    "graph_router",
    "health_router",
    "admin_router",
    "ingest_router",
    "audit_router",
]
