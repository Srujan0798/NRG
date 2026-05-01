"""Query and streaming answer endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, model_validator

from src.auth.middleware import get_current_user

router = APIRouter(tags=["query"])

_query_stream_response: Callable[[Any, dict, Request | None], Awaitable[Any]] | None = None
_query_handler: Callable[[Any, dict, Request | None], Awaitable[Any]] | None = None


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_question_alias(cls, data):
        """Accept legacy clients that submit {'question': ...} instead of {'query': ...}."""
        if isinstance(data, dict) and "query" not in data and "question" in data:
            return {**data, "query": data["question"]}
        return data


def configure_query_router(
    *,
    query_stream_response: Callable[[Any, dict, Request | None], Awaitable[Any]],
    query_handler: Callable[[Any, dict, Request | None], Awaitable[Any]],
) -> None:
    """Bind query routes to the app-level answer engine implementation."""
    global _query_stream_response, _query_handler
    _query_stream_response = query_stream_response
    _query_handler = query_handler


async def _stream_response(request: QueryRequest, token_payload: dict, raw_request: Request | None):
    if _query_stream_response is None:
        raise RuntimeError("Query router is not configured with a stream handler")
    return await _query_stream_response(request, token_payload, raw_request)


async def _handle_query(request: QueryRequest, token_payload: dict, raw_request: Request | None):
    if _query_handler is None:
        raise RuntimeError("Query router is not configured with a query handler")
    return await _query_handler(request, token_payload, raw_request)


@router.get("/api/query/stream")
async def query_stream_get(
    query: str = Query(..., min_length=1),
    session_id: Optional[str] = None,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    request = QueryRequest(query=query, session_id=session_id)
    return await _stream_response(request, token_payload, raw_request)


@router.post("/api/query/stream")
async def query_stream(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    return await _stream_response(request, token_payload, raw_request)


@router.post("/query")
async def query_with_langgraph(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    return await _handle_query(request, token_payload, raw_request)
