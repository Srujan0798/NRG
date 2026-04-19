"""OpenTelemetry + Langfuse distributed tracing for NRG."""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from langfuse import Langfuse


# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
)

# Initialize OpenTelemetry
tracer_provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
)
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer("nrg")


def instrument_fastapi(app):
    """Instrument FastAPI with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)


@contextmanager
def trace_llm_call(provider: str, model: str, prompt: str):
    """Trace an LLM call with both Langfuse and OpenTelemetry."""
    trace_id = os.urandom(16).hex()
    
    # Langfuse trace
    langfuse_trace = langfuse.trace(
        name="llm_call",
        metadata={"provider": provider, "model": model},
    )
    
    # Langfuse generation
    generation = langfuse.generation(
        trace_id=langfuse_trace.id,
        name=f"{provider}_{model}",
        model=model,
        prompt=prompt[:1000],
    )
    
    # OpenTelemetry span
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.provider", provider)
        span.set_attribute("llm.model", model)
        span.set_attribute("trace.id", trace_id)
        
        try:
            yield trace_id
            generation.end()
        except Exception as e:
            generation.end(level="ERROR", status_message=str(e))
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise


@contextmanager
def trace_skill_execution(skill_name: str, user_tier: int):
    """Trace skill execution."""
    with tracer.start_as_current_span(f"skill_{skill_name}") as span:
        span.set_attribute("skill.name", skill_name)
        span.set_attribute("user.tier", user_tier)
        
        langfuse_span = langfuse.span(
            name=f"skill_{skill_name}",
            metadata={"tier": user_tier},
        )
        
        try:
            yield
            langfuse_span.end()
        except Exception as e:
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
    with tracer.start_as_current_span("query") as span:
        span.set_attribute("query.id", query_id)
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.tier", user_tier)
        span.set_attribute("query.text", query_text[:200])
        
        trace = langfuse.trace(
            name="query",
            id=query_id,
            user_id=user_id,
            metadata={"tier": user_tier},
        )
        
        return trace.id


def get_trace_context() -> Dict[str, Any]:
    """Get current trace context for propagation."""
    current_span = trace.get_current_span()
    if current_span:
        return {
            "trace_id": current_span.get_span_context().trace_id,
            "span_id": current_span.get_span_context().span_id,
        }
    return {}
