from __future__ import annotations

from typing import Any

from src.api import main as api_main
from src.api import query_helpers


def _shape(payload: dict[str, Any] | None) -> dict[str, Any]:
    assert payload is not None
    return {
        "intent": payload.get("intent"),
        "routing_decision": payload.get("routing_decision"),
        "route": payload.get("route"),
        "has_citations": bool(payload.get("citations")),
        "has_provenance": bool(payload.get("provenance")),
        "sql_result_count": len(payload.get("sql_results") or []),
    }


def test_query_helpers_match_live_fast_path_shapes_for_known_drift_cases() -> None:
    cases = [
        "Count projects by their innovation stage (TRL level), grouped per institute.",
        "top funding agencies by grant amount",
        "explain policy pattern behind top government grant funding agencies",
        "show labs by research area",
        "researchers by state statistics",
    ]

    for index, query in enumerate(cases):
        session_id = f"helper-drift-{index}"
        live_shape = _shape(
            api_main._fast_query_response(
                query,
                user_tier=1,
                user_id="helper-drift-user",
                session_id=session_id,
            )
        )
        helper_shape = _shape(
            query_helpers._fast_query_response(
                query,
                user_tier=1,
                user_id="helper-drift-user",
                session_id=session_id,
            )
        )

        assert helper_shape == live_shape
