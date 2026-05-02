"""Query and streaming answer endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, model_validator

from src.auth.middleware import get_current_user

router = APIRouter(tags=["query"])

TokenPayload = dict[str, Any]
QueryRouteHandler = Callable[[Any, TokenPayload, Request | None], Awaitable[Any]]

_query_stream_response: QueryRouteHandler | None = None
_query_handler: QueryRouteHandler | None = None


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_question_alias(cls, data: Any) -> Any:
        """Accept legacy clients that submit {'question': ...} instead of {'query': ...}."""
        if isinstance(data, dict) and "query" not in data and "question" in data:
            data_dict = cast(dict[str, Any], data)
            return {**data_dict, "query": data_dict["question"]}
        return cast(Any, data)


def configure_query_router(
    *,
    query_stream_response: QueryRouteHandler,
    query_handler: QueryRouteHandler,
) -> None:
    """Bind query routes to the app-level answer engine implementation."""
    global _query_stream_response, _query_handler
    _query_stream_response = query_stream_response
    _query_handler = query_handler


async def _stream_response(request: QueryRequest, token_payload: TokenPayload, raw_request: Request | None) -> Any:
    if _query_stream_response is None:
        raise RuntimeError("Query router is not configured with a stream handler")
    return await _query_stream_response(request, token_payload, raw_request)


async def _handle_query(request: QueryRequest, token_payload: TokenPayload, raw_request: Request | None) -> Any:
    if _query_handler is None:
        raise RuntimeError("Query router is not configured with a query handler")
    return await _query_handler(request, token_payload, raw_request)


@router.get("/api/query/stream")
async def query_stream_get(
    raw_request: Request,
    query: str = Query(..., min_length=1),
    session_id: Optional[str] = None,
    token_payload: TokenPayload = Depends(get_current_user),
) -> Any:
    request = QueryRequest(query=query, session_id=session_id)
    return await _stream_response(request, token_payload, raw_request)


@router.post("/api/query/stream")
async def query_stream(
    request: QueryRequest,
    raw_request: Request,
    token_payload: TokenPayload = Depends(get_current_user),
) -> Any:
    return await _stream_response(request, token_payload, raw_request)


@router.post("/query")
async def query_with_langgraph(
    request: QueryRequest,
    raw_request: Request,
    token_payload: TokenPayload = Depends(get_current_user),
) -> Any:
    return await _handle_query(request, token_payload, raw_request)
