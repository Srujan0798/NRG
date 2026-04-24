"""OpenTelemetry + Langfuse distributed tracing for NRG."""

import os
import logging
from contextlib import contextmanager
from typing import Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

_langfuse_client: Any = None


def _get_langfuse():
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client if _langfuse_client is not False else None

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if public_key and secret_key and host:
        try:
            from langfuse import Langfuse
            _langfuse_client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            logger.info("Langfuse initialized in tracing.py: %s", host)
        except Exception as exc:
            logger.warning("Langfuse init failed in tracing.py: %s", exc)
            _langfuse_client = False
    else:
        _langfuse_client = False
    return _langfuse_client if _langfuse_client is not False else None


# Initialize OpenTelemetry lazily
_tracer_provider = None
_tracer = None


def _get_tracer():
    global _tracer_provider, _tracer
    if _tracer is None:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
            )
            _tracer_provider = TracerProvider()
            _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(_tracer_provider)
            _tracer = trace.get_tracer("nrg")
        except Exception as exc:
            logger.warning("OpenTelemetry setup failed: %s", exc)
            _tracer = trace.get_tracer("nrg")
    return _tracer


def instrument_fastapi(app):
    """Instrument FastAPI with OpenTelemetry."""
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        logger.warning("FastAPI instrumentation failed: %s", e)


@contextmanager
def trace_llm_call(provider: str, model: str, prompt: str):
    """Trace an LLM call with both Langfuse and OpenTelemetry."""
    langfuse = _get_langfuse()
    tracer = _get_tracer()
    trace_id = os.urandom(16).hex()

    if langfuse:
        langfuse_trace = langfuse.trace(
            name="llm_call",
            metadata={"provider": provider, "model": model},
        )
        generation = langfuse.generation(
            trace_id=langfuse_trace.id,
            name=f"{provider}_{model}",
            model=model,
            prompt=prompt[:1000],
        )
    else:
        langfuse_trace = None
        generation = None

    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.provider", provider)
        span.set_attribute("llm.model", model)
        span.set_attribute("trace.id", trace_id)

        try:
            yield trace_id
            if generation:
                generation.end()
        except Exception as e:
            if generation:
                generation.end(level="ERROR", status_message=str(e))
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise


@contextmanager
def trace_skill_execution(skill_name: str, user_tier: int):
    """Trace skill execution."""
    langfuse = _get_langfuse()
    tracer = _get_tracer()

    with tracer.start_as_current_span(f"skill_{skill_name}") as span:
        span.set_attribute("skill.name", skill_name)
        span.set_attribute("user.tier", user_tier)

        langfuse_span = None
        if langfuse:
            try:
                langfuse_span = langfuse.span(
                    name=f"skill_{skill_name}",
                    metadata={"tier": user_tier},
                )
            except Exception:
                pass

        try:
            yield
            if langfuse_span:
                langfuse_span.end()
        except Exception as e:
            if langfuse_span:
                langfuse_span.end(level="ERROR")
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise


def trace_query(
    query_id: str,
    user_id: str,
    user_tier: int,
    query_text: str,
) -> str:
    """Start tracing a user query."""
    langfuse = _get_langfuse()
    tracer = _get_tracer()

    with tracer.start_as_current_span("query") as span:
        span.set_attribute("query.id", query_id)
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.tier", user_tier)
        span.set_attribute("query.text", query_text[:200])

        if langfuse:
            trace = langfuse.trace(
                name="query",
                id=query_id,
                user_id=user_id,
                metadata={"tier": user_tier},
            )
            return str(trace.id)
        return query_id


def get_trace_context() -> Dict[str, Any]:
    """Get current trace context for propagation."""
    current_span = trace.get_current_span()
    if current_span:
        return {
            "trace_id": current_span.get_span_context().trace_id,
            "span_id": current_span.get_span_context().span_id,
        }
    return {}
