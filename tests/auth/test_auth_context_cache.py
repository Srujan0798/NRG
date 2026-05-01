import time

from src.auth.middleware import (
    _verify_access_token_cached,
    reset_auth_context_token_cache,
)


class _FakeJWTHandler:
    def __init__(self):
        self.calls = 0

    def verify_access_token(self, token: str, *, client_ip: str | None = None) -> dict:
        self.calls += 1
        return {
            "sub": "researcher_user",
            "tier": 1,
            "token": token,
            "client_ip": client_ip,
            "exp": time.time() + 60,
        }


def test_auth_context_reuses_verified_token_within_short_ttl(monkeypatch):
    reset_auth_context_token_cache()
    monkeypatch.setenv("NRG_AUTH_CONTEXT_CACHE_TTL_SECONDS", "5")
    handler = _FakeJWTHandler()

    first = _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.1")
    second = _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.1")

    assert first == second
    assert handler.calls == 1


def test_auth_context_cache_is_bound_to_client_ip(monkeypatch):
    reset_auth_context_token_cache()
    monkeypatch.setenv("NRG_AUTH_CONTEXT_CACHE_TTL_SECONDS", "5")
    handler = _FakeJWTHandler()

    _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.1")
    _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.2")

    assert handler.calls == 2


def test_auth_context_cache_can_be_disabled(monkeypatch):
    reset_auth_context_token_cache()
    monkeypatch.setenv("NRG_AUTH_CONTEXT_CACHE_TTL_SECONDS", "0")
    handler = _FakeJWTHandler()

    _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.1")
    _verify_access_token_cached(handler, "token-a", client_ip="127.0.0.1")

    assert handler.calls == 2
