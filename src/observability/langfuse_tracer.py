"""Langfuse Tracing for NRG pipeline - traces every node with latency, tokens, errors."""

import os
import logging
import time
import random
from functools import wraps
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

_client: Any = None
_sampling_rate: float = float(os.getenv("LANGFUSE_SAMPLING_RATE", "1.0"))


@dataclass
class TraceConfig:
    capture_tokens: bool = True
    capture_latency: bool = True
    capture_errors: bool = True
    capture_routing: bool = True
    capture_metadata: bool = True


def _init_langfuse() -> Any:
    global _client
    if _client is not None:
        return _client if _client is not False else None
    
    try:
        from langfuse import Langfuse
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        if public_key and secret_key:
            _client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            logger.info("Langfuse initialized: %s (sampling_rate=%.2f)", host, _sampling_rate)
        else:
            _client = False
            logger.info("Langfuse not configured - tracing disabled")
    except Exception as exc:
        logger.warning("Langfuse import failed - LLM tracing disabled: %s", exc)
        _client = False
    return _client if _client is not False else None


def _should_sample() -> bool:
    return random.random() < _sampling_rate


def trace_llm_call(node_name: str, capture_output: bool = False) -> Callable:
    """Decorator to trace LLM calls in pipeline nodes."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = _init_langfuse()
            if not client or not _should_sample():
                return func(*args, **kwargs)

            trace = client.trace(name=f"nrg.{node_name}")
            span = trace.span(
                name=f"{node_name}.generate",
                input={"args": str(args)[:200], "kwargs": list(kwargs.keys())}
            )
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                
                metadata = {"latency_ms": latency_ms}
                if capture_output:
                    metadata["output_preview"] = str(result)[:200]
                
                span.update(
                    status="success",
                    metadata=metadata,
                    output=str(result)[:500] if capture_output else None
                )
                trace.update(status="success", metadata={"node": node_name})
                
                return result
            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                span.update(
                    status="error",
                    output=str(exc),
                    metadata={"latency_ms": latency_ms, "error_type": type(exc).__name__}
                )
                trace.update(status="error", metadata={"node": node_name, "error": str(exc)})
                raise
            finally:
                span.end()
        
        return wrapper
    return decorator


def trace_pipeline_node(
    node_name: str,
    capture_tokens: bool = True,
    capture_latency: bool = True,
    capture_routing: bool = False
) -> Callable:
    """Decorator to trace pipeline node execution with comprehensive metadata."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = _init_langfuse()
            should_trace = client and _should_sample()
            
            trace = None
            span = None
            start = time.time()
            
            if should_trace:
                trace = client.trace(name=f"nrg.pipeline.{node_name}")
                span = trace.span(name=node_name)
            
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                
                if should_trace and span:
                    metadata = {"latency_ms": latency_ms}
                    if capture_routing and isinstance(result, dict):
                        metadata["routing_decision"] = result.get("routing_decision", "unknown")
                        metadata["intent"] = result.get("intent", "unknown")
                        metadata["confidence"] = result.get("routing_confidence", 0.0)
                    
                    span.update(status="success", metadata=metadata)
                    if trace:
                        trace.update(
                            status="success",
                            metadata={
                                "node": node_name,
                                "latency_ms": latency_ms,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                
                return result
                
            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                if should_trace and span:
                    span.update(
                        status="error",
                        output=str(exc),
                        metadata={"latency_ms": latency_ms, "error": type(exc).__name__}
                    )
                    if trace:
                        trace.update(
                            status="error",
                            metadata={"node": node_name, "error": str(exc)}
                        )
                raise
            finally:
                if span:
                    span.end()
        
        return wrapper
    return decorator


def trace_routing_decision(func: Callable) -> Callable:
    """Decorator specifically for router node to capture routing decisions."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        client = _init_langfuse()
        
        if not client or not _should_sample():
            return func(*args, **kwargs)
        
        trace = client.trace(name="nrg.router")
        span = trace.span(name="route_decision")
        start = time.time()
        
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start) * 1000
            
            metadata = {
                "latency_ms": latency_ms,
                "intent": result.get("intent", "unknown") if isinstance(result, dict) else "unknown",
                "routing_decision": result.get("routing_decision", "unknown") if isinstance(result, dict) else "unknown",
                "confidence": result.get("routing_confidence", 0.0) if isinstance(result, dict) else 0.0,
            }
            
            span.update(metadata=metadata)
            trace.update(metadata=metadata)
            
            return result
        except Exception as exc:
            span.update(status="error", output=str(exc))
            trace.update(status="error", metadata={"error": str(exc)})
            raise
        finally:
            span.end()
    
    return wrapper


def create_generation(
    trace_id: str,
    model: str,
    provider: str,
    prompt: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Any:
    """Create a Langfuse generation span for LLM calls."""
    client = _init_langfuse()
    if not client:
        return None
    
    try:
        generation = client.generation(
            trace_id=trace_id,
            name=f"{provider}_{model}",
            model=model,
            prompt=prompt[:1000] if prompt else "",
            metadata=metadata or {}
        )
        return generation
    except Exception as exc:
        logger.warning("Failed to create Langfuse generation: %s", exc)
        return None


def end_generation(generation: Any, output: str = None, error: str = None, token_usage: Dict[str, int] = None):
    """End a Langfuse generation span with output and token usage."""
    if not generation:
        return
    
    try:
        if error:
            generation.end(level="ERROR", status_message=error)
        else:
            end_metadata = {}
            if token_usage:
                end_metadata["usage"] = token_usage
            if output:
                end_metadata["output_preview"] = output[:200]
            generation.end(metadata=end_metadata if end_metadata else None)
    except Exception as exc:
        logger.warning("Failed to end Langfuse generation: %s", exc)


class PipelineTracer:
    """Context manager for tracing a complete pipeline execution."""
    
    def __init__(
        self,
        query_id: str,
        user_id: str,
        user_tier: int,
        query_text: str,
        capture_tokens: bool = True
    ):
        self.query_id = query_id
        self.user_id = user_id
        self.user_tier = user_tier
        self.query_text = query_text[:200]
        self.capture_tokens = capture_tokens
        self.client = None
        self.trace = None
        self.spans: Dict[str, Any] = {}
        
    def __enter__(self):
        self.client = _init_langfuse()
        if self.client and _should_sample():
            self.trace = self.client.trace(
                name="nrg.pipeline",
                id=self.query_id,
                user_id=self.user_id,
                metadata={
                    "user_tier": self.user_tier,
                    "query_preview": self.query_text
                }
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.trace:
            if exc_type:
                self.trace.update(status="error", metadata={"error": str(exc_val)})
            else:
                self.trace.update(status="success")
    
    def start_span(self, name: str) -> Optional[Any]:
        """Start a named span within the pipeline."""
        if not self.trace:
            return None
        span = self.trace.span(name=name)
        self.spans[name] = {"span": span, "start": time.time()}
        return span
    
    def end_span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """End a named span with optional metadata."""
        if name not in self.spans:
            return
        
        span_info = self.spans[name]
        span = span_info["span"]
        latency_ms = (time.time() - span_info["start"]) * 1000
        
        update_meta = {"latency_ms": latency_ms}
        if metadata:
            update_meta.update(metadata)
        
        span.update(status="success", metadata=update_meta)
        span.end()
        del self.spans[name]
    
    def record_tokens(self, provider: str, model: str, tokens: int, role: str = "unknown"):
        """Record token usage to current span."""
        if not self.client or not self.trace:
            return
        
        try:
            self.trace.update(
                metadata={
                    f"tokens_{role}": tokens,
                    f"provider_{role}": provider,
                    f"model_{role}": model
                }
            )
        except Exception:
            pass
    
    def record_error(self, node: str, error: str):
        """Record an error in the trace."""
        if not self.trace:
            return
        self.trace.update(
            metadata={"error_node": node, "error": error, "error_type": "pipeline_error"}
        )


def init_pipeline_tracing(
    query_id: str,
    user_id: str,
    user_tier: int,
    query_text: str
) -> PipelineTracer:
    """Initialize pipeline tracing context."""
    return PipelineTracer(
        query_id=query_id,
        user_id=user_id,
        user_tier=user_tier,
        query_text=query_text
    )