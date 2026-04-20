import re

import pytest

from src.orchestration.graph import NRGWorkflow
import src.orchestration.nodes.executor as executor_module
import src.orchestration.nodes.synthesizer as synthesizer_module
import src.orchestration.nodes.verifier as verifier_module


class _StubRAGSkill:
    def retrieve(self, query: str, user_tier: int = 1, top_k: int = 5):  # noqa: ARG002
        return {
            "chunks": [
                {
                    "publication_id": "PUB-RAG-001",
                    "chunk_id": "0",
                    "title": "AI Research Trends",
                    "content": "AI research trends show rapid growth in multimodal models and energy-aware training.",
                }
            ],
            "metadata": [
                {
                    "source_id": "PUB-RAG-001",
                    "access_tier": user_tier,
                }
            ],
        }

    def close(self):
        return None


def _reset_executor_cache() -> None:
    executor_module._sql_skill_instance = None
    executor_module._sql_skill_class_id = None
    executor_module._rag_skill_instance = None
    executor_module._rag_skill_class_id = None


def _assert_pipeline_contract(result: dict) -> None:
    assert isinstance(result.get("plan"), (dict, type(None)))
    assert isinstance(result.get("planner_metadata"), (dict, type(None)))
    assert isinstance(result.get("verification_status"), (bool, str))
    assert isinstance(result.get("synthesized_response"), str)


def _assert_has_citation(response: str) -> None:
    assert "[cite:" in response


@pytest.fixture(autouse=True)
def _force_rule_based_synthesis(monkeypatch):
    monkeypatch.setattr(synthesizer_module, "get_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)
    _reset_executor_cache()
    yield
    _reset_executor_cache()


def test_pipeline_sql_path_number_with_citation():
    workflow = NRGWorkflow()
    result = workflow.run("How many researchers are in Maharashtra?", user_tier=1)
    response = result["synthesized_response"]

    _assert_pipeline_contract(result)
    _assert_has_citation(response)
    assert any(char.isdigit() for char in response)


def test_pipeline_rag_path_prose_with_citation(monkeypatch):
    monkeypatch.setattr(executor_module, "_get_rag_skill", lambda: _StubRAGSkill())
    workflow = NRGWorkflow()
    result = workflow.run("What are the trends in AI research?", user_tier=2)
    response = result["synthesized_response"]

    _assert_pipeline_contract(result)
    _assert_has_citation(response)
    assert "ai" in response.lower()


def test_pipeline_hybrid_path_contains_structured_and_rag(monkeypatch):
    monkeypatch.setattr(executor_module, "_get_rag_skill", lambda: _StubRAGSkill())
    workflow = NRGWorkflow()
    result = workflow.run(
        "Compare IIT Bombay and IIT Delhi publication counts",
        user_tier=2,
    )
    response = result["synthesized_response"].lower()

    _assert_pipeline_contract(result)
    _assert_has_citation(response)
    assert "structured data" in response
    assert "excerpt" in response


def test_pipeline_tier3_email_request_has_no_pii_leakage():
    workflow = NRGWorkflow()
    result = workflow.run("Show emails of researchers in Gujarat", user_tier=3)
    response = result["synthesized_response"]

    _assert_pipeline_contract(result)
    _assert_has_citation(response)
    assert "email:" not in response.lower()
    assert re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", response) is None
