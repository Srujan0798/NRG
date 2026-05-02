from __future__ import annotations

from typing import Any

import pytest

from src.api.routes import data as data_routes


class FakeCache:
    def get(self, _key: str) -> None:
        return None

    def set(self, _key: str, _value: Any, *, ttl: int) -> None:
        return None


class FakeDB:
    def get_stats(self) -> dict[str, Any]:
        return {
            "researchers": None,
            "publications": None,
            "institutions": None,
            "labs": None,
            "funding_records": None,
            "research_areas": [],
            "state_distribution": [],
        }


@pytest.mark.asyncio
async def test_stats_preserves_null_aggregates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data_routes, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(data_routes, "_api_cache", FakeCache())
    monkeypatch.setattr(data_routes, "_tier_response_filter", lambda payload, _tier, **_kwargs: payload)

    payload = await data_routes.get_stats(
        token_payload={"role": "government", "tier": 2, "sub": "user-1", "kid": "kid-1"}
    )

    assert payload["total_researchers"] is None
    assert payload["total_publications"] is None
    assert payload["total_institutions"] is None
    assert payload["total_labs"] is None
    assert payload["total_funding_amount"] is None
