"""Regression coverage for support modules used by CI gates and runtime adapters."""

from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest
from starlette.responses import Response


def test_shared_sql_domain_extractors_handle_academic_hints():
    from src.api._shared_sql_domain import (
        extract_institute_hint,
        extract_year_hint,
        previous_financial_year,
    )

    assert extract_institute_hint("What courses did IIT Madras offer in 2024?") == "IIT Madras"
    assert extract_institute_hint("no institute here") is None
    assert extract_year_hint("compare 2023 and 2024") == "2023-24"
    assert extract_year_hint("for 2022-23") == "2022-23"
    assert extract_year_hint("no year") is None
    assert previous_financial_year("2023-24") == "2022-23"
    assert previous_financial_year("bad") is None


def test_security_headers_helpers_add_required_policy_headers():
    from src.security.headers import add_security_headers, get_security_headers_dict
    import src.security.security_harden as security_harden

    response = Response()
    add_security_headers(response)

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert get_security_headers_dict()["Strict-Transport-Security"].startswith("max-age=")
    assert "SecurityHeadersMiddleware" in security_harden.__all__


def test_sso_config_domain_role_and_login_flow(monkeypatch):
    from src.auth.sso_handler import SSOAuthHandler, SSOConfig, _normalize_role

    monkeypatch.setenv("SSO_ENABLED", "true")
    monkeypatch.setenv("SSO_PROVIDER_TYPE", "oidc")
    monkeypatch.setenv("SSO_CLIENT_ID", "client")
    monkeypatch.setenv("SSO_CLIENT_SECRET", "secret")
    monkeypatch.setenv("SSO_AUTHORIZATION_URL", "https://idp.example/auth")
    monkeypatch.setenv("SSO_TOKEN_URL", "https://idp.example/token")
    monkeypatch.setenv("SSO_ALLOWED_DOMAINS", "iitgn.ac.in,gov.in")

    config = SSOConfig()
    assert config.is_configured is True
    assert config.domain_allowed("user@iitgn.ac.in") is True
    assert config.domain_allowed("user@example.com") is False
    assert _normalize_role(config, {"groups": ["ministry-admin"]}) == "government"
    assert _normalize_role(config, {"role": "faculty"}) == "researcher"
    assert _normalize_role(config, {"role": "industry-partner"}) == "industry"

    handler = SSOAuthHandler()
    redirect_url, state = handler.initiate_login()

    assert redirect_url.startswith("https://idp.example/auth?")
    assert "client_id=client" in redirect_url
    assert state in handler._state_store
    handler._state_store["old"] = ("challenge", time.time() - handler.STATE_TTL - 1)
    handler._pkce_store["old"] = "verifier"
    handler._prune_expired_states()
    assert "old" not in handler._state_store
    assert "old" not in handler._pkce_store


def test_sso_callback_issues_jwt_pair_from_oidc_claims(monkeypatch):
    import src.auth.sso_handler as sso_handler
    from src.auth.sso_handler import SSOAuthHandler

    monkeypatch.setenv("SSO_ENABLED", "true")
    monkeypatch.setenv("SSO_PROVIDER_TYPE", "oidc")
    monkeypatch.setenv("SSO_CLIENT_ID", "client")
    monkeypatch.setenv("SSO_CLIENT_SECRET", "secret")
    monkeypatch.setenv("SSO_AUTHORIZATION_URL", "https://idp.example/auth")
    monkeypatch.setenv("SSO_TOKEN_URL", "https://idp.example/token")
    monkeypatch.setenv("SSO_ALLOWED_DOMAINS", "iitgn.ac.in")

    class FakeJWTHandler:
        def issue_token_pair(self, user_info):
            assert user_info["user_id"] == "sso-sub-1"
            assert user_info["tier"] == 1
            assert user_info["email"] == "user@iitgn.ac.in"
            return {"access_token": "access", "refresh_token": "refresh"}

    monkeypatch.setattr(
        sso_handler,
        "_exchange_code_for_tokens",
        lambda config, code, verifier=None: {"id_token": "signed-id-token"},
    )
    monkeypatch.setattr(
        sso_handler.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "sub-1",
            "email": "user@iitgn.ac.in",
            "role": "researcher",
            "iss": "issuer",
            "name": "Research User",
        },
    )

    import src.auth.jwt_handler as jwt_handler_module

    monkeypatch.setattr(jwt_handler_module, "JWTHandler", FakeJWTHandler)
    handler = SSOAuthHandler()
    _, state = handler.initiate_login()

    token_pair = handler.handle_callback(code="code", state=state, expected_state=state)

    assert token_pair.access_token == "access"
    assert token_pair.refresh_token == "refresh"


