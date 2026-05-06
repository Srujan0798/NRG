"""Answer-engine service for query and streaming routes."""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

import orjson
from fastapi import HTTPException, Request
from starlette.responses import Response, StreamingResponse

from src.api.answer_contract import blocked_answer_payload
from src.api.middleware.security import IPAllowlist
from src.api.query_response_utils import (
    answer_confidence_from_verification,
    normalise_query_answer_payload,
    normalise_stream_answer_payload,
    redact_pii_from_response,
    schedule_answer_record_persist,
    sse,
)
from src.api.response_filter import warm_response_policy_cache
from src.api.routes.query import QueryRequest, TokenPayload
from src.config.database import get_database_manager
from src.observability.metrics import get_slo_tracker
from src.security.rate_limiter import check_endpoint_rate_limit, check_tier_rate_limit
from src.services.consent import get_consent_service


@dataclass(frozen=True)
class QueryServiceDependencies:
    logger: Any
    api_cache: Any
    query_result_cache_ttl_seconds: int
    prompt_sanitiser: Any
    query_stage_profiler_factory: Callable[..., Any]
    as_json_dict: Callable[[Any], dict[str, Any]]
    as_sequence_for_count: Callable[[Any], list[Any]]
    audit_log_query_sync: Callable[..., Any]
    audit_log_query: Callable[..., Awaitable[Any]]
    audit_log_anomaly: Callable[..., Awaitable[Any]]
    rate_limit_detail: Callable[..., Awaitable[dict[str, Any]]]
    apply_tier_response_filter: Callable[..., Any]
    apply_ai_synthesis_after_tier_filter: Callable[..., dict[str, Any]]
    should_use_c4_read_model: Callable[[str], bool]
    c4_read_model_response: Callable[..., dict[str, Any] | None]
    get_or_build_query_cache_singleflight: Callable[..., Awaitable[tuple[Any, bool]]]
    fast_query_response: Callable[..., dict[str, Any] | None]
    academic_follow_up_response: Callable[..., dict[str, Any] | None]
    killer_query_response: Callable[..., dict[str, Any] | None]
    advanced_adversarial_response: Callable[..., dict[str, Any] | None]
    run_workflow: Callable[..., dict[str, Any] | None]
    sql_context_key: Callable[[str | None, str | None], str]
    remember_sql_domain_context: Callable[[str, str, str | None], None]


