"""Query endpoints — /query, /api/query/stream."""

from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.deps import (
    QueryRequest,
    FeedbackRequest,
    _apply_tier_response_filter,
    _api_cache,
    _answer_confidence_from_verification,
    _redact_pii_from_response,
    _remember_sql_domain_context,
    _sql_context_key,
    check_endpoint_rate_limit,
    check_tier_rate_limit,
    get_workflow,
    get_db,
    QUERY_RESULT_CACHE_TTL_SECONDS,
)
from src.api.logging_config import get_logger
from src.api.middleware.security import IPAllowlist
from src.api.query_helpers import (
    _academic_follow_up_response,
    _advanced_adversarial_response,
    _fast_query_response,
    _killer_query_response,
)
from src.auth.middleware import get_current_user
from src.audit import log_query as audit_log_query
from src.observability.metrics import get_slo_tracker
from src.security.gateway.prompt_sanitiser import prompt_sanitiser
from src.services.consent import ConsentService

router = APIRouter(prefix="", tags=["query"])
logger = get_logger(__name__)


def _apply_tier_filter_to_response(payload, user_tier, user_id, jwt_kid, request_fp):
    payload, redacted_pii = _redact_pii_from_response(payload)
    if redacted_pii:
        payload["warnings"] = payload.get("warnings", []) + [
            f"PII redaction applied to response: {', '.join(redacted_pii)}"
        ]
    return _apply_tier_response_filter(
        payload,
        user_tier,
        user_id=user_id,
        jwt_kid=jwt_kid,
        request_fingerprint=request_fp,
        endpoint="/query",
    )


