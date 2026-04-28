from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.orchestration.contracts import (
    CONTRACT_EDGE_NAMES,
    detect_major_version_bumps,
    generate_contract_markdown,
    list_contracts,
    validate_edge_payload,
)
from src.orchestration.nodes.receiver import receiver_node


def _merge_state(state: dict, update: dict) -> dict:
    merged = dict(state)
    merged.update(update)
    return merged


def _receiver_payload() -> dict:
    return receiver_node(
        {
            "user_query": "How many researchers are in Gujarat?",
            "user_tier": 2,
            "session_id": "contract-session",
            "conversation_history": [],
        }
    )


def _planner_payload(monkeypatch) -> dict:
    import src.orchestration.nodes.planner as planner_module

    monkeypatch.setattr(planner_module, "_get_planner_client", lambda: None)
    monkeypatch.setattr(planner_module, "log_plan", lambda *args, **kwargs: None)
    state = _receiver_payload()
    return _merge_state(state, planner_module.planner_node(state))


def _router_payload(monkeypatch) -> dict:
    from src.orchestration.nodes.router import router_node

    state = _planner_payload(monkeypatch)
    return _merge_state(state, router_node(state))


def _executor_payload(monkeypatch) -> dict:
    import src.orchestration.nodes.executor as executor_module

    monkeypatch.setattr(
        executor_module,
        "_execute_sql",
        lambda query, tier: (
            {
                "sql_query": "SELECT COUNT(*) AS researcher_count FROM researchers",
                "sql_results": [{"researcher_count": 42}],
                "errors": [],
                "warnings": [],
            },
            3.0,
        ),
    )
    monkeypatch.setattr(
        executor_module,
        "_execute_rag",
        lambda query, tier: (
            {
                "retrieved_chunks": [],
                "retrieval_metadata": [],
                "retrieval_sources": [],
                "errors": [],
                "warnings": [],
            },
            2.0,
        ),
    )
    state = _router_payload(monkeypatch)
    state["routing_decision"] = "text_to_sql"
    return _merge_state(state, executor_module.executor_node(state))


def _synthesizer_payload(monkeypatch) -> dict:
    import src.orchestration.nodes.synthesizer as synthesizer_module

    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)
    state = _executor_payload(monkeypatch)
    state["routing_decision"] = "text_to_sql"
    return _merge_state(state, synthesizer_module.synthesizer_node(state))


@pytest.mark.contract
def test_all_pipeline_contracts_are_defined_with_semver():
    contracts = list_contracts()

    assert [contract.edge for contract in contracts] == list(CONTRACT_EDGE_NAMES)
    assert len(contracts) == 5
    for contract in contracts:
        assert contract.version == "1.0.0"
        assert contract.path.exists()
        assert contract.schema["$schema"].startswith("https://json-schema.org/")


@pytest.mark.contract
@pytest.mark.parametrize(
    ("edge", "payload_factory"),
    [
        ("receiver_to_planner", lambda monkeypatch: _receiver_payload()),
        ("planner_to_router", _planner_payload),
        ("router_to_executor", _router_payload),
        ("executor_to_synthesizer", _executor_payload),
        ("synthesizer_to_verifier", _synthesizer_payload),
    ],
)
def test_producers_emit_payloads_matching_edge_contracts(monkeypatch, edge, payload_factory):
    payload = payload_factory(monkeypatch)

    errors = validate_edge_payload(edge, payload)

    assert errors == []


@pytest.mark.contract
def test_planner_consumes_receiver_contract(monkeypatch):
    import src.orchestration.nodes.planner as planner_module

    payload = _receiver_payload()
    assert validate_edge_payload("receiver_to_planner", payload) == []

    monkeypatch.setattr(planner_module, "_get_planner_client", lambda: None)
    monkeypatch.setattr(planner_module, "log_plan", lambda *args, **kwargs: None)
    result = planner_module.planner_node(payload)

    assert validate_edge_payload("planner_to_router", _merge_state(payload, result)) == []


@pytest.mark.contract
def test_router_consumes_planner_contract(monkeypatch):
    from src.orchestration.nodes.router import router_node

    payload = _planner_payload(monkeypatch)
    assert validate_edge_payload("planner_to_router", payload) == []

    result = router_node(payload)

    assert validate_edge_payload("router_to_executor", _merge_state(payload, result)) == []


@pytest.mark.contract
def test_executor_consumes_router_contract(monkeypatch):
    import src.orchestration.nodes.executor as executor_module

    payload = _router_payload(monkeypatch)
    assert validate_edge_payload("router_to_executor", payload) == []

    monkeypatch.setattr(
        executor_module,
        "_execute_sql",
        lambda query, tier: ({"sql_query": "SELECT 1", "sql_results": [{"n": 1}], "errors": [], "warnings": []}, 1.0),
    )
    result = executor_module.executor_node(payload)

    assert validate_edge_payload("executor_to_synthesizer", _merge_state(payload, result)) == []


@pytest.mark.contract
def test_synthesizer_consumes_executor_contract(monkeypatch):
    import src.orchestration.nodes.synthesizer as synthesizer_module

    payload = _executor_payload(monkeypatch)
    assert validate_edge_payload("executor_to_synthesizer", payload) == []

    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)
    result = synthesizer_module.synthesizer_node(payload)

    assert validate_edge_payload("synthesizer_to_verifier", _merge_state(payload, result)) == []


@pytest.mark.contract
def test_verifier_consumes_synthesizer_contract(monkeypatch):
    import src.orchestration.nodes.verifier as verifier_module

    payload = _synthesizer_payload(monkeypatch)
    assert validate_edge_payload("synthesizer_to_verifier", payload) == []

    monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)
    fake_db = MagicMock()
    fake_db.close = MagicMock()
    monkeypatch.setattr(verifier_module, "_get_db_connection", lambda: fake_db)
    result = verifier_module.verifier_node(payload)

    assert "verification_status" in result
    assert "faithfulness_score" in result


@pytest.mark.contract
def test_contract_docs_are_generated_from_schema_titles():
    markdown = generate_contract_markdown()

    assert "# 6-Node Pipeline Contracts" in markdown
    assert "receiver_to_planner" in markdown
    assert "synthesizer_to_verifier" in markdown


@pytest.mark.contract
def test_semver_major_bump_detection():
    previous = {"receiver_to_planner": "1.2.3", "planner_to_router": "1.0.0"}
    current = {"receiver_to_planner": "2.0.0", "planner_to_router": "1.1.0"}

    bumps = detect_major_version_bumps(previous, current)

    assert bumps == {"receiver_to_planner": {"previous": "1.2.3", "current": "2.0.0"}}


@pytest.mark.contract
def test_validate_contracts_script_writes_docs_and_report(tmp_path):
    from scripts import validate_contracts

    docs_output = tmp_path / "contracts.md"
    report_output = tmp_path / "contracts.json"

    exit_code = validate_contracts.main(
        [
            "--docs-output",
            str(docs_output),
            "--report-output",
            str(report_output),
        ]
    )

    payload = json.loads(report_output.read_text())
    assert exit_code == 0
    assert payload["ok"] is True
    assert len(payload["contracts"]) == 5
    assert docs_output.read_text().startswith("# 6-Node Pipeline Contracts")