def test_sso_callback_rejects_bad_state(monkeypatch):
    from src.auth.jwt_handler import AuthError
    from src.auth.sso_handler import SSOAuthHandler

    monkeypatch.delenv("SSO_ENABLED", raising=False)
    handler = SSOAuthHandler()
    with pytest.raises(AuthError, match="not configured"):
        handler.initiate_login()


def test_local_llm_prompt_generation_and_rule_based_fallback(monkeypatch):
    import src.config.local_llm as local_llm

    monkeypatch.setattr(local_llm, "get_local_llm", lambda: (None, None))
    client = local_llm.LocalLLMClient()
    prompt = client._build_prompt(
        "system",
        "current question",
        [{"query": "old question", "response": "old answer"}],
    )

    assert "System: system" in prompt
    assert "User: old question" in prompt
    assert prompt.endswith("Assistant:")

    synthesis = local_llm.rule_based_synthesis(
        "find AI researchers",
        [{"name": "Dr A", "research_area": "AI", "state": "Gujarat", "institution_id": "IIT"}],
        [],
        user_tier=2,
    )
    assert "Found **1** research records" in synthesis
    assert "Government Tier Access" in synthesis

    chunk_synthesis = local_llm.rule_based_synthesis("docs", [], ["alpha" * 50], user_tier=3)
    assert "Document Analysis" in chunk_synthesis
    assert "Industry Tier Access" in chunk_synthesis


def test_llama_cpp_client_handles_success_streaming_and_health(monkeypatch):
    import src.config.local_llm as local_llm

    class FakeResponse:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "local answer"}}]}

        def iter_lines(self):
            yield b'data: {"choices":[{"delta":{"content":"part-1"}}]}'
            yield b'data: {"choices":[{"delta":{"content":"part-2"}}]}'
            yield b"data: [DONE]"

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr(local_llm.httpx, "post", fake_post)
    monkeypatch.setattr(local_llm.httpx, "get", lambda url, timeout: SimpleNamespace(status_code=200))

    client = local_llm.LlamaCppClient(url="http://local", model="gguf")
    assert client.generate("sys", "question", [{"query": "q", "response": "a"}]) == "local answer"
    assert list(client.generate_streaming("sys", "question")) == ["part-1", "part-2"]
    assert client.health_check() is True
    assert calls[0][1]["json"]["model"] == "gguf"


def test_llama_cpp_client_error_paths_and_cache(monkeypatch):
    import src.config.local_llm as local_llm

    local_llm._llama_cpp_health_cache = None
    real_llama_client = local_llm.LlamaCppClient
    monkeypatch.setenv("LOCAL_LLM_DISABLED", "true")
    assert local_llm.get_llama_cpp_client() is None
    assert local_llm.get_llama_cpp_health_cache()[1] is False

    monkeypatch.setenv("LOCAL_LLM_DISABLED", "false")
    local_llm._llama_cpp_health_cache = None

    class HealthyClient:
        def health_check(self):
            return True

    monkeypatch.setattr(local_llm, "LlamaCppClient", HealthyClient)
    assert isinstance(local_llm.get_llama_cpp_client(), HealthyClient)
    monkeypatch.setattr(local_llm, "LlamaCppClient", real_llama_client)

    class NoContentResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": []}

    monkeypatch.setattr(local_llm.httpx, "post", lambda *args, **kwargs: NoContentResponse())
    client = local_llm.LlamaCppClient(url="http://local")
    with pytest.raises(RuntimeError, match="did not include content"):
        client.generate("sys", "question")


class _FakeSpan:
    def __init__(self):
        self.updates = []
        self.ended = False

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def end(self):
        self.ended = True


class _FakeTrace:
    def __init__(self):
        self.spans = []
        self.updates = []

    def span(self, name, **kwargs):
        span = _FakeSpan()
        self.spans.append((name, kwargs, span))
        return span

    def update(self, **kwargs):
        self.updates.append(kwargs)