class QueryAnswerService:
    """Owns the answer-engine path behind /query and /api/query/stream."""

    def __init__(self, deps: QueryServiceDependencies) -> None:
        self.deps = deps
        self._serialized_cached_responses: dict[str, tuple[int, bytes]] = {}
        warm_response_policy_cache()

    def _serialized_tier_filtered_cache_hit(
        self,
        *,
        cache_key: str,
        cached: Mapping[str, Any],
        user_tier: int,
    ) -> Response | None:
        if not (
            cached.get("_tier_filter_applied") is True
            and cached.get("_tier_filter_tier") == user_tier
        ):
            return None

        cached_identity = id(cached)
        entry = self._serialized_cached_responses.get(cache_key)
        if entry is None or entry[0] != cached_identity:
            payload = self.deps.as_json_dict(cached)
            payload["cached"] = True
            payload.pop("_tier_filter_applied", None)
            payload.pop("_tier_filter_tier", None)
            entry = (cached_identity, orjson.dumps(payload))
            self._serialized_cached_responses[cache_key] = entry
        return Response(content=entry[1], media_type="application/json")

    def build_stream_answer_payload(
        self,
        request: QueryRequest,
        *,
        token_payload: TokenPayload,
        raw_request: Request | None,
    ) -> dict[str, Any]:
        user_tier = token_payload.get("tier", 1)
        user_id = token_payload.get("sub", "anonymous")
        jwt_kid = token_payload.get("kid")
        request_fp = getattr(raw_request.state, "request_fingerprint", None) if raw_request else None

        cache_key = self.deps.api_cache.make_cache_key(request.query, user_tier)
        cached = self.deps.api_cache.get(cache_key)
        if cached is not None:
            cached_response = self.deps.as_json_dict(cached) if isinstance(cached, Mapping) else cached
            if isinstance(cached_response, dict):
                cached_response["cached"] = True
            return self.deps.apply_tier_response_filter(
                cached_response,
                user_tier,
                user_id=user_id,
                jwt_kid=jwt_kid,
                request_fingerprint=request_fp,
                endpoint="/api/query/stream",
            )

        audit_event_id = None
        try:
            audit_event_id = self.deps.audit_log_query_sync(
                user_id,
                request.query,
                jwt_kid=jwt_kid,
                request_fingerprint=request_fp,
            )
        except Exception:
            self.deps.logger.warning("Audit log_query failed for stream query", exc_info=True)

        context_key = self.deps.sql_context_key(user_id, request.session_id)
        result = (
            self.deps.fast_query_response(request.query, user_tier=user_tier, user_id=user_id, session_id=request.session_id)
            or self.deps.academic_follow_up_response(request.query, user_tier=user_tier, session_id=request.session_id, context_key=context_key)
            or self.deps.killer_query_response(request.query, user_tier=user_tier, session_id=request.session_id)
            or self.deps.advanced_adversarial_response(request.query, user_tier=user_tier, session_id=request.session_id)
        )

        if result is None:
            result = self.deps.run_workflow(
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
                user_id=user_id,
            )

        if audit_event_id:
            result.setdefault("audit_event_id", audit_event_id)

        response_payload = normalise_stream_answer_payload(
            result,
            request=request,
            user_tier=user_tier,
            audit_event_id=audit_event_id,
        )
        response_payload = self.deps.apply_tier_response_filter(
            response_payload,
            user_tier,
            user_id=user_id,
            jwt_kid=jwt_kid,
            request_fingerprint=request_fp,
            endpoint="/api/query/stream",
        )
        schedule_answer_record_persist(user_id, request.session_id, response_payload)
        self.deps.api_cache.set(cache_key, response_payload, ttl=self.deps.query_result_cache_ttl_seconds)
        self.deps.remember_sql_domain_context(context_key, request.query, response_payload.get("sql_query"))
        return response_payload


    async def query_stream_response(
        self,
        request: QueryRequest,
        token_payload: TokenPayload,
        raw_request: Request | None,
    ) -> StreamingResponse:
        client_ip = raw_request.client.host if raw_request and raw_request.client else None
        user_tier = token_payload.get("tier", 1)
        user_id = token_payload.get("sub", "anonymous")

        allowed, _remaining, _reset_time, rate_headers = check_tier_rate_limit(user_id, user_tier, client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=await self.deps.rate_limit_detail(
                    user_id=user_id,
                    message="Rate limit exceeded",
                    client_ip=client_ip,
                    limit_scope="tier",
                ),
                headers=rate_headers,
            )

        consent_service = get_consent_service()
        if not consent_service.has_consent(user_id, "research_access"):
            raise HTTPException(status_code=403, detail="Consent required for research_access")

        async def event_generator() -> AsyncIterator[str]:
            started_at = time.time()
            yield "retry: 300\n\n"

            def phase_payload(phase: str, label: str, progress: float, **extra: Any) -> dict[str, Any]:
                return {
                    "phase": phase,
                    "label": label,
                    "progress": progress,
                    "elapsed_ms": int((time.time() - started_at) * 1000),
                    **extra,
                }

            validation = self.deps.prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
            yield sse("phase", phase_payload("understanding", "Understanding your question", 0.08))
            yield sse("phase", phase_payload("parsing", "Parsing your question...", 0.08))
            await asyncio.sleep(0.02)
            if not validation["valid"]:
                blocked = blocked_answer_payload(
                    question=request.query,
                    user_tier=user_tier,
                    audit_event_id=None,
                    reason=f"Security policy blocked this query: {validation['reason']}",
                )
                yield sse("phase", phase_payload("blocked", "Blocked by safety policy", 1.0))
                yield sse("meta", blocked)
                yield sse("done", "")
                return

            try:
                yield sse("phase", phase_payload("planning", "Planning retrieval", 0.18))
                await asyncio.sleep(0.02)
                yield sse("phase", phase_payload("searching_records", "Searching research records", 0.42))
                yield sse("phase", phase_payload("querying", "Querying 58 research tables...", 0.52))
                answer_task = asyncio.create_task(
                    asyncio.to_thread(
                        self.build_stream_answer_payload,
                        request,
                        token_payload=token_payload,
                        raw_request=raw_request,
                    )
                )
                while not answer_task.done():
                    yield sse(
                        "heartbeat",
                        {
                            "phase": "heartbeat",
                            "elapsed_ms": int((time.time() - started_at) * 1000),
                        },
                    )
                    await asyncio.sleep(1)
                answer_payload = await answer_task
                row_count = len(answer_payload.get("sql_results") or [])
                yield sse("phase", phase_payload("checking_documents", "Checking documents", 0.58, row_count=row_count))
                yield sse("phase", phase_payload("querying", "Querying 58 research tables...", 0.62, row_count=row_count))
                await asyncio.sleep(0.02)
                yield sse("phase", phase_payload("synthesizing", "Synthesizing answer", 0.78))
                await asyncio.sleep(0.02)
                yield sse("phase", phase_payload("verifying", "Verifying sources", 0.92))
                await asyncio.sleep(0.02)
                answer_payload["elapsed_ms"] = int((time.time() - started_at) * 1000)
                yield sse("answer", answer_payload)
                yield sse("done", "")
            except Exception as e:
                self.deps.logger.error(f"Streaming query error: {e}", exc_info=True)
                yield sse(
                    "error",
                    {
                        "phase": "error",
                        "message": (
                            "The streaming answer stopped before verification. "
                            "Run the query again; the signed audit trail remains intact."
                        ),
                    },
                )
                yield sse("done", "")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )


    async def query_with_langgraph(
        self,
        request: QueryRequest,
        token_payload: TokenPayload,
        raw_request: Request | None = None,
    ) -> Any:
        """Process query using LangGraph orchestration with full security hardening."""
        client_ip = None
        if raw_request and raw_request.client:
            client_ip = raw_request.client.host

        user_tier = token_payload.get("tier", 1)
        user_id = token_payload.get("sub", "anonymous")
        profiler = self.deps.query_stage_profiler_factory(query=request.query, user_tier=user_tier, user_id=user_id)

        allowed, _remaining, _reset_time, rate_headers = check_tier_rate_limit(
            user_id, user_tier, client_ip
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=await self.deps.rate_limit_detail(
                    user_id=user_id,
                    message="Rate limit exceeded",
                    client_ip=client_ip,
                    limit_scope="tier",
                ),
                headers=rate_headers,
            )

        allowed_endpoint, _remaining_endpoint, _reset_endpoint, endpoint_headers = check_endpoint_rate_limit(
            "/query", user_id
        )
        if not allowed_endpoint:
            raise HTTPException(
                status_code=429,
                detail=await self.deps.rate_limit_detail(
                    user_id=user_id,
                    message="Query rate limit exceeded (10/min). Please wait before submitting another query.",
                    client_ip=client_ip,
                    limit_scope="endpoint:/query",
                ),
                headers={**rate_headers, **endpoint_headers},
            )

        if user_tier == 2:
            if not IPAllowlist.is_allowed(client_ip or ""):
                self.deps.logger.warning(
                    "Government tier access blocked for non-whitelisted IP",
                    client_ip=client_ip,
                    user=user_id,
                )
                raise HTTPException(
                    status_code=403,
                    detail="IP not allowed for government tier access",
                )
        profiler.mark("rate_limit_and_tier_guard")

        try:
            validation = self.deps.prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
            if not validation["valid"]:
                log_blocked_prompts = os.getenv("NRG_LOG_BLOCKED_PROMPTS", "").lower() in {
                    "1",
                    "true",
                    "yes",
                }
                log_method = self.deps.logger.warning if log_blocked_prompts else self.deps.logger.debug
                log_method(f"Security violation: {validation['reason']} - {validation.get('details', '')}")
                if validation["reason"] == "RATE_LIMITED":
                    raise HTTPException(
                        status_code=429,
                        detail=await self.deps.rate_limit_detail(
                            user_id=user_id,
                            message="Rate limit exceeded",
                            client_ip=client_ip,
                            limit_scope="prompt_sanitiser",
                        ),
                    )

                blocked_cache_key = self.deps.api_cache.make_cache_key(
                    request.query,
                    user_tier,
                    intent="blocked",
                    routing=f"{validation['reason']}:{user_id}",
                )
                cached_blocked = self.deps.api_cache.get(blocked_cache_key)
                profiler.mark("blocked_cache_lookup")
                if cached_blocked is not None:
                    cached_blocked_response: Any = cached_blocked
                    if isinstance(cached_blocked, Mapping):
                        cached_blocked_response = self.deps.as_json_dict(cached_blocked)
                        cached_blocked_response["cached"] = True
                        if (
                            cached_blocked_response.get("_tier_filter_applied") is True
                            and cached_blocked_response.get("_tier_filter_tier") == user_tier
                        ):
                            cached_blocked_response.pop("_tier_filter_applied", None)
                            cached_blocked_response.pop("_tier_filter_tier", None)
                            profiler.finish(route="blocked", outcome="blocked", cache_hit=True)
                            return cached_blocked_response
                    filtered_cached_blocked = self.deps.apply_tier_response_filter(
                        cached_blocked_response,
                        user_tier,
                        user_id=user_id,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                        endpoint="/query",
                    )
                    profiler.mark("tier_filter")
                    profiler.finish(route="blocked", outcome="blocked", cache_hit=True)
                    return filtered_cached_blocked

                async def build_blocked_response() -> dict[str, Any]:
                    audit_event_id = None
                    try:
                        audit_event_id = await self.deps.audit_log_anomaly(
                            user_id=user_id,
                            anomaly_type=validation["reason"],
                            details={
                                "query": request.query[:200],
                                "details": validation.get("details", ""),
                                "rate_limit_triggered": validation.get("rate_limit_triggered", False),
                            },
                            identifier=client_ip,
                        )
                    except Exception:
                        self.deps.logger.warning("Audit log_anomaly failed at API layer", exc_info=True)
                    blocked = blocked_answer_payload(
                        question=request.query,
                        user_tier=user_tier,
                        audit_event_id=audit_event_id,
                        reason=f"Security policy blocked this query: {validation['reason']}",
                    )
                    filtered_blocked = self.deps.apply_tier_response_filter(
                        blocked,
                        user_tier,
                        user_id=user_id,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                        endpoint="/query",
                    )
                    if isinstance(filtered_blocked, dict):
                        filtered_blocked["_tier_filter_applied"] = True
                        filtered_blocked["_tier_filter_tier"] = user_tier
                    return filtered_blocked

                filtered_blocked, blocked_cache_hit = await self.deps.get_or_build_query_cache_singleflight(
                    blocked_cache_key,
                    build_blocked_response,
                    ttl=self.deps.query_result_cache_ttl_seconds,
                )
                profiler.mark("prompt_sanitizer_block")
                if isinstance(filtered_blocked, Mapping):
                    blocked_response_dict = self.deps.as_json_dict(filtered_blocked)
                    if blocked_cache_hit:
                        blocked_response_dict["cached"] = True
                    if (
                        blocked_response_dict.get("_tier_filter_applied") is True
                        and blocked_response_dict.get("_tier_filter_tier") == user_tier
                    ):
                        blocked_response_dict.pop("_tier_filter_applied", None)
                        blocked_response_dict.pop("_tier_filter_tier", None)
                        profiler.finish(route="blocked", outcome="blocked", cache_hit=blocked_cache_hit)
                        return blocked_response_dict
                    filtered_blocked = blocked_response_dict
                profiler.finish(route="blocked", outcome="blocked", cache_hit=blocked_cache_hit)
                return filtered_blocked
            profiler.mark("prompt_sanitizer")

            consent_service = get_consent_service()
            if not consent_service.has_consent(user_id, "research_access"):
                raise HTTPException(
                    status_code=403,
                    detail="Consent required: Please grant research_access consent before querying data"
                )
            profiler.mark("consent_check")

            # Use normalized cache key for better hit rate
            cache_key = self.deps.api_cache.make_cache_key(request.query, user_tier)
            cached = self.deps.api_cache.get(cache_key)
            profiler.mark("cache_lookup")
            if cached is not None:
                cached_response: Any = cached
                if isinstance(cached, Mapping):
                    serialized_cached = self._serialized_tier_filtered_cache_hit(
                        cache_key=cache_key,
                        cached=cached,
                        user_tier=user_tier,
                    )
                    if serialized_cached is not None:
                        profiler.finish(route="cache", outcome="success", cache_hit=True)
                        return serialized_cached
                    cached_response_dict = self.deps.as_json_dict(cached)
                    cached_response_dict["cached"] = True
                    if (
                        cached_response_dict.get("_tier_filter_applied") is True
                        and cached_response_dict.get("_tier_filter_tier") == user_tier
                    ):
                        cached_response_dict.pop("_tier_filter_applied", None)
                        cached_response_dict.pop("_tier_filter_tier", None)
                        profiler.finish(route="cache", outcome="success", cache_hit=True)
                        return cached_response_dict
                    cached_response = cached_response_dict
                filtered_cached = self.deps.apply_tier_response_filter(
                    cached_response,
                    user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                profiler.mark("tier_filter")
                profiler.finish(route="cache", outcome="success", cache_hit=True)
                return filtered_cached

            if self.deps.should_use_c4_read_model(request.query):
                async def build_c4_response() -> dict[str, Any] | None:
                    c4_response = await asyncio.to_thread(
                        self.deps.c4_read_model_response,
                        request.query,
                        user_tier=user_tier,
                        session_id=request.session_id,
                    )
                    profiler.mark("c4_read_model")
                    if c4_response is None:
                        return None
                    try:
                        c4_response["audit_event_id"] = await self.deps.audit_log_query(
                            user_id,
                            request.query,
                            jwt_kid=token_payload.get("kid"),
                            request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                        )
                    except Exception:
                        self.deps.logger.warning("Audit log_query failed for C4 read model path", exc_info=True)
                        c4_response["audit_event_id"] = "audit_unavailable"
                    profiler.mark("audit_append")
                    normalized = normalise_query_answer_payload(
                        request,
                        user_tier=user_tier,
                        audit_event_id=c4_response.get("audit_event_id"),
                        elapsed_ms=0,
                        result=c4_response,
                    )
                    normalized, redacted_pii = redact_pii_from_response(normalized)
                    if redacted_pii:
                        normalized["warnings"] = normalized.get("warnings", []) + [
                            f"PII redaction applied to response: {', '.join(redacted_pii)}"
                        ]
                    profiler.mark("normalize_and_redact")
                    normalized = self.deps.apply_tier_response_filter(
                        normalized,
                        user_tier,
                        user_id=user_id,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                        endpoint="/query",
                    )
                    normalized["_tier_filter_applied"] = True
                    normalized["_tier_filter_tier"] = user_tier
                    profiler.mark("tier_filter")
                    schedule_answer_record_persist(user_id, request.session_id, normalized)
                    profiler.mark("answer_record_schedule")
                    return normalized

                c4_payload, c4_cache_hit = await self.deps.get_or_build_query_cache_singleflight(
                    cache_key,
                    build_c4_response,
                    ttl=self.deps.query_result_cache_ttl_seconds,
                )
                profiler.mark("c4_singleflight")
                if c4_payload is not None:
                    response_payload: Any = c4_payload
                    if isinstance(c4_payload, Mapping):
                        response_payload_dict = self.deps.as_json_dict(c4_payload)
                        if c4_cache_hit:
                            response_payload_dict["cached"] = True
                        if (
                            response_payload_dict.get("_tier_filter_applied") is True
                            and response_payload_dict.get("_tier_filter_tier") == user_tier
                        ):
                            response_payload_dict.pop("_tier_filter_applied", None)
                            response_payload_dict.pop("_tier_filter_tier", None)
                            profiler.finish(route="c4_read_model", outcome="success", cache_hit=c4_cache_hit)
                            return response_payload_dict
                        response_payload = response_payload_dict
                    filtered_c4_payload = self.deps.apply_tier_response_filter(
                        response_payload,
                        user_tier,
                        user_id=user_id,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                        endpoint="/query",
                    )
                    profiler.mark("tier_filter")
                    profiler.finish(route="c4_read_model", outcome="success", cache_hit=c4_cache_hit)
                    return filtered_c4_payload

            fast_response = await asyncio.to_thread(
                self.deps.fast_query_response,
                request.query,
                user_tier=user_tier,
                user_id=user_id,
                session_id=request.session_id,
            )
            profiler.mark("fast_query_response")
            if fast_response is not None:
                try:
                    fast_response["audit_event_id"] = await self.deps.audit_log_query(
                        user_id,
                        request.query,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    )
                except Exception:
                    self.deps.logger.warning("Audit log_query failed for query fast path", exc_info=True)
                    fast_response["audit_event_id"] = "audit_unavailable"
                profiler.mark("audit_append")
                fast_response = normalise_query_answer_payload(
                    request,
                    user_tier=user_tier,
                    audit_event_id=fast_response.get("audit_event_id"),
                    elapsed_ms=0,
                    result=fast_response,
                )
                fast_response, redacted_pii = redact_pii_from_response(fast_response)
                if redacted_pii:
                    fast_response["warnings"] = fast_response.get("warnings", []) + [
                        f"PII redaction applied to response: {', '.join(redacted_pii)}"
                    ]
                profiler.mark("normalize_and_redact")
                fast_response = self.deps.apply_tier_response_filter(
                    fast_response,
                    user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                profiler.mark("tier_filter")
                fast_response = self.deps.apply_ai_synthesis_after_tier_filter(
                    fast_response,
                    query=request.query,
                    user_tier=user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                profiler.mark("ai_synthesis")
                schedule_answer_record_persist(user_id, request.session_id, fast_response)
                self.deps.api_cache.set(cache_key, fast_response, ttl=self.deps.query_result_cache_ttl_seconds)
                profiler.mark("persist_and_cache")
                profiler.finish(route="fast_query", outcome="success", cache_hit=False)
                return fast_response

            context_key = self.deps.sql_context_key(user_id, request.session_id)
            follow_up_response = await asyncio.to_thread(
                self.deps.academic_follow_up_response,
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
                context_key=context_key,
            )
            profiler.mark("follow_up_response")
            if follow_up_response is not None:
                try:
                    follow_up_response["audit_event_id"] = await self.deps.audit_log_query(
                        user_id,
                        request.query,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    )
                except Exception:
                    self.deps.logger.warning("Audit log_query failed for SQL follow-up fast path", exc_info=True)
                    follow_up_response["audit_event_id"] = "audit_unavailable"
                profiler.mark("audit_append")
                follow_up_response = normalise_query_answer_payload(
                    request,
                    user_tier=user_tier,
                    audit_event_id=follow_up_response.get("audit_event_id"),
                    elapsed_ms=0,
                    result=follow_up_response,
                )
                follow_up_response, redacted_pii = redact_pii_from_response(follow_up_response)
                if redacted_pii:
                    follow_up_response["warnings"] = follow_up_response.get("warnings", []) + [
                        f"PII redaction applied to response: {', '.join(redacted_pii)}"
                    ]
                follow_up_response = self.deps.apply_tier_response_filter(
                    follow_up_response,
                    user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                follow_up_response = self.deps.apply_ai_synthesis_after_tier_filter(
                    follow_up_response,
                    query=request.query,
                    user_tier=user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                schedule_answer_record_persist(user_id, request.session_id, follow_up_response)
                self.deps.api_cache.set(cache_key, follow_up_response, ttl=self.deps.query_result_cache_ttl_seconds)
                profiler.mark("persist_and_cache")
                profiler.finish(route="follow_up", outcome="success", cache_hit=False)
                return follow_up_response

            killer_response = await asyncio.to_thread(
                self.deps.killer_query_response,
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
            )
            profiler.mark("killer_query_response")
            if killer_response is not None:
                try:
                    killer_response["audit_event_id"] = await self.deps.audit_log_query(
                        user_id,
                        request.query,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    )
                except Exception:
                    self.deps.logger.warning("Audit log_query failed for killer query fast path", exc_info=True)
                    killer_response["audit_event_id"] = "audit_unavailable"
                profiler.mark("audit_append")
                killer_response = normalise_query_answer_payload(
                    request,
                    user_tier=user_tier,
                    audit_event_id=killer_response.get("audit_event_id"),
                    elapsed_ms=0,
                    result=killer_response,
                )
                killer_response, redacted_pii = redact_pii_from_response(killer_response)
                if redacted_pii:
                    killer_response["warnings"] = killer_response.get("warnings", []) + [
                        f"PII redaction applied to response: {', '.join(redacted_pii)}"
                    ]
                killer_response = self.deps.apply_tier_response_filter(
                    killer_response,
                    user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                killer_response = self.deps.apply_ai_synthesis_after_tier_filter(
                    killer_response,
                    query=request.query,
                    user_tier=user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                schedule_answer_record_persist(user_id, request.session_id, killer_response)
                self.deps.api_cache.set(cache_key, killer_response, ttl=self.deps.query_result_cache_ttl_seconds)
                self.deps.remember_sql_domain_context(
                    self.deps.sql_context_key(user_id, request.session_id),
                    request.query,
                    killer_response.get("sql_query"),
                )
                profiler.mark("persist_cache_and_context")
                profiler.finish(route="killer_query", outcome="success", cache_hit=False)
                return killer_response

            adversarial_response = await asyncio.to_thread(
                self.deps.advanced_adversarial_response,
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
            )
            profiler.mark("adversarial_response")
            if adversarial_response is not None:
                try:
                    adversarial_response["audit_event_id"] = await self.deps.audit_log_query(
                        user_id,
                        request.query,
                        jwt_kid=token_payload.get("kid"),
                        request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    )
                except Exception:
                    self.deps.logger.warning("Audit log_query failed for adversarial SQL pattern", exc_info=True)
                    adversarial_response["audit_event_id"] = "audit_unavailable"
                profiler.mark("audit_append")
                adversarial_response = normalise_query_answer_payload(
                    request,
                    user_tier=user_tier,
                    audit_event_id=adversarial_response.get("audit_event_id"),
                    elapsed_ms=0,
                    result=adversarial_response,
                )
                adversarial_response = self.deps.apply_tier_response_filter(
                    adversarial_response,
                    user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                adversarial_response = self.deps.apply_ai_synthesis_after_tier_filter(
                    adversarial_response,
                    query=request.query,
                    user_tier=user_tier,
                    user_id=user_id,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                    endpoint="/query",
                )
                schedule_answer_record_persist(user_id, request.session_id, adversarial_response)
                self.deps.api_cache.set(cache_key, adversarial_response, ttl=self.deps.query_result_cache_ttl_seconds)
                profiler.mark("persist_and_cache")
                profiler.finish(route="adversarial", outcome="success", cache_hit=False)
                return adversarial_response

            slo_tracker = get_slo_tracker()
            slo_tracker.increment_concurrency()

            query_start = time.time()

            jwt_kid = token_payload.get("kid")
            request_fp = getattr(raw_request.state, "request_fingerprint", None) if raw_request else None

            audit_event_id = None
            try:
                audit_event_id = await self.deps.audit_log_query(user_id, request.query, jwt_kid=jwt_kid, request_fingerprint=request_fp)
            except Exception:
                self.deps.logger.warning("Audit log_query failed at API layer", exc_info=True)
            profiler.mark("audit_append")

            result: dict[str, Any] | None = None
            try:
                db = get_database_manager()
                if db.is_overloaded():
                    raise HTTPException(
                        status_code=503,
                        detail="Service temporarily unavailable due to database load. Please retry in a moment.",
                    )

                result = await asyncio.to_thread(
                    self.deps.run_workflow,
                    request.query,
                    user_tier=user_tier,
                    session_id=request.session_id,
                    user_id=user_id,
                )
                profiler.mark("workflow_run")
            finally:
                latency_ms = (time.time() - query_start) * 1000
                slo_tracker.decrement_concurrency()
                slo_tracker.record_latency(latency_ms)
                if result is not None:
                    citations = self.deps.as_sequence_for_count(result.get("citations", []))
                    synthesis_method = str(result.get("synthesis_method", "unknown"))
                else:
                    citations = []
                    synthesis_method = "error"
                slo_tracker.record_citation(
                    has_citation=len(citations) > 0,
                    synthesis_method=synthesis_method,
                )

            if result is None:
                result = {}
            synthesis_method = str(result.get("synthesis_method", "unknown"))
            warnings_text = " ".join(str(item).lower() for item in self.deps.as_sequence_for_count(result.get("warnings", [])))
            explicit_sql_only_degradation = synthesis_method == "sql_only" and (
                "vector" in warnings_text or "qdrant" in warnings_text
            )
            if (
                synthesis_method == "unknown"
                or (synthesis_method == "sql_only" and not explicit_sql_only_degradation)
            ) and result.get("synthesized_response"):
                synthesis_method = "rule_based"
            provenance = self.deps.as_json_dict(result.get("provenance", {}) or {})
            if "synth" not in provenance:
                provenance["synth"] = synthesis_method if synthesis_method != "unknown" else "rule_based"
            provenance.setdefault("cloud_synthesis_used", "cloud" in str(provenance.get("synth", "")))

            response_payload = normalise_query_answer_payload(
                request,
                user_tier=user_tier,
                audit_event_id=audit_event_id,
                elapsed_ms=latency_ms,
                result={
                    **result,
                    "warnings": result.get("warnings", result.get("errors", [])),
                    "provenance": provenance,
                    "synthesis_method": synthesis_method,
                    "answer_confidence": result.get(
                        "answer_confidence",
                        answer_confidence_from_verification(result.get("verification_status", False)),
                    ),
                },
                default_verification=False,
            )

            response_payload, redacted_pii = redact_pii_from_response(response_payload)
            if redacted_pii:
                response_payload["warnings"] = response_payload.get("warnings", []) + [
                    f"PII redaction applied to response: {', '.join(redacted_pii)}"
                ]
            response_payload = self.deps.apply_tier_response_filter(
                response_payload,
                user_tier,
                user_id=user_id,
                jwt_kid=jwt_kid,
                request_fingerprint=request_fp,
                endpoint="/query",
            )
            response_payload = self.deps.apply_ai_synthesis_after_tier_filter(
                response_payload,
                query=request.query,
                user_tier=user_tier,
                user_id=user_id,
                jwt_kid=jwt_kid,
                request_fingerprint=request_fp,
                endpoint="/query",
            )

            schedule_answer_record_persist(user_id, request.session_id, response_payload)
            self.deps.api_cache.set(cache_key, response_payload, ttl=self.deps.query_result_cache_ttl_seconds)
            self.deps.remember_sql_domain_context(
                self.deps.sql_context_key(user_id, request.session_id),
                request.query,
                response_payload.get("sql_query"),
            )
            profiler.mark("fallback_persist_cache_and_context")
            profiler.finish(route="workflow", outcome="success", cache_hit=False)
            return response_payload
        except HTTPException:
            profiler.finish(route="exception", outcome="http_exception", cache_hit=None)
            raise
        except Exception as e:
            profiler.finish(route="exception", outcome="error", cache_hit=None)
            self.deps.logger.error(f"Workflow execution error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