@router.post("/query")
async def query_with_langgraph(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    client_ip = raw_request.client.host if raw_request and raw_request.client else None
    user_tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(user_id, user_tier, client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    allowed_endpoint, remaining_endpoint, reset_endpoint, endpoint_headers = check_endpoint_rate_limit("/query", user_id)
    if not allowed_endpoint:
        raise HTTPException(
            status_code=429,
            detail="Query rate limit exceeded (10/min). Please wait before submitting another query.",
            headers={**rate_headers, **endpoint_headers},
        )

    if user_tier == 2:
        if not IPAllowlist.is_allowed(client_ip or ""):
            logger.warning(
                "Government tier access blocked for non-whitelisted IP: ip=%s user=%s",
                client_ip,
                user_id,
            )
            raise HTTPException(status_code=403, detail="IP not allowed for government tier access")

    try:
        validation = prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
        if not validation["valid"]:
            logger.warning(f"Security violation: {validation['reason']} - {validation.get('details', '')}")
            if validation["reason"] != "RATE_LIMITED":
                try:
                    from src.audit import log_anomaly

                    log_anomaly(
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
                    logger.warning("Audit log_anomaly failed at API layer", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

        consent_service = ConsentService()
        if not consent_service.has_consent(user_id, "research_access"):
            raise HTTPException(
                status_code=403,
                detail="Consent required: Please grant research_access consent before querying data",
            )

        cache_key = _api_cache._make_cache_key(request.query, user_tier)
        cached = _api_cache.get(cache_key)
        if cached is not None:
            cached_response = dict(cached) if isinstance(cached, dict) else cached
            if isinstance(cached_response, dict):
                cached_response["cached"] = True
            return _apply_tier_filter_to_response(
                cached_response, user_tier, user_id,
                token_payload.get("kid"),
                getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )

        fast_response = _fast_query_response(
            request.query,
            user_tier=user_tier,
            user_id=user_id,
            session_id=request.session_id,
        )
        if fast_response is not None:
            fast_response["audit_event_id"] = "fast_path_ui_audit"
            fast_response = _apply_tier_filter_to_response(
                fast_response, user_tier, user_id,
                token_payload.get("kid"),
                getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )
            _api_cache.set(cache_key, fast_response, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
            return fast_response

        context_key = _sql_context_key(user_id, request.session_id)
        follow_up_response = _academic_follow_up_response(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
            context_key=context_key,
        )
        if follow_up_response is not None:
            try:
                follow_up_response["audit_event_id"] = audit_log_query(
                    user_id,
                    request.query,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                )
            except Exception:
                logger.warning("Audit log_query failed for SQL follow-up fast path", exc_info=True)
                follow_up_response["audit_event_id"] = "audit_unavailable"
            follow_up_response = _apply_tier_filter_to_response(
                follow_up_response, user_tier, user_id,
                token_payload.get("kid"),
                getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )
            _api_cache.set(cache_key, follow_up_response, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
            return follow_up_response

        killer_response = _killer_query_response(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
        )
        if killer_response is not None:
            try:
                killer_response["audit_event_id"] = audit_log_query(
                    user_id,
                    request.query,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                )
            except Exception:
                logger.warning("Audit log_query failed for killer query fast path", exc_info=True)
                killer_response["audit_event_id"] = "audit_unavailable"
            killer_response = _apply_tier_filter_to_response(
                killer_response, user_tier, user_id,
                token_payload.get("kid"),
                getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )
            _api_cache.set(cache_key, killer_response, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
            _remember_sql_domain_context(
                _sql_context_key(user_id, request.session_id),
                request.query,
                killer_response.get("sql_query"),
            )
            return killer_response

        adversarial_response = _advanced_adversarial_response(
            request.query,
            user_tier=user_tier,
            session_id=request.session_id,
        )
        if adversarial_response is not None:
            try:
                adversarial_response["audit_event_id"] = audit_log_query(
                    user_id,
                    request.query,
                    jwt_kid=token_payload.get("kid"),
                    request_fingerprint=getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
                )
            except Exception:
                logger.warning("Audit log_query failed for adversarial SQL pattern", exc_info=True)
                adversarial_response["audit_event_id"] = "audit_unavailable"
            adversarial_response = _apply_tier_filter_to_response(
                adversarial_response, user_tier, user_id,
                token_payload.get("kid"),
                getattr(raw_request.state, "request_fingerprint", None) if raw_request else None,
            )
            _api_cache.set(cache_key, adversarial_response, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
            return adversarial_response

        slo_tracker = get_slo_tracker()
        slo_tracker.increment_concurrency()
        query_start = time.time()
        jwt_kid = token_payload.get("kid")
        request_fp = getattr(raw_request.state, "request_fingerprint", None) if raw_request else None

        audit_event_id = None
        try:
            audit_event_id = audit_log_query(user_id, request.query, jwt_kid=jwt_kid, request_fingerprint=request_fp)
        except Exception:
            logger.warning("Audit log_query failed at API layer", exc_info=True)

        result = None
        try:
            from src.config.database import get_database_manager

            db = get_database_manager()
            if db.is_overloaded():
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable due to database load. Please retry in a moment.",
                )
            result = get_workflow().run(
                request.query,
                user_tier=user_tier,
                session_id=request.session_id,
                user_id=user_id,
            )
        finally:
            latency_ms = (time.time() - query_start) * 1000
            slo_tracker.decrement_concurrency()
            slo_tracker.record_latency(latency_ms)
            citations = result.get("citations", []) if result is not None else []
            synthesis_method = result.get("synthesis_method", "unknown") if result is not None else "error"
            slo_tracker.record_citation(has_citation=len(citations) > 0, synthesis_method=synthesis_method)

        synthesis_method = result.get("synthesis_method", "unknown")
        warnings_text = " ".join(str(item).lower() for item in result.get("warnings", []))
        explicit_sql_only_degradation = synthesis_method == "sql_only" and (
            "vector" in warnings_text or "qdrant" in warnings_text
        )
        if (
            synthesis_method == "unknown"
            or (synthesis_method == "sql_only" and not explicit_sql_only_degradation)
        ) and result.get("synthesized_response"):
            synthesis_method = "rule_based"
        provenance = result.get("provenance", {}) or {}
        if "synth" not in provenance:
            provenance["synth"] = synthesis_method if synthesis_method != "unknown" else "rule_based"
        provenance.setdefault("cloud_synthesis_used", "cloud" in str(provenance.get("synth", "")))

        response_payload = {
            "query_id": result.get("query_id", str(uuid.uuid4())),
            "audit_event_id": audit_event_id,
            "session_id": result.get("session_id"),
            "response": result.get("synthesized_response", ""),
            "status": "success",
            "tier": user_tier,
            "intent": result.get("intent"),
            "routing_decision": result.get("routing_decision"),
            "verification_status": result.get("verification_status", False),
            "citation_validity": result.get("citation_validity", 1.0),
            "plan": result.get("plan"),
            "planner_metadata": result.get("planner_metadata", {}),
            "citations": result.get("citations", []),
            "warnings": result.get("warnings", result.get("errors", [])),
            "answer_confidence": _answer_confidence_from_verification(result.get("verification_status", False)),
            "answer_confidence_score": result.get(
                "answer_confidence_score",
                result.get("faithfulness_score", 0.95 if result.get("verification_status", False) else 0.45),
            ),
            "sql_anomaly_report": result.get("sql_anomaly_report", {}),
            "sql_query": result.get("sql_query"),
            "sql_queries": result.get("sql_queries", []),
            "sql_results": result.get("sql_results", []),
            "retrieval_sources": result.get("retrieval_sources", []),
            "provenance": provenance,
            "synthesis_method": synthesis_method,
            "conversation_history": result.get("conversation_history", []),
            "node_timings": result.get("node_timings", {}),
        }

        response_payload = _apply_tier_filter_to_response(
            response_payload, user_tier, user_id, jwt_kid, request_fp,
        )
        _api_cache.set(cache_key, response_payload, ttl=QUERY_RESULT_CACHE_TTL_SECONDS)
        _remember_sql_domain_context(
            _sql_context_key(user_id, request.session_id),
            request.query,
            response_payload.get("sql_query"),
        )
        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/query/stream")
async def query_stream(
    request: QueryRequest,
    token_payload: dict = Depends(get_current_user),
    raw_request: Request = None,
):
    client_ip = raw_request.client.host if raw_request and raw_request.client else None
    user_tier = token_payload.get("tier", 1)
    user_id = token_payload.get("sub", "anonymous")
    jwt_kid = token_payload.get("kid")
    request_fp = getattr(raw_request.state, "request_fingerprint", None) if raw_request else None

    allowed, remaining, reset_time, rate_headers = check_tier_rate_limit(user_id, user_tier, client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=rate_headers)

    validation = prompt_sanitiser.validate_query({"query": request.query}, identifier=user_id or client_ip)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Security violation: {validation['reason']}")

    consent_service = ConsentService()
    if not consent_service.has_consent(user_id, "research_access"):
        raise HTTPException(status_code=403, detail="Consent required for research_access")

    query_id = str(uuid.uuid4())

    async def event_generator():
        cite_pattern = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")

        def extract_citations(text: str):
            results = []
            for pub_id, chunk_id in cite_pattern.findall(text):
                results.append({"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id})
            return results

        try:
            from src.orchestration.nodes.synthesizer import synthesizer_node_streaming
            from src.data.database import NRGDatabase
            from src.skills.rag.skill import RAGSkill
            from src.skills.text_to_sql.skill import TextToSQLSkill

            start = time.time()
            sql_results = []
            chunks = []

            yield "event: phase\ndata: {\"phase\": \"intent_detection\", \"label\": \"Analysing query\", \"progress\": 0.1}\n\n"
            await asyncio.sleep(0.05)

            intent, routing = "structured", "text_to_sql"
            try:
                schema_extractor = TextToSQLSkill()
                schema_prompt = schema_extractor.get_schema_prompt(user_tier)
            except Exception:
                schema_prompt = ""

            query_lower = request.query.lower()
            needs_rag = any(
                kw in query_lower
                for kw in ["explain", "summarize", "what is", "describe", "latest", "recent", "trends", "advances"]
            )

            yield "event: phase\ndata: {\"phase\": \"retrieval\", \"label\": \"Fetching evidence\", \"progress\": 0.3}\n\n"

            if needs_rag:
                rag = RAGSkill()
                try:
                    retrieved = rag.retrieve(request.query, user_tier=user_tier, top_k=5)
                    chunks = retrieved.get("chunks", [])
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            if schema_prompt and not needs_rag:
                try:
                    db = NRGDatabase()
                    search_term = request.query.split()[0]
                    sql_results = db.execute_query(
                        "SELECT * FROM researchers WHERE research_area LIKE ? LIMIT 10",
                        (f"%{search_term}%",),
                        user_tier=user_tier,
                    )
                except Exception as e:
                    logger.warning(f"SQL execution failed: {e}")

            yield "event: phase\ndata: {\"phase\": \"synthesis\", \"label\": \"Generating response\", \"progress\": 0.6}\n\n"

            state = {
                "user_query": request.query,
                "sql_results": sql_results,
                "retrieved_chunks": chunks,
                "user_tier": user_tier,
                "conversation_history": [],
                "intent": intent,
                "routing_decision": routing,
            }

            streamed_citations = []

            for event in synthesizer_node_streaming(state):
                if event["event"] == "token":
                    token_text = event["data"]
                    safe_token = _apply_tier_response_filter(
                        {"response": token_text},
                        user_tier,
                        user_id=user_id,
                        jwt_kid=jwt_kid,
                        request_fingerprint=request_fp,
                        endpoint="/api/query/stream",
                    ).get("response", "")
                    yield f"data: {safe_token}\n\n"

                    for cite in extract_citations(token_text):
                        if cite["id"] not in [c["id"] for c in streamed_citations]:
                            streamed_citations.append(cite)
                            safe_cite = _apply_tier_response_filter(
                                cite,
                                user_tier,
                                user_id=user_id,
                                jwt_kid=jwt_kid,
                                request_fingerprint=request_fp,
                                endpoint="/api/query/stream",
                            )
                            yield f"event: citation\ndata: {json.dumps(safe_cite)}\n\n"

                elif event["event"] == "done":
                    elapsed_ms = (time.time() - start) * 1000
                    final_state = event.get("state", {})
                    citations = final_state.get("citations", streamed_citations)
                    verification = final_state.get("verification_status", False)
                    provenance = final_state.get("provenance", {})

                    meta = {
                        "elapsed_ms": elapsed_ms,
                        "synthesis_tier": "rule_based",
                        "verification_status": verification,
                        "citations": citations,
                        "provenance": provenance,
                        "query_id": query_id,
                    }
                    meta = _apply_tier_response_filter(
                        meta,
                        user_tier,
                        user_id=user_id,
                        jwt_kid=jwt_kid,
                        request_fingerprint=request_fp,
                        endpoint="/api/query/stream",
                    )
                    yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
                    yield "event: done\ndata: \n\n"

        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            safe_error = _apply_tier_response_filter(
                {"error": str(e)},
                user_tier,
                user_id=user_id,
                jwt_kid=jwt_kid,
                request_fingerprint=request_fp,
                endpoint="/api/query/stream",
            ).get("error", "Request failed")
            yield f"event: error\ndata: {safe_error}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/feedback")
async def submit_feedback(
    request: Request,
    feedback: FeedbackRequest,
):
    if feedback.score < 1 or feedback.score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")

    try:
        from src.training.data_collector import get_training_collector

        collector = get_training_collector()
        success = collector.update_feedback(
            query_id=feedback.query_id,
            score=feedback.score,
            feedback_text=feedback.feedback_text,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Training pair not found")
        return {"status": "ok", "query_id": feedback.query_id, "score": feedback.score}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback update failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")