class _FakeLangfuseClient:
    def __init__(self):
        self.traces = []
        self.generations = []

    def trace(self, **kwargs):
        trace = _FakeTrace()
        self.traces.append((kwargs, trace))
        return trace

    def generation(self, **kwargs):
        generation = _FakeGeneration(kwargs)
        self.generations.append(generation)
        return generation


class _FakeGeneration:
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.ended = []

    def end(self, **kwargs):
        self.ended.append(kwargs)


def test_langfuse_disabled_and_decorator_fallback(monkeypatch):
    import src.observability.langfuse_tracer as tracer

    tracer._client = None
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    assert tracer.is_langfuse_enabled() is False
    assert tracer.create_generation("trace", "model", "provider", "prompt") is None

    @tracer.trace_pipeline_node("node")
    def add_one(value):
        return value + 1

    assert add_one(1) == 2


def test_langfuse_traced_decorators_and_pipeline_context(monkeypatch):
    import src.observability.langfuse_tracer as tracer

    fake_client = _FakeLangfuseClient()
    monkeypatch.setattr(tracer, "_init_langfuse", lambda: fake_client)
    monkeypatch.setattr(tracer, "_should_sample", lambda: True)

    @tracer.trace_llm_call("planner", capture_output=True)
    def llm_call():
        return {"answer": "ok"}

    @tracer.trace_routing_decision
    def route():
        return {"intent": "researcher", "routing_decision": "text_to_sql", "routing_confidence": 0.9}

    @tracer.trace_sql_generation
    def sql_generate():
        return {"query": "SELECT 1"}

    @tracer.trace_rag_retrieval
    def rag_retrieve():
        return {"chunks": ["a", "b"]}

    assert llm_call() == {"answer": "ok"}
    assert route()["intent"] == "researcher"
    assert sql_generate()["query"] == "SELECT 1"
    assert rag_retrieve()["chunks"] == ["a", "b"]

    generation = tracer.create_generation("trace-1", "model", "provider", "prompt")
    tracer.end_generation(generation, output="answer", token_usage={"total": 3})
    tracer.end_generation(generation, error="failed")
    assert generation.ended

    with tracer.PipelineTracer("qid", "user", 2, "query text") as pipeline:
        span = pipeline.start_span("planner")
        assert span is not None
        pipeline.end_span("planner", {"rows": 3})
        pipeline.record_tokens("provider", "model", 11, role="input")
        pipeline.record_error("planner", "bad")

    assert fake_client.traces


def test_training_data_formatter_all_formats_and_jsonl_roundtrip(tmp_path):
    from src.training.data_formatter import DataFormatter, pairs_to_jsonl, read_jsonl

    pair = {
        "query": "Find AI researchers",
        "response": "Answer",
        "route": "text_to_sql",
        "sql_generated": "SELECT * FROM researchers WHERE research_area = 'AI'",
        "sql_result": json.dumps([{"name": "Dr A"}] * 12),
        "sql_row_count": 12,
        "citations": json.dumps(["c1", "c2"]),
        "quality_grade": "A",
        "tier": 1,
        "verifier_score": 0.95,
    }
    formatter = DataFormatter(include_metadata=True)

    alpaca = formatter.to_alpaca(pair)
    assert "expert SQL query writer" in alpaca["instruction"]
    assert alpaca["metadata"]["route"] == "text_to_sql"

    rag_pair = {**pair, "route": "rag", "citations": "not-json"}
    assert "research assistant" in formatter.to_alpaca(rag_pair)["instruction"]
    assert formatter.to_sharegpt({**pair, "route": "rag"})["conversations"][0]["from"] == "human"

    sql_format = formatter.to_sql_format(pair)
    assert sql_format["difficulty"] == "medium"
    assert "... and 2 more rows" in sql_format["sql_result"]
    assert formatter.to_sql_format({**pair, "route": "rag"}) == {}
    assert formatter.format_pair(pair, "unknown") is None
    assert len(formatter.format_batch([pair, {**pair, "route": "rag"}], "sql")) == 1

    output_path = tmp_path / "training" / "pairs.jsonl"
    assert pairs_to_jsonl([pair], output_path) == 1
    assert read_jsonl(output_path)[0]["query"] == "Find AI researchers"
