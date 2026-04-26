"""Startup behavior tests for the API lifespan manager."""

import pytest

import src.api.main as api_main
import src.skills.rag.embedder as embedder_module


@pytest.mark.asyncio
async def test_lifespan_can_skip_embedder_warmup(monkeypatch):
    calls: list[str] = []

    class ExplodingEmbedder:
        def __init__(self):
            calls.append("init")
            raise AssertionError("embedder warmup should be skipped")

    monkeypatch.setenv("NRG_SKIP_EMBEDDER_WARMUP", "1")
    monkeypatch.setattr(embedder_module, "Embedder", ExplodingEmbedder)

    async def drain_noop():
        return None

    monkeypatch.setattr(api_main, "drain_connections", drain_noop)

    async with api_main.lifespan(api_main.app):
        pass

    assert calls == []
