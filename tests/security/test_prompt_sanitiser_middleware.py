from types import SimpleNamespace

from starlette.datastructures import Headers

from src.api.middleware.security import PromptSanitiserMiddleware


def _request(headers: dict[str, str] | None = None, host: str = "127.0.0.1"):
    return SimpleNamespace(
        headers=Headers(headers or {}),
        client=SimpleNamespace(host=host),
    )


def test_prompt_sanitiser_uses_client_host_by_default(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    middleware = PromptSanitiserMiddleware(app=lambda scope, receive, send: None)

    identifier = middleware._identifier_for_request(
        _request({"x-forwarded-for": "203.0.113.10"})
    )

    assert identifier == "127.0.0.1"


def test_prompt_sanitiser_can_trust_forwarded_for_when_enabled(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    middleware = PromptSanitiserMiddleware(app=lambda scope, receive, send: None)

    identifier = middleware._identifier_for_request(
        _request({"x-forwarded-for": "203.0.113.10, 10.0.0.5"})
    )

    assert identifier == "203.0.113.10"
