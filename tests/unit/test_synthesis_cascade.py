"""
Test the 3-tier synthesis cascade:
1. Cloud works → use cloud response
2. Cloud fails, local works → use local response
3. Both fail → rule-based fallback
"""
import os
import pytest
from unittest.mock import patch

from src.orchestration.nodes.synthesizer import _synthesize, _fallback_synthesis


class _FakeCloudClient:
    model = "cloud-test"

    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list):
        return "Cloud LLM says: 42 researchers found."


class _FailingCloudClient:
    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list):
        raise RuntimeError("cloud timeout")


class _FakeLocalClient:
    model = "local-test"

    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list):
        return "Local SLM says: 42 researchers found."


class _FailingLocalClient:
    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list):
        raise RuntimeError("local timeout")


@pytest.fixture
def sample_sql_results():
    return [{"count": 42}]


@pytest.fixture
def sample_chunks():
    return []


def test_cloud_tier_succeeds(sample_sql_results, sample_chunks):
    """When cloud LLM works, its response is used."""
    with patch.dict(os.environ, {"CLOUD_SYNTHESIS_ALLOWED": "true"}):
        with patch("src.orchestration.nodes.synthesizer.get_llm_client", return_value=_FakeCloudClient()):
            response, provenance = _synthesize(
                query="How many researchers?",
                sources=["Structured data: 1 records"],
                sql_results=sample_sql_results,
                chunks=sample_chunks,
                user_tier=1,
                context_summary="",
            )
    assert "Cloud LLM says" in response
    assert provenance["synth"] == "cloud_llm"
    assert provenance["cloud_synthesis_used"] is True


def test_cloud_falls_back_to_local(sample_sql_results, sample_chunks):
    """When cloud fails but local works, local response is used."""
    with patch("src.orchestration.nodes.synthesizer.get_llm_client", return_value=_FailingCloudClient()):
        with patch("src.orchestration.nodes.synthesizer.get_local_llm_client", return_value=_FakeLocalClient()):
            response, provenance = _synthesize(
                query="How many researchers?",
                sources=["Structured data: 1 records"],
                sql_results=sample_sql_results,
                chunks=sample_chunks,
                user_tier=1,
                context_summary="",
            )
    assert "Local SLM says" in response
    assert provenance["synth"] == "local_llm"
    assert provenance["cloud_synthesis_used"] is False


def test_both_fail_uses_rule_based(sample_sql_results, sample_chunks):
    """When both cloud and local fail, rule-based fallback activates."""
    with patch("src.orchestration.nodes.synthesizer.get_llm_client", return_value=_FailingCloudClient()):
        with patch("src.orchestration.nodes.synthesizer.get_local_llm_client", return_value=_FailingLocalClient()):
            response, provenance = _synthesize(
                query="How many researchers?",
                sources=["Structured data: 1 records"],
                sql_results=sample_sql_results,
                chunks=sample_chunks,
                user_tier=1,
                context_summary="",
            )
    assert "NATIONAL RESEARCH GRAPH" in response or "Query:" in response
    assert provenance["synth"] == "rule_based"
    assert provenance["cloud_synthesis_used"] is False


def test_rule_based_formats_data_without_llm():
    """Rule-based fallback produces structured output without any LLM."""
    response = _fallback_synthesis(
        query="Find researchers in Gujarat",
        sql_results=[{"name": "Dr. Rao", "state": "Gujarat", "research_area": "AI"}],
        chunks=[],
        context_summary="",
        intent="structured",
        routing_decision="text_to_sql",
        user_tier=1,
    )
    assert "Dr. Rao" in response
    assert "Gujarat" in response
    assert "[Fallback Mode" in response


def test_rule_based_handles_aggregate_counts():
    """Rule-based fallback clearly states aggregate results."""
    response = _fallback_synthesis(
        query="How many researchers in Maharashtra?",
        sql_results=[{"count": 625}],
        chunks=[],
        context_summary="",
        intent="structured",
        routing_decision="text_to_sql",
        user_tier=1,
    )
    assert "625" in response
